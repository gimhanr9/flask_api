from firebase_admin import db
from datetime import datetime, timedelta
from flask import request
import jwt
import random
from myapp import app
from myapp import mail
from myapp import bcrypt
from flask_mail import Message



@app.route('/api/login',methods=['POST'])
def login():
    try:
        data=request.json
        if not data:
            return {
                'message': 'Please provide user details',
                'data': None,
                'error': 'Bad request'
            }, 400

        email=data.get('email')
        password=data.get('password')
        ref=db.reference('/users/')
        snapshot = ref.order_by_child('email').equal_to(email).get()
        if len(snapshot) == 0:
            return{
                'message':'Invalid email or password',
                'data':None
            },404
        
        for key,val in snapshot.items():
            db_name=val.get('name')
            db_email=val.get('email')
            db_password=val.get('password')
            is_matching=bcrypt.check_password_hash(db_password, password)
            if is_matching is True:
                token_user={
                'id':key,
                'name':db_name,
                'email':db_email,
                'exp' : datetime.utcnow() + timedelta(hours = 24)
                }
                encoded_token=jwt.encode(token_user,app.config['SECRET_KEY'],algorithm="HS256")
                return {
                    'message':'Login successful',
                    'data': encoded_token
                },200
            return {
                'message':'Invalid email or password',
                'data':None
            },401

    except Exception as e:
        return {
                'message': 'Something went wrong!',
                'error': str(e),
                'data': None
        }, 500


@app.route('/api/register',methods=['POST'])
def register():
    try:
        data=request.json
        if not data:
            return {
                'message': 'Please provide user details',
                'data': None,
                'error': 'Bad request'
            }, 400
        
        email=data.get('email')
        name=data.get('name')
        password=data.get('password')
        encrypted_password=bcrypt.generate_password_hash(password,10).decode('utf-8')
        ref=db.reference('/users/')
        snapshot = ref.order_by_child('email').equal_to(email).get()
        if len(snapshot) == 0:
            user_ref=ref.push({
                'name': name,
                'email': email,
                'password':encrypted_password,
                'otp':0,
                'failedAttempts':0})

            token_user={
                'id':user_ref.key,
                'name':name,
                'email':email,
                'exp' : datetime.utcnow() + timedelta(hours = 24)
            }
            jwt_token=jwt.encode(token_user,app.config['SECRET_KEY'],algorithm="HS256")
            return{
                'message':'Successfully registered',
                'data':jwt_token
            }, 200

        return{
            'message':'Email already exists',
            'data': None
        }, 409

    except Exception as e:
        return {
                'message': 'Something went wrong!',
                'error': str(e),
                'data': None
        }, 500


@app.route('/api/forgotpassword',methods=['POST'])
def forgot_password():
    try:
        data=request.json
        if not data:
            return {
                'message': 'Please provide user details',
                'data': None,
                'error': 'Bad request'
            }, 400

        email=data.get('email')
        ref=db.reference('/users/')
        snapshot = ref.order_by_child('email').equal_to(email).get()
        if len(snapshot) == 0:
            return{
                'message':'Invalid email',
                'data':None
            },404
        
        rand_otp=random.randint(1000,9999)
        
        msg=Message('Forgot Password OTP',recipients=[email])
        msg.body='Find the 4-digit OTP to reset your password'
        msg.html=f'<p>{rand_otp}</p>'
        mail.send(msg)
        for key in snapshot:
            ref.child(key).update({
                'otp':rand_otp
            })
        return {
            'message':'OTP sent to email',
            'data':None
        },200
    except Exception as e:
        return {
                'message': 'Something went wrong!',
                'error': str(e),
                'data': None
        }, 500


@app.route('/api/checkotp',methods=['POST'])
def check_otp():
    try:
        data=request.json
        if not data:
            return {
                'message': 'Please provide user details',
                'data': None,
                'error': 'Bad request'
            }, 400

        email=data.get('email')
        otp=data.get('otp')
        ref=db.reference('/users/')
        snapshot = ref.order_by_child('email').equal_to(email).get()
        if len(snapshot) == 0:
            return{
                'message':'Invalid email',
                'data':None
            },404

        for key,val in snapshot.items():
            db_otp=val.get('otp')
            failed_attempts=val.get('failedAttempts')
            if otp != db_otp:
                ref.child(key).update({
                    'failedAttempts':failed_attempts + 1
                })
                if failed_attempts == 2:
                    ref.child(key).update({
                        'otp':0,
                        'failedAttempts':0
                    })
                    return {
                        'message':'You have entered the incorrect OTP too many times',
                        'data':None
                    },429
                
                return {
                    'message':'Incorrect OTP',
                    'data':None
                },401
            return {
                'message':'OTP verified',
                'data':None
            },200

    except Exception as e:
        return {
                'message': 'Something went wrong!',
                'error': str(e),
                'data': None
        }, 500


@app.route('/api/resetpassword',methods=['POST'])
def reset_password():
    try:
        data=request.json
        if not data:
            return {
                'message': 'Please provide user details',
                'data': None,
                'error': 'Bad request'
            }, 400

        email=data.get('email')
        password=data.get('password')
        ref=db.reference('/users/')
        snapshot = ref.order_by_child('email').equal_to(email).get()
        if len(snapshot) == 0:
            return{
                'message':'Invalid email',
                'data':None
            },404

        encrypted_password=bcrypt.generate_password_hash(password,10).decode('utf-8')
        for key in snapshot:
            ref.child(key).update({
                'otp':0,
                'password':encrypted_password,
                'failedAttempts':0
            })
        return {
            'message':'Password reset successful',
            'data':None
        },200
    except Exception as e:
        return {
                'message': 'Something went wrong!',
                'error': str(e),
                'data': None
        }, 500





