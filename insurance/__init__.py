from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_mail import Mail

app = Flask(__name__)
app.config['SECRET_KEY'] = '5791628bb0b13ce0c676dfde280ba245'
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgres://fmiljksogiilds:f18e4c7cd5e738294d6afddfac2db779ee8bbe24beb8d99b95d37c93696ee272@ec2-52-21-252-142.compute-1.amazonaws.com:5432/d76bl6j1modhmf'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'
Migrate(app, db, render_as_batch=True)

app.config['MAIL_SERVER'] = 'smtp.googlemail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'quickauths@gmail.com'
app.config['MAIL_PASSWORD'] = 'Pass123!'
app.config['CELERY_BROKER_URL'] = 'redis://:p8750f9e4294d018a66bf25e9d4a4eced40ebf76b1c0a90f18c9ef222b638faa1@ec2-54-157-119-18.compute-1.amazonaws.com:7239'
# app.config['broker_url'] = 'redis://localhost:6379'
app.config['CELERY_RESULT_BACKEND'] = 'redis://:p8750f9e4294d018a66bf25e9d4a4eced40ebf76b1c0a90f18c9ef222b638faa1@ec2-54-157-119-18.compute-1.amazonaws.com:7239'
# app.config['result_backend'] = 'redis://localhost:6379'
mail = Mail(app)

from insurance import routes