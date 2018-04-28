import os

from datetime import date, timedelta, datetime

from flask import Flask, render_template, request, url_for, redirect
from flask_pymongo import PyMongo
import json


app = Flask(__name__, static_url_path='')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', None)
app.config['MONGO_DBNAME'] = os.environ.get('MONGO_DBNAME', None)
app.config['MONGO_URI'] = os.environ.get('MONGO_URI', None)
app.config.from_pyfile('config.py', silent=True)
mongo = PyMongo(app)

DAY_REPEATS = [0, 1, 8, 16, 35, 70]


def add_days(days):
    return (date.today() + timedelta(days=days)).isoformat()


def process_repeats(db_result):
    if db_result is None:
        return {'today': [], 'before': []}

    repeat_items = db_result['items']

    added_today = list(filter(lambda x: x['added_days_ago'] == 0, repeat_items))
    added_today.sort(key=lambda x: x['added_timestamp'])

    added_before = list(filter(lambda x: x['added_days_ago'] != 0, repeat_items))
    added_before.sort(key=lambda x: x['added_timestamp'])

    return {'today': added_today, 'before': added_before, 'id': str(db_result['_id'])}


@app.route('/', methods=['GET', 'POST'])
def root():
    if request.method == 'POST':
        item = request.form.to_dict(flat=True)
        for interval in DAY_REPEATS:
            item["added_days_ago"] = interval
            item["added_timestamp"] = datetime.today()
            item["done"] = False

            mongo.db.repeats.update(
                {'date': add_days(interval)},
                {'$push': {'items': item}},
                upsert=True
            )
        return redirect(url_for('root'))

    else:
        db_result = mongo.db.repeats.find_one(
            {'date': date.today().isoformat()}
        )

        return render_template('spaced_repetition.html', result=process_repeats(db_result))


@app.route('/api/item_done_change', methods=['POST'])
def change_done():
    # TODO: check input & handle errors

    update_data = json.loads(request.data)

    mongo.db.repeats.update(
        {'_id': update_data['parent_id'], 'items.added_timestamp': update_data['added_timestamp']},
        {"$set": {"items.$.done": update_data['done']}}
    )

    return 'ok'


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 33508))
    app.run(debug=True, port=port)
