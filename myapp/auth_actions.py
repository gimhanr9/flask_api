from firebase_admin import db

def validate_login(email,password):
    ref=db.reference('/users/')
    snapshot = ref.order_by_child('email').equal_to(email).get()
    if snapshot is None:
        return{
            'message':'Invalid email or password'
        }
    for key in snapshot:
        print(key)

def register(email,name,password):
    ref=db.reference('/users/')
    snapshot = ref.order_by_child('email').equal_to(email).get()
    if snapshot is None:
        return{
            'message':'Email or password is invalid'
        }
    for key in snapshot:
        print(key)
    