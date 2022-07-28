import os
from flask import Flask
import firebase_admin
from firebase_admin import credentials
from firebase_admin import storage
# from dotenv import load_dotenv
# load_dotenv()
from flask_mail import Mail
from flask_bcrypt import Bcrypt

app=Flask(__name__)
cred_obj = credentials.Certificate('key.json')
firebase_admin.initialize_app(cred_obj, {
	'databaseURL':'https://fyp-doorbell-cb008385-default-rtdb.firebaseio.com/',
    'storageBucket':'fyp-doorbell-cb008385.appspot.com'
	})
# SECRET_KEY = os.getenv('SECRET_KEY') or 'this is a secret'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['MAIL_SERVER'] = 'smtp.sendgrid.net'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'apikey'
app.config['MAIL_PASSWORD'] = os.environ.get('SENDGRID_API_KEY')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER')
mail = Mail(app)
bcrypt=Bcrypt(app)
bucket=storage.bucket()

from myapp import auth_routes
from myapp import profile_routes