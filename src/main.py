import os
from datetime import date, timedelta, datetime
import json

from flask import Flask, render_template, request, redirect
from flask_mail import Mail
from flask_security import logout_user
from sqlalchemy.sql.elements import not_
from sqlalchemy.sql.expression import desc

from flask_security import Security, login_required, SQLAlchemySessionUserDatastore

from src.db.database import db_session, init_db
from src.models.login import Login, Register
from src.models.users import User, Role
from src.models.entries import LogItem, DateRepeatItemLink, RepeatItem, Tag

DAY_REPEATS = [0, 1, 8, 16, 35, 70]


app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', None)
app.config['SECURITY_PASSWORD_SALT'] = os.environ.get('SECURITY_PASSWORD_SALT', None)
app.config.from_pyfile('config.py', silent=True)
app.config['SECURITY_REGISTERABLE'] = True
app.config['SEND_REGISTER_EMAIL'] = False
app.config['MAIL_SUPPRESS_SEND'] = True
app.config['SECURITY_USER_IDENTITY_ATTRIBUTES'] = ('username', 'email')

# TODO: email confirmation
mail = Mail()
mail.init_app(app)


# Setup Flask-Security
user_datastore = SQLAlchemySessionUserDatastore(db_session, User, Role)
security = Security(app, user_datastore,
                    login_form=Login,
                    register_form=Register)

init_db()


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


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
@login_required
def root():
    if request.method == 'POST':
        item = request.form.to_dict(flat=True)
        tags = []

        for tag in set(item['tags'].split(",")):
            old_tag = Tag.query.filter_by(tag=tag).first()
            if not old_tag:
                old_tag = Tag(tag, 1)
                db_session.add(old_tag)
            else:
                old_tag.count = old_tag.count + 1

            tags.append(old_tag)

        db_session.flush()

        repeat_item = RepeatItem(datetime.utcnow(), item['description'], tags)
        db_session.add(repeat_item)
        db_session.flush()

        for interval in DAY_REPEATS:
            dateItemLink = DateRepeatItemLink(add_days(interval), repeat_item.id, interval)
            db_session.add(dateItemLink)
        db_session.commit()
        return render_template('added_today_item.html',
                               item={'repeat_item': repeat_item})

    else:
        print("req ac r" + str(request.access_route))
        log_item = LogItem(timestamp=datetime.utcnow(), ip=request.access_route[0])
        db_session.add(log_item)
        db_session.flush()

        db_result = DateRepeatItemLink.query.filter_by(date_to_repeat=date.today()).all()
        result = process_repeats(db_result)
        tags = Tag.query.order_by(desc('count')).limit(15).all()
        result['tags'] = tags

        return render_template('spaced_repetition.html', result=result)


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
    link = db_session.query(DateRepeatItemLink).get(update_data['parent_id'])
    link.done = update_data['done']
    db_session.add(link)
    db_session.commit()

    return 'ok'


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 33508))
    app.run(debug=True, port=port)
