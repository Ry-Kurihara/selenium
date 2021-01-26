from flask import Flask
from flask.helpers import url_for 
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object('flask_data.config')
    if test_config:
        app.config.from_mapping(test_config)

    db.init_app(app)

    from flask_data.views.views import view
    from flask_data.views.entries import entry
    app.register_blueprint(entry, url_prefix='/users')
    app.register_blueprint(view, url_prefix='/users')

    return app 