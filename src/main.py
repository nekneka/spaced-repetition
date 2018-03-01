import os

from datetime import date, timedelta
from flask import Flask, render_template, request, url_for
from flask_pymongo import PyMongo
from werkzeug.utils import redirect


app = Flask(__name__,
            static_url_path='/static')
app.config.from_pyfile('config.py', silent=True)
mongo = PyMongo(app)

DAY_REPEATS = [0, 1, 8, 16, 35, 70]


def add_days(days):
    return (date.today() + timedelta(days=days)).isoformat()


@app.route('/', methods=['GET', 'POST'])
def root():
    if request.method == 'POST':
        item = request.form.to_dict(flat=True)

        for interval in DAY_REPEATS:
            item["added_days_ago"] = interval
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
        return render_template('spaced_repetition.html', result=db_result)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 33508))
    app.run(debug=True, port=port)
