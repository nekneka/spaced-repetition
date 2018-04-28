import os
from datetime import date, timedelta, datetime
import json

from flask import Flask, render_template, request, url_for, redirect
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


class RepeatItem(db.Model):
    id = db.Column(BigInteger, primary_key=True)
    date_created = db.Column(db.DateTime, unique=False, nullable=False)
    description = db.Column(db.String, unique=False, nullable=False)
    # move to separate table
    tags = db.Column(db.String, unique=False, nullable=True)

    def __init__(self, date_created, description, tags):
        self.date_created = date_created
        self.description = description
        self.tags = tags

    def __repr__(self):
        return '<Repeat Item info %r>' % self.repeat_item_id


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
        self.done = False

    def __repr__(self):
        return '<Date info %r>' % self.repeat_item_id


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
        repeat_item = RepeatItem(date.today(), item['description'], item['tags'])
        db.session.add(repeat_item)
        db.session.flush()

        for interval in DAY_REPEATS:
            dateItemLink = DateRepeatItemLink(add_days(interval), repeat_item.id, interval)
            db.session.add(dateItemLink)
        db.session.commit()
        return redirect(url_for('root'))

    else:
        db_result = DateRepeatItemLink.query.filter_by(date_to_repeat=date.today()).all()

        return render_template('spaced_repetition.html', result=process_repeats(db_result))


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
