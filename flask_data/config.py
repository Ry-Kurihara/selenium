import os 
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass 

SQLALCHEMY_DATABASE_URI = os.environ["HEROKU_POSTGRES_URL"]
SQLALCHEMY_TRACK_MODIFICATIONS = True 

DEBUG = True
USERNAME = 'john'
PASSWORD = 'due123'
SECRET_KEY = 'secret key'