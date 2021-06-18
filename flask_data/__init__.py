from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_apscheduler import APScheduler
from flask_login import LoginManager

db = SQLAlchemy()
scheduler = APScheduler()

def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_object('flask_data.config')
    if test_config:
        app.config.from_mapping(test_config)

    db.init_app(app)

    login_manager = LoginManager()
    login_manager.login_view = 'view.login'
    login_manager.init_app(app)

    from flask_data.models.histories import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    from flask_data.views.views import view
    from flask_data.views.histories import history
    app.register_blueprint(view, url_prefix='/')
    app.register_blueprint(history, url_prefix='/histories')

    from flask_line_api.line import line 
    app.register_blueprint(line)

    # initialize scheduler 
    scheduler.init_app(app)
    scheduler.start()

    return app 