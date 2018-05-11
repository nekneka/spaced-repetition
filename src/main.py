import os
from datetime import date, timedelta, datetime
import json

from flask import Flask, render_template, request, url_for, redirect
from sqlalchemy.sql.elements import not_
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.types import BigInteger
from src import config


app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', None)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'postgresql://{}:{}@{}:{}/{}'.format(
        config.DB_USER, config.DB_PASS, config.DB_HOST, config.DB_PORT, config.DB_NAME))
app.config.from_pyfile('config.py', silent=True)

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy(app)


class LogItem(db.Model):
    id = db.Column(BigInteger, primary_key=True)
    timestamp = db.Column(db.DateTime, unique=False, nullable=False)
    ip = db.Column(db.String, unique=False, nullable=False)
    description = db.Column(db.String, unique=False, nullable=True)

    def __init__(self, timestamp, ip):
        self.timestamp = timestamp
        self.ip = ip

    def __repr__(self):
        return json.dumps({'timestamp': self.timestamp,
                           'ip': self.ip})


repeat_item_to_tag = db.Table('repeat_item_to_tag', db.Model.metadata,
    db.Column('item_id', db.Integer, ForeignKey('repeat_item.id')),
    db.Column('tag_id', db.Integer, ForeignKey('tag.id'))
)


class Tag(db.Model):
    __tablename__ = 'tag'
    id = db.Column(BigInteger, primary_key=True)
    tag = db.Column(db.String, unique=True, nullable=False)
    count = db.Column(db.Integer, unique=False, nullable=False)
    items = relationship(
        "RepeatItem",
        secondary=repeat_item_to_tag,
        back_populates="tags")

    def __init__(self, tag, count):
        self.tag = tag
        self.count = count

    def __repr__(self):
        return json.dumps({'tag': self.tag,
                           'count': self.count})


class RepeatItem(db.Model):
    __tablename__ = 'repeat_item'
    id = db.Column(BigInteger, primary_key=True)
    date_created = db.Column(db.DateTime, unique=False, nullable=False)
    description = db.Column(db.String, unique=False, nullable=False)
    tags = relationship(
        "Tag",
        secondary=repeat_item_to_tag,
        back_populates="items")

    def __init__(self, date_created, description, tags):
        self.date_created = date_created
        self.description = description
        self.tags = tags

    # not used, to return repr(db_results_list)
    def __repr__(self):
        return json.dumps({'description': self.description,
                           'tags': json.loads(repr(self.tags))})


class DateRepeatItemLink(db.Model):
    id = db.Column(BigInteger, primary_key=True)
    date_to_repeat = db.Column(db.DateTime, unique=False, nullable=False)
    repeat_item_id = db.Column(BigInteger, ForeignKey('repeat_item.id'))
    repeat_item = relationship("RepeatItem")

    # TODO probably don't need to store it here - can just calculate each time from Item Created date
    added_days_ago = db.Column(db.Integer, unique=False, nullable=False)
    done = db.Column(db.Boolean, unique=False, nullable=False)

    def __init__(self, date_to_repeat, repeat_item_id, added_days_ago):
        self.date_to_repeat = date_to_repeat
        self.repeat_item_id = repeat_item_id
        self.added_days_ago = added_days_ago
        self.done = False if added_days_ago != 0 else True

    # not used, to return repr(db_results_list)
    def __repr__(self):
        return json.dumps({'date_to_repeat': self.date_to_repeat.isoformat(),
                           'repeat_item': json.loads(repr(self.repeat_item))})


DAY_REPEATS = [0, 1, 8, 16, 35, 70]


def add_days(days):
    return (date.today() + timedelta(days=days)).isoformat()


def process_repeats(db_result):
    if not db_result:
        return {'today': [], 'before': []}

    added_today = list(filter(lambda x: x.added_days_ago == 0, db_result))
    added_today.sort(key=lambda x: x.repeat_item.date_created)

    added_before = list(filter(lambda x: x.added_days_ago != 0, db_result))
    added_before.sort(key=lambda x: x.repeat_item.date_created)

    return {'today': added_today, 'before': added_before}


@app.route('/', methods=['GET', 'POST'])
def root():
    if request.method == 'POST':
        item = request.form.to_dict(flat=True)
        tags = []

        for tag in item['tags'].split(" "):
            old_tag = Tag.query.filter_by(tag=tag).first()
            if not old_tag:
                old_tag = Tag(tag, 1)
                db.session.add(old_tag)
            else:
                old_tag.count = old_tag.count + 1

            tags.append(old_tag)
        db.session.flush()

        repeat_item = RepeatItem(datetime.utcnow(), item['description'], tags)
        db.session.add(repeat_item)
        db.session.flush()

        for interval in DAY_REPEATS:
            dateItemLink = DateRepeatItemLink(add_days(interval), repeat_item.id, interval)
            db.session.add(dateItemLink)
        db.session.commit()
        return render_template('added_today_item.html',
                               item={'repeat_item': repeat_item})

    else:
        log_item = LogItem(datetime.utcnow(), request.access_route)
        db.session.add(log_item)
        db.session.commit()

        db_result = DateRepeatItemLink.query.filter_by(date_to_repeat=date.today()).all()

        return render_template('spaced_repetition.html', result=process_repeats(db_result))


# it is actually a GET, but Form data is dropped on GET, so POST was used
@app.route('/agenda', methods=['POST'])
def get_agenda():

    agenda_dates = request.form
    # TODO: check that not too much, pagination?
    # TODO: check arguments
    # TODO: error handling
    # TODO: filter added_days_ago==0
    if agenda_dates.get('is_range', False) and agenda_dates['agenda_end_date_input']:
        items_to_repeat = DateRepeatItemLink.query\
            .filter(
                DateRepeatItemLink.date_to_repeat >= agenda_dates['agenda_start_date_input'],
                DateRepeatItemLink.date_to_repeat <= agenda_dates['agenda_end_date_input'],
                not_(DateRepeatItemLink.added_days_ago == 0))\
            .all()
    else:
        items_to_repeat = DateRepeatItemLink.query\
            .filter(
                DateRepeatItemLink.date_to_repeat == agenda_dates['agenda_start_date_input'],
                not_(DateRepeatItemLink.added_days_ago == 0))\
            .all()

    return render_template('agenda_response.html',
                           items=items_to_repeat,
                           isRange=agenda_dates['agenda_end_date_input'],
                           dates=[agenda_dates['agenda_start_date_input'], agenda_dates['agenda_end_date_input']])


@app.route('/api/item_done_change', methods=['POST'])
def change_done():
    # TODO: check input & handle errors

    update_data = json.loads(request.data)
    link = db.session.query(DateRepeatItemLink).get(update_data['parent_id'])
    link.done = update_data['done']
    db.session.add(link)
    db.session.commit()

    return 'ok'


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 33508))
    app.run(debug=True, port=port)
