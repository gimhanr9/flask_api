import cv2
from firebase_admin import db
from datetime import datetime, timedelta
from flask import request
import jwt
from requests import delete
from myapp import app
from myapp import bucket
from myapp.auth_middleware import token_required
from myapp.common import detect_face
	

@app.route('/api/getprofile',methods=['GET'])
@token_required
def get_profile(current_user):
    try:
        user_id=current_user.get('id')
        ref=db.reference('/users/' + user_id)
        snapshot = ref.get()
        if snapshot is not None:
            user_data={'name':snapshot.get('name'),'email':snapshot.get('email')}

        return {
            'message':'Successfully fetched profile data',
            'data':user_data
        },200
    except Exception as e:
        return {
                'message': 'Something went wrong!',
                'error': str(e),
                'data': None
        }, 500


@app.route('/api/getvisitors',methods=['GET'])
@token_required
def get_visitors(current_user):
    try:
        user_id=current_user.get('id')
        visitor_ref=db.reference('/visitors/' + user_id)
        visitor_snapshot=visitor_ref.get()
        data_list=[]
        if visitor_snapshot is not None:
            for key,val in visitor_snapshot.items():
                json_object={'id':key,'imageUrl':val['imageUrl'],'fname':val['firstName'],'lname':val['lastName']}
                data_list.append(json_object)

        return {
            'message':'Successfully fetched visitor data',
            'data':data_list
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
                'data':None,
                'error':'Unauthorized'
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
                    'data':None,
                    'error':'Conflict'
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
        #data=request.json
        # if not data:
        now = datetime.now()
        date_n = now.strftime("%d/%m/%Y")
        date_ns = now.strftime("%d-%m-%Y")
        time_n = now.strftime("%H:%M:%S")
        time_ns = now.strftime("%H-%M-%S")
            
        user_id=current_user.get('id')
        
        fname=request.form.get('fname')
        
        if not fname:
            return {
                'message': 'Please provide visitor details',
                'data': None,
                'error': 'Bad request'
            }, 400
        
        lname=request.form.get('lname')
        if not lname:
            return {
                'message': 'Please provide visitor details',
                'data': None,
                'error': 'Bad request'
            }, 400
        image_file = request.files['file']
        
        if image_file.filename == '':
            return {
                'message':'File not found',
                'data':None,
                'error': 'Bad request'
            }, 400
        image_path=r'myapp/images/' + image_file.filename
       
        image_file.save(image_path)
        
        read_image=cv2.imread(image_path)
        
        image_raw=read_image.copy()
        
        aligned_face=detect_face(read_image,False,image_raw)
        
        if aligned_face is False:
            return {
                'message':'Face not found',
                'data':None,
                'error': 'Bad request'
            }, 400

        detected_face=detect_face(aligned_face,True,image_raw)
        
        if detected_face is False:
            return {
                'message':'Face not found',
                'data':None,
                'error': 'Bad request'
            }, 400

        image_path=r'myapp/images/' + date_ns + time_ns + image_file.filename
       
        cv2.imwrite(image_path,detected_face)
        
        blob=bucket.blob(image_path)
        blob.upload_from_filename(image_path)
        blob.make_public()
        image_url=blob.public_url
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



@app.route('/api/editvisitor',methods=['POST'])
@token_required
def edit_visitor(current_user):
    try:
        #data=request.json
        #if not data:
        now = datetime.now()
        date_n = now.strftime("%d/%m/%Y")
        date_ns = now.strftime("%d-%m-%Y")
        time_n = now.strftime("%H:%M:%S")
        time_ns = now.strftime("%H-%M-%S")
            
        user_id=current_user.get('id')
        visitor_id=request.form.get('id')
        if not visitor_id:
            return {
                'message': 'Please provide visitor details',
                'data': None,
                'error': 'Bad request'
            }, 400
        fname=request.form.get('fname')
        if not fname:
            return {
                'message': 'Please provide visitor details',
                'data': None,
                'error': 'Bad request'
            }, 400
        lname=request.form.get('lname')
        if not lname:
            return {
                'message': 'Please provide visitor details',
                'data': None,
                'error': 'Bad request'
            }, 400
        previous_image=request.form.get('image_url')
        
        if not previous_image:
            return {
                'message': 'Please provide visitor details',
                'data': None,
                'error': 'Bad request'
            }, 400
        image_file = request.files['file']
        if image_file.filename == '':
            return {
                'message':'File not found',
                'data':None,
                'error': 'Bad request'
            }, 400

        image_path=r'myapp/images/' + date_ns + time_ns + image_file.filename
        image_file.save(image_path)
        read_image=cv2.imread(image_path)
        image_raw=read_image.copy()
        aligned_face=detect_face(read_image,False,image_raw)
        if aligned_face is None:
            return {
                'message':'Face not found',
                'data':None,
                'error': 'Bad request'
            }, 400
        
        detected_face=detect_face(aligned_face,True,image_raw)
        if detected_face is None:
            return {
                'message':'Face not found',
                'data':None,
                'error': 'Bad request'
            }, 400
        
        save_path=r"myapp/images/final_image.jpg"
        
        cv2.imwrite(save_path,detected_face)
        
        previous_blob=bucket.blob(previous_image)
       
        #previous_blob.delete()
        
        blob=bucket.blob(save_path)
       
        blob.upload_from_filename(save_path)
        blob.make_public()
        image_url=blob.public_url
        visitor_ref=db.reference('/visitors/' + user_id)
        visitor_ref.child(visitor_id).update({'imageUrl':image_url,'firstName':fname,'lastName':lname})
       
        return {
            'message':'Visitor edited successfully',
            'data':None
        },200
    except Exception as e:
        return {
                'message': 'Something went wrong!',
                'error': str(e),
                'data': None
        }, 500


@app.route('/api/deletevisitor',methods=['POST'])
@token_required
def delete_visitor(current_user):
    try:
        data=request.json
        if not data:
            return {
                'message': 'Please provide visitor details',
                'data': None,
                'error': 'Bad request'
            }, 400

        user_id=current_user.get('id')
        visitor_id=data.get('id')
        image_url=data.get('image_url')
        blob=bucket.blob(image_url)
        #blob.delete()
        visitor_ref=db.reference('/visitors/' + user_id + '/' + visitor_id)
        visitor_ref.delete()
       
        return {
            'message':'Visitor removed successfully',
            'data':None
        },200
    except Exception as e:
        return {
                'message': 'Something went wrong!',
                'error': str(e),
                'data': None
        }, 500
