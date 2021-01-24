from flask import Flask 

app = Flask(__name__)
# configファイルを使うとtimezoneエラーが起こる
app.config.from_object('flask_data.config')

import flask_data.views