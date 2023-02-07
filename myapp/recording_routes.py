from firebase_admin import db
from myapp import app
from myapp.auth_middleware import token_required


@app.route('/api/getrecordings',methods=['GET'])
@token_required
def get_recordings(current_user):
    try:
        user_id=current_user.get('id')
        recording_ref=db.reference('/recordings/' + user_id)
        recording_snapshot=recording_ref.get()
        data_list=[]
        if recording_snapshot is not None:
            for key,val in recording_snapshot.items():
                json_object={'id':key,'url':val['recordingUrl'],'name':val['name']}
                data_list.append(json_object)

        return {
            'message':'Successfully fetched recording data',
            'data':data_list
        },200
    except Exception as e:
        return {
                'message': 'Something went wrong!',
                'error': str(e),
                'data': None
        }, 500