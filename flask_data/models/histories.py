from flask_data import db

class Scheduled_History(db.Model):
    __tablename__ = 'line_purchase_list'
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
    message = db.Column(db.Text, primary_key=True)
    timestamp = db.Column(db.Text, primary_key=True)
    user_id = db.Column(db.Text, primary_key=True)

    def __init__(self, message=None, timestamp=None, user_id=None):
        self.message = message
        self.timestamp = timestamp
        self.user_id = user_id

    def __repr__(self):
        return '<Message_History message:{} user_id:{} timestamp:{}>'.format(self.message, self.user_id, self.timestamp)