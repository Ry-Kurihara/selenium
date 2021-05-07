from flask_data.views.views import login_required
from flask import request, redirect, url_for, render_template, flash, session
from flask_data import db 
from flask import Blueprint
from flask_data.models.histories import Scheduled_History, Message_History
from flask import current_app as app 

history = Blueprint('history', __name__)

# TODO: debug用の全履歴：後で消す
@history.route('/show')
def show_all_history():
    all_histories = Scheduled_History.query.all()
    return render_template('histories/show_all.html', all_histories=all_histories)

# TODO: login requireにしたい
@history.route('/show/<string:user_id>')
def show_history(user_id):
    histories = Message_History.query.filter(Message_History.user_id == user_id).all()
    return render_template('histories/show.html', histories=histories)
