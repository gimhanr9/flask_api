from datetime import datetime
import os
import requests
import json
from firebase_admin import db
from flask import request
from myapp import app
from myapp import bucket
from myapp.common import recognize_face

@app.route('/api/recognizevisitor',methods=['POST'])
def recognize_visitor():
    try:
        one_signal_url=os.environ.get('ONE_SIGNAL_URL')
        
        now = datetime.now()
        date_n = now.strftime("%d/%m/%Y")
        date_ns = now.strftime("%d-%m-%Y")
        time_n = now.strftime("%H:%M:%S")
        time_ns = now.strftime("%H-%M-%S")
        #data=request.json
        
       
        id=request.form.get('user_id')
       
        if not id:
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
        
        image_path=r'myapp/images/'+ date_ns + "-" + time_ns + image_file.filename 
        print(image_path)
        
        image_file.save(image_path)
     
        user_ref=db.reference('/users/' + id)
        user_onesignal_id=""
        snapshot = user_ref.get()
        
        if snapshot is not None:
           
            user_onesignal_id=snapshot.get('onesignalId')

        visitor_ref=db.reference('/visitors/' + id)
        
        visitor_snapshot=visitor_ref.get()
        data_list=[]
        image_url_list=[]
        name_list=[]
        
        if visitor_snapshot is not None:
            for key,val in visitor_snapshot.items():
                json_object={'id':key,'imageUrl':val['imageUrl'],'fname':val['firstName'],'lname':val['lastName']}
                data_list.append(json_object)
                image_url_list.append(val['imageUrl'])
                w_name=val['firstName'] + " " + val['lastName']
                name_list.append(w_name)

        recognition_status_name="Unrecognized"

        status=recognize_face(image_path,image_url_list)
        
        if status >= 0:
            # rec_fname=data_list[status]['fname']
            # rec_lname=data_list[status]['lname']
            recognition_status_name=name_list[status]
       

        blob=bucket.blob(image_path)
        print(image_path)
        
        blob.upload_from_filename(image_path)
       
        blob.make_public()
        
        image_url=blob.public_url
      
        activity_ref=db.reference('/activities/' + id)
       
       
        activity_ref.push({'name':recognition_status_name,'date':date_n,'time':time_n,'imageUrl':image_url})
        
        payload = {
            "app_id": os.environ.get('ONE_SIGNAL_APP_ID'),
            "included_segments": ["included_player_ids"],
            "include_player_ids": [user_onesignal_id],
            "content_available":True,
            "headings": {
                "en": "Visitor Alert",
            },
            "contents": {
                "en": "{} is here. Tap to talk them.".format(recognition_status_name),
            },
            "name": "INTERNAL_CAMPAIGN_NAME"
        }
        headers = {
            "Accept": "application/json",
            "Authorization": "Basic " + os.environ.get('ONE_SIGNAL_API_KEY'),
            "Content-Type": "application/json; charset=utf-8"
        }
        print(payload)

        response = requests.post(one_signal_url, json=payload, headers=headers)
        print(response)
        print(response.text)
        

        return {
            'message':'Activity added successfully',
            'data':None
        },200
        
    except Exception as e:
        return {
                'message': 'Something went wrong!',
                'error': str(e),
                'data': None
        }, 500


@app.route('/api/addrecording',methods=['POST'])
def add_recording():
    try:
        #data=request.json
        # if not data:
        #     return {
        #         'message': 'Please provide visitor details',
        #         'data': None,
        #         'error': 'Bad request'
        #     }, 400
        now = datetime.now()
        date_n = now.strftime("%d/%m/%Y")
        date_ns = now.strftime("%d-%m-%Y")
        time_n = now.strftime("%H:%M:%S")
        time_ns = now.strftime("%H-%M-%S")

        id=request.form.get('user_id')
        if not id:
            return {
                'message': 'Please provide details',
                'data': None,
                'error': 'Bad request'
            }, 400

        name=request.form.get('file_name')
        if not name:
            return {
                'message': 'Please provide details',
                'data': None,
                'error': 'Bad request'
            }, 400
        video_file = request.files['video']
        if video_file.filename == '':
            return {
                'message':'File not found',
                'data':None,
                'error': 'Bad request'
            }, 400
        video_path='./videos/'+ date_ns + time_ns + video_file.filename
        video_file.save(video_path)
        blob=bucket.blob(video_path)
        blob.upload_from_filename(video_path)
        blob.make_public()
        video_url=blob.public_url
        recording_ref=db.reference('/recordings/' + id)
        recording_ref.push({'recordingUrl':video_url,'name':name})
       
        return {
            'message':'Recording added successfully',
            'data':None
        },200

        
    except Exception as e:
        return {
                'message': 'Something went wrong!',
                'error': str(e),
                'data': None
        }, 500
