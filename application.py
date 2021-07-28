import os
from flask import Flask, request,  send_from_directory, render_template
import uuid
from cassandraCluster import cassandraCluster as dbcluster
import json
import potholeDetector as detector

UPLOAD_FOLDER = 'uploads'

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def savePatholeInfoInCassandra(file_path): 
    db = dbcluster(app)
    session = db.connection.connect()
    id = uuid.uuid1()
    params = [id, "longitude", "latitude" ,file_path]   
    session.execute("INSERT INTO images.pathole (patholeid, longitude, latitude, imagepath) VALUES (%s,%s,%s,%s)", params)                 

def saveImageInLocal(pathole):
    filename = pathole.filename
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
    detector.detectPathole(file_path, file_path, True)
    return render_template("home.html", imagesource=file_path)
    
@app.route('/predict', methods=['POST'])
def predict_pathole_from_api():
    file = request.files['file']  
    file_path = saveImageInLocal(file)                    
    probs = detector.detectPathole(file_path, file_path, False)  
    if(probs[0] >= 0.5):
        savePatholeInfoInCassandra(file_path)
    return json.dumps(str(probs))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'],
                               filename)

if __name__ == "__main__":
    app.run(debug=False, threaded=False)
