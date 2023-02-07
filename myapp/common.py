import numpy as np
import urllib
import pandas as pd
from PIL import Image
import math
import cv2
import tensorflow as tf

face_detector_path = r"myapp/data/haarcascade_frontalface_default.xml"
eye_detector_path = r"myapp/data/haarcascade_eye.xml"
face_detector = cv2.CascadeClassifier(face_detector_path)
eye_detector = cv2.CascadeClassifier(eye_detector_path)
proto=r"myapp/face_detector/deploy.prototxt"
caffe_model=r"myapp/face_detector/res10_300x300_ssd_iter_140000.caffemodel"
net = cv2.dnn.readNet(proto, caffe_model)
model_path=r"myapp/models/arcface_final.h5"
model = tf.keras.models.load_model(model_path)
cos_dis = lambda x, y: tf.norm(x-y)

def euclidean_distance(a, b):
	x1 = a[0]; y1 = a[1]
	x2 = b[0]; y2 = b[1]
	return math.sqrt(((x2 - x1) * (x2 - x1)) + ((y2 - y1) * (y2 - y1)))

def align_face(img):
    img_raw = img.copy()
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    eyes = eye_detector.detectMultiScale(img_gray)
    
    
    if len(eyes) >= 2:
        base_eyes = eyes[:, 2]
        items = []
        for i in range(0, len(base_eyes)):
            item = (base_eyes[i], i)
            items.append(item)
        
        df = pd.DataFrame(items, columns = ["length", "idx"]).sort_values(by=['length'], ascending=False)
        
        eyes = eyes[df.idx.values[0:2]]
        
        #--------------------
        #decide left and right eye
        
        eye_1 = eyes[0]; eye_2 = eyes[1]
        
        if eye_1[0] < eye_2[0]:
            left_eye = eye_1
            right_eye = eye_2
        else:
            left_eye = eye_2
            right_eye = eye_1
        
        #--------------------
        #center of eyes
        
        left_eye_center = (int(left_eye[0] + (left_eye[2] / 2)), int(left_eye[1] + (left_eye[3] / 2)))
        left_eye_x = left_eye_center[0]; left_eye_y = left_eye_center[1]
        
        right_eye_center = (int(right_eye[0] + (right_eye[2]/2)), int(right_eye[1] + (right_eye[3]/2)))
        right_eye_x = right_eye_center[0]; right_eye_y = right_eye_center[1]
        
        #center_of_eyes = (int((left_eye_x+right_eye_x)/2), int((left_eye_y+right_eye_y)/2))
        
        cv2.circle(img, left_eye_center, 2, (255, 0, 0) , 2)
        cv2.circle(img, right_eye_center, 2, (255, 0, 0) , 2)
        
        #find rotation direction
        
        if left_eye_y > right_eye_y:
            point_3rd = (right_eye_x, left_eye_y)
            direction = -1 #rotate same direction to clock
            print("rotate to clock direction")
        else:
            point_3rd = (left_eye_x, right_eye_y)
            direction = 1 #rotate inverse direction of clock
            print("rotate to inverse clock direction")
    
        cv2.circle(img, point_3rd, 2, (255, 0, 0) , 2)
        
        cv2.line(img,right_eye_center, left_eye_center,(67,67,67),1)
        cv2.line(img,left_eye_center, point_3rd,(67,67,67),1)
        cv2.line(img,right_eye_center, point_3rd,(67,67,67),1)
        
        a = euclidean_distance(left_eye_center, point_3rd)
        b = euclidean_distance(right_eye_center, point_3rd)
        c = euclidean_distance(right_eye_center, left_eye_center)

        cos_a = (b*b + c*c - a*a)/(2*b*c)
       
        angle = np.arccos(cos_a)
       
        angle = (angle * 180) / math.pi
        print("angle: ", angle," in degree")
        
        if direction == -1:
            angle = 90 - angle
        
        print("angle: ", angle," in degree")
        
        new_img = Image.fromarray(img_raw)
        new_img = np.array(new_img.rotate(direction * angle))
        return new_img
    if new_img is None:
        return img_raw

    return new_img
    

def detect_face(image,is_aligned,img_raw):
    
    frame=image.copy()
    (h, w) = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 1.0,
        (100, 100), (104.0, 177.0, 123.0))
    
    
    net.setInput(blob)
    
    detections = net.forward()
    
    confidence = detections[0, 0, 0, 2]
    
    if confidence < 0.5:
        return False
    
    
    box = detections[0, 0, 0, 3:7] * np.array([w, h, w, h])
    
    (startX, startY, endX, endY) = box.astype("int")
    (startX, startY) = (max(0, startX), max(0, startY))
    (endX, endY) = (min(w - 1, endX), min(h - 1, endY))
    face = frame[startY:endY, startX:endX]
    
    if is_aligned is True:
        return face
    else:
        print("re 9")
        aligned_image=align_face(img_raw)
        return aligned_image
    
    #face = cv2.resize(face, (224, 224)) 

def turn_rgb(images):
    b, g, r = tf.split(images, 3, axis=-1)
    images = tf.concat([r, g, b], -1)

    return images

def resize_face(face):
    face = tf.image.resize(face, (112, 112), method="nearest")

    return (tf.cast(face, tf.float32) - 127.5) / 128.

def get_output(images):
	return tf.nn.l2_normalize(model(images, training=False))

def recognize_face(path,face_list):
    count=0
    face=cv2.imread(path)
    
    new_face = cv2.cvtColor(face, cv2.COLOR_BGR2RGB)
    
    new_face = tf.convert_to_tensor([resize_face(face)])
    
    output1 = get_output(new_face)[0]
    
    status=-1
    for saved_face in face_list:
        
        resp = urllib.request.urlopen(saved_face)
        
        image = np.asarray(bytearray(resp.read()), dtype="uint8")
        
        image = cv2.imdecode(image, cv2.IMREAD_COLOR)
     
        new_face = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
      
        new_face = tf.convert_to_tensor([resize_face(new_face)])
       
        output2 = get_output(new_face)[0]
        
        dist = cos_dis(output1, output2)
     
        
        if dist < 1.1:
            status=count
            break
        
        count=count+1
    return status

