from flask import request, redirect, url_for, render_template, flash, session 
from functools import wraps
from flask import Blueprint
from flask import current_app as app 

from werkzeug.security import generate_password_hash, check_password_hash
import sys, os
sys.path.append(os.path.join(os.path.dirname(__file__), '../models/'))
from histories import User
from flask_login import login_user, logout_user, login_required
from flask_data import db 

view = Blueprint('view', __name__)

@view.route('/')
def display_top_page():
    return render_template('top.html')

@view.route('/signup')
def signup():
    return render_template('signup.html')


@view.route('/signup', methods=['POST'])
def signup_post():
    user_id = request.form.get('user_id')
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(user_id=user_id).first()

    if user:
        flash('Email address already exists!!')
        return redirect(url_for('view.signup'))

    new_user = User(user_id=user_id, username=username, password=generate_password_hash(password, method='sha256'))

    db.session.add(new_user)
    db.session.commit()

    flash('正常に登録できました。ログインしてください！')
    return redirect(url_for('view.login'))


@view.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False 

        user = User.query.filter_by(user_id=user_id).first()

        if not user or not check_password_hash(user.password, password):
            flash('Please check your login details and try again!!')
            return redirect(url_for('view.login'))
        
        login_user(user, remember=remember)
        flash('ログインしました！')
        return redirect(url_for('view.display_top_page'))
    
    # GETメソッドの場合
    return render_template('login.html')

@view.route('/logout')
@login_required
def logout():
    logout_user()
    flash('ログアウトしました')
    return redirect(url_for('view.display_top_page'))

@view.app_errorhandler(404)
def non_existant_route(error):
    return redirect(url_for('view.login'))