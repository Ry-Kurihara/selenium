from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object('flask_data.config')
    if test_config:
        app.config.from_mapping(test_config)

    db.init_app(app)

    from flask_data.views.views import view
    from flask_data.views.histories import history
    app.register_blueprint(view, url_prefix='/')
    app.register_blueprint(history, url_prefix='/histories')

    from flask_line_api.line import line 
    app.register_blueprint(line)

    return app 