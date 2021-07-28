import os
from threading import Thread
from flask import Flask, request, redirect, url_for, send_from_directory, render_template
from keras.preprocessing.image import ImageDataGenerator, load_img, img_to_array
from keras.models import Sequential, load_model
from werkzeug.utils import secure_filename
import numpy as np
from keras.applications.vgg16 import VGG16, decode_predictions
import uuid
from cassandraCluster import cassandraCluster as dbcluster
import json

ALLOWED_EXTENSIONS = set(['jpg', 'jpeg', 'png'])
IMAGE_SIZE = (224, 224)
UPLOAD_FOLDER = 'uploads'
vgg16 = VGG16(weights='imagenet')
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


def predict(file):  
    img  = load_img(file, target_size=IMAGE_SIZE)
    img = img_to_array(img)/255.0
    img = np.expand_dims(img, axis=0)
    preds = vgg16.predict(img)
    vgg16.predict(img)
    probs = decode_predictions(preds, top=3)[0]
    return probs

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def savePatholeInfoInCassandra(pathole): 
    db = dbcluster(app)
    session = db.connection.connect()
    id = uuid.uuid1()
    params = [id, "lonitude", "latitude" ,"imagepath"]   
    session.execute("INSERT INTO images.pathole (patholeid, longitude, latitude, imagepath) VALUES (%s,%s,%s,%s)", params)                 

def saveImageInLocal(pathole):
    filename = secure_filename(pathole.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    pathole.save(file_path)
    return file_path
    
@app.route("/")
def template_test():
    return render_template('home.html', label='', imagesource='file://null')

@app.route('/', methods=['POST'])
def predict_pathole_from_app():
    file = request.files['file'] 
    file_path = saveImageInLocal(file)
    print(file_path)
    probs = predict(file)
    output = {probs[0][1]:probs[0][2]}
    return render_template("home.html", label=output, imagesource=file_path)
    
@app.route('/predict', methods=['POST'])
def predict_pathole_from_api():
    file = request.files['file']             
    probs = predict(file)
    if probs[0][2] >0 :
       savePatholeInfoInCassandra(file)
       print(json.dumps(str(probs[0])))
    return json.dumps(str(probs[0]))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

if __name__ == "__main__":
    app.run(debug=False, threaded=False)
