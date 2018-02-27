import os
from flask import Flask, render_template

import config

app = Flask(__name__,
            static_url_path='/static')
app.config['SECRET_KEY'] = config.flask['secret_key']


@app.route('/')
def root():
    return render_template('example.html', param='Flask')


if __name__ == '__main__':
    port = int(os.environ.get("PORT", 33508))
    app.run(debug=True, port=port)
