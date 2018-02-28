import os
from flask import Flask, render_template
from flask_pymongo import PyMongo

app = Flask(__name__,
            static_url_path='/static')
app.config.from_pyfile('config.py')
mongo = PyMongo(app)


@app.route('/')
def root():
    items = mongo.db.items.find()
    return render_template('spaced_repetition.html', items=items)


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 33508))
    app.run(debug=True, port=port)
