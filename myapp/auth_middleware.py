from functools import wraps
import jwt
from flask import request, jsonify
from flask import current_app

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if 'Authorization' in request.headers:
            token = request.headers['Authorization']
        if not token:
            return jsonify({'message' : 'Token is missing!'}), 401
        try:
            data=jwt.decode(token, current_app.config['SECRET_KEY'],algorithms=["HS256"])
            current_user=data
            
        except:
            return jsonify({
                'message' : 'Token is invalid!'
            }), 401

        return f(current_user, *args, **kwargs)

    return decorated