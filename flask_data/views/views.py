from flask import request, redirect, url_for, render_template, flash, session 
from functools import wraps
from flask import Blueprint
from flask import current_app as app 

from werkzeug.security import generate_password_hash, check_password_hash
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '../models/'))
from histories import User
from flask_data import db 

view = Blueprint('view', __name__)

def login_required(view):
    @wraps(view)
    def inner(*args, **kwargs):
        if not session.get('logged_in'):
            return redirect(url_for('view.login'))
        return view(*args, **kwargs)
    return inner

@view.route('/')
def display_top_page():
    return render_template('top.html')


@view.route('/signup', methods=['POST'])
def signup_post():
    user_id = request.form.get('user_id')
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(user_id=user_id).first()

    if user:
        flash('Email address already exists!!')
        return redirect(url_for('auth.signup'))

    new_user = User(user_id=user_id, username=username, password=generate_password_hash(password, method='sha256'))

    db.session.add(new_user)
    db.session.commit()

    return redirect(url_for('auth.login'))


@view.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['username'] != app.config['USERNAME']:
            flash('ユーザ名が異なります')
        elif request.form['password'] != app.config['PASSWORD']:
            flash('パスワードが異なります')
        elif request.form['user_id'] != app.config['USER_ID']:
            flash('ユーザIDが異なります')
        else:
            session['logged_in'] = True
            session['user_id'] = request.form['user_id']
            flash('ログインしました')
            return redirect(url_for('view.display_top_page'))
    return render_template('login.html')

@view.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('ログアウトしました')
    return redirect(url_for('view.display_top_page'))

@view.app_errorhandler(404)
def non_existant_route(error):
    return redirect(url_for('view.login'))