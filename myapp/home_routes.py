from firebase_admin import db
from datetime import datetime, timedelta
from flask import request
from myapp import app
from myapp import bucket
from myapp.auth_middleware import token_required

@app.route('/api/getactivities',methods=['GET'])
@token_required
def get_activities(current_user):
    try:
        user_id=current_user.get('id')
        visitor_ref=db.reference('/activities/' + user_id)
        visitor_snapshot=visitor_ref.get()
        data_list=[]
        user_data={'name':current_user.get('name'),'email':current_user.get('email')}
        if visitor_snapshot is not None:
            for key,val in visitor_snapshot.items():
              
                json_object={'id':key,'name':val['name'],'date':val['date'],'time':val['time'],'imageUrl':val['imageUrl']}
                data_list.append(json_object)
        

        all_data={'user_details':user_data,'activities':data_list}
                
        return {
            'message':'Successfully fetched profile data',
            'data':all_data
        },200
    except Exception as e:
        return {
                'message': 'Something went wrong!',
                'error': str(e),
                'data': None
        }, 500