import os 
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '../my_lib'))
import param_store as ps

from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from sqlalchemy import create_engine

SQLALCHEMY_DATABASE_URI = ps.get_parameters('/heroku/postgres_url')
SQLALCHEMY_TRACK_MODIFICATIONS = True 

DEBUG = True
SECRET_KEY = 'secret key'

# flask-apscheduler
SCHEDULER_API_ENABLED = True
engine = create_engine(SQLALCHEMY_DATABASE_URI)
SCHEDULER_JOBSTORES = {"default": SQLAlchemyJobStore(engine=engine, tablename='line_ps5_jobstore')}