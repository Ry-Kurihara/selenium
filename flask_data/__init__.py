from flask import Flask 
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
# configファイルを使うとtimezoneエラーが起こる
app.config.from_object('flask_data.config')

db = SQLAlchemy(app)

from flask_data.views import views, entries