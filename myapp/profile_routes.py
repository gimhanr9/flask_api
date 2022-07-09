from firebase_admin import db
from datetime import datetime, timedelta
from flask import request
import jwt
from myapp import app
from myapp import bucket
from myapp.auth_middleware import token_required



@app.route('/api/getprofile',methods=['GET'])
@token_required
def get_profile(current_user):
    try:
        user_id=current_user.get('id')
        ref=db.reference('/users/' + user_id)
        visitor_ref=db.reference('/visitors/' + user_id)
        snapshot = ref.get()
        if snapshot is None:
            return{
                'message':'Unauthorized access',
                'data':None
            },401

        profile_data=[]
        user_data={'name':snapshot.get('name'),'email':snapshot.get('email')}
        profile_data.append(user_data)
        visitor_snapshot=visitor_ref.get()
        if visitor_snapshot is not None:
            for key,val in visitor_snapshot:
                print(key)
        
        print(profile_data)
        return {
            'message':'Successfully fetched profile data',
            'data':profile_data
        },200
    except Exception as e:
        return {
                'message': 'Something went wrong!',
                'error': str(e),
                'data': None
        }, 500




@app.route('/api/editprofile',methods=['POST'])
@token_required
def edit_profile(current_user):
    try:
        data=request.json
        if not data:
            return {
                'message': 'Please provide user details',
                'data': None,
                'error': 'Bad request'
            }, 400

        name=data.get('name')
        user_id=current_user.get('id')
        previous_email=current_user.get('email')
        new_email=data.get('email')
        ref=db.reference('/users/')
        snapshot = ref.order_by_child('email').equal_to(previous_email).get()
        if len(snapshot) == 0:
            return {
                'message':'Unauthorized access',
                'data':None
            },401
        else:
            if previous_email == new_email:
                ref.child(user_id).update({
                    'name':name
                })
                token_user={
                    'id':user_id,
                    'name':name,
                    'email':previous_email,
                    'exp' : datetime.utcnow() + timedelta(hours = 24)
                }
                jwt_token=jwt.encode(token_user,app.config['SECRET_KEY'],algorithm="HS256")
                return {
                    'message':'Successfully updated user details',
                    'data':jwt_token
                },200
            else:
                new_snapshot = ref.order_by_child('email').equal_to(new_email).get()
                if len(new_snapshot) == 0:
                    ref.child(user_id).update({      
                        'name':name,
                        'email':new_email
                    })
                    token_user_new={
                        'id':user_id,
                        'name':name,
                        'email':new_email,
                        'exp' : datetime.utcnow() + timedelta(hours = 24)
                    }
                    jwt_token_new=jwt.encode(token_user_new,app.config['SECRET_KEY'],algorithm="HS256")
                    return {
                        'message':'Successfully updated user details',
                        'data':jwt_token_new
                    },200

                return {
                    'message':'Email already exists',
                    'data':None
                },409
        
    except Exception as e:
        return {
            'message': 'Something went wrong!',
            'error': str(e),
            'data': None
        }, 500



@app.route('/api/addvisitor',methods=['POST'])
@token_required
def add_visitor(current_user):
    try:
        data=request.json
        if not data:
            return {
                'message': 'Please provide user details',
                'data': None,
                'error': 'Bad request'
            }, 400

        user_id=current_user.get('id')
        fname=data.get('fname')
        lname=data.get('lname')
        image_url=''
        visitor_ref=db.reference('/visitors/' + user_id)
        visitor_ref.push({'imageUrl':image_url,'firstName':fname,'lastName':lname})
       
        return {
            'message':'Visitor added successfully',
            'data':None
        },200
    except Exception as e:
        return {
                'message': 'Something went wrong!',
                'error': str(e),
                'data': None
        }, 500

