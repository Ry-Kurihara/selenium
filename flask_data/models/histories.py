from flask_data import db
from flask_login import UserMixin

class Scheduled_History(db.Model):
    __tablename__ = 'line_purchase_list'
    __table_args__ = {'extend_existing': True}
    item_url = db.Column(db.Text, primary_key=True)
    product_title = db.Column(db.Text, primary_key=True)
    timestamp = db.Column(db.Text, primary_key=True)
    user_id = db.Column(db.Text, primary_key=True)

    def __init__(self, item_url=None, product_title=None, timestamp=None, user_id=None):
        self.item_url = item_url
        self.product_title = product_title
        self.timestamp = timestamp
        self.user_id = user_id

    def __repr__(self):
        return '<Scheduled_History product_title:{} user_id:{} timestamp:{}>'.format(self.product_title, self.user_id, self.timestamp)

class Message_History(db.Model):
    __tablename__ = 'line_autopurchase'
    __table_args__ = {'extend_existing': True}
    message = db.Column(db.Text, primary_key=True)
    timestamp = db.Column(db.Text, primary_key=True)
    user_id = db.Column(db.Text, primary_key=True)

    def __init__(self, message=None, timestamp=None, user_id=None):
        self.message = message
        self.timestamp = timestamp
        self.user_id = user_id

    def __repr__(self):
        return '<Message_History message:{} user_id:{} timestamp:{}>'.format(self.message, self.user_id, self.timestamp)

class Job_History(db.Model):
    __tablename__ = 'line_purchase_job_history'
    __table_args__ = {'extend_existing': True}
    job_message = db.Column(db.Text, primary_key=True)
    timestamp = db.Column(db.Text, primary_key=True)
    user_id = db.Column(db.Text, primary_key=True)
    item_url = db.Column(db.Text, primary_key=True)

    def __init__(self, job_message=None, timestamp=None, user_id=None, item_url=None):
        self.job_message = job_message
        self.timestamp = timestamp
        self.user_id = user_id
        self.item_url = item_url



class User(UserMixin, db.Model):
    __tablename__ = 'user_auth'
    __table_args__ = {'extend_existing': True}
    user_id = db.Column(db.Text, unique=True, primary_key=True)
    username = db.Column(db.Text)
    password = db.Column(db.Text)

    def __init__(self, user_id=None, username=None, password=None):
        self.user_id = user_id 
        self.username = username 
        self.password = password

    def get_id(self):
        return (self.user_id)