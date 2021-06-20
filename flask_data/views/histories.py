from flask_data.views.views import login_required
from flask import request, redirect, url_for, render_template, flash, session
from flask_data import db 
from flask import Blueprint
from flask_data.models.histories import Scheduled_History, Message_History, Job_History
from flask import current_app as app 
from sqlalchemy import desc

from flask_login import login_required, current_user

history = Blueprint('history', __name__)

# TODO: debug用の全履歴：後で消す
@history.route('/show')
def show_all_history():
    all_histories = Scheduled_History.query.all()
    return render_template('histories/show_all.html', all_histories=all_histories)

@history.route('/show/<string:user_id>')
@login_required
def show_history(user_id):
    message_histories = Message_History.query.filter(Message_History.user_id == user_id).order_by(desc(Message_History.timestamp)).limit(50).all()
    scheduled_histories = Scheduled_History.query.filter(Scheduled_History.user_id == user_id).order_by(desc(Scheduled_History.timestamp)).limit(50).all()
    job_histories = Job_History.query.filter(Job_History.user_id == user_id).order_by(desc(Job_History.timestamp)).limit(50).all()
    return render_template('histories/show.html', message_histories=message_histories, scheduled_histories=scheduled_histories, job_histories=job_histories)

@history.route('/show/line_bot_description')
def show_line_bot_description():
    return render_template('histories/line_bot_description.html')

@history.route('/show/info/<string:user_id>')
@login_required
def show_user_info(user_id):
    return render_template('histories/userinfo.html', username=current_user.username)
