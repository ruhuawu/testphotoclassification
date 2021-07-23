import os
from flask import Flask, request, redirect, url_for, send_from_directory, render_template
from keras.preprocessing.image import ImageDataGenerator, load_img, img_to_array
from keras.models import Sequential, load_model
from werkzeug.utils import secure_filename
import numpy as np
from keras.applications.vgg16 import VGG16, decode_predictions
from PIL import Image
import uuid
from cassandraCluster import cassandraCluster as dbcluster

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
    output = {probs[0][1]:probs[0][2]}
    return output

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route("/")
def template_test():
    return render_template('home.html', label='', imagesource='file://null')


@app.route('/', methods=['GET', 'POST'])
def upload_file():
    db = dbcluster(app)
    cluster = db.connection
    if request.method == 'POST':
        file = request.files['file']
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            # save the info(image uuid, label/ispathole) in cassandra, for now not saving the image meta data
            b=bytearray([])
            id = uuid.uuid1()
            output = predict(file_path)
            label = list(output.keys())[0]
            params = [id, label, True, b]
            # cluster.connect().execute('CREATE TABLE IF NOT EXISTS images.pathole (image_id uuid PRIMARY KEY, label text, is_pathold boolean, file blob)')
            cluster.connect().execute("INSERT INTO images.pathole (image_id, label, is_pathold, file) VALUES (%s,%s,%s,%s)", params)                 
    return render_template("home.html", label=output, imagesource=file_path)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

if __name__ == "__main__":
    app.run(debug=False, threaded=False)
