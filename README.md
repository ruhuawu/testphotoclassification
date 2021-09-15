# testphotoclassification

This app will allow user to check their photo for road conditions. the app support image upload, and it 
applies ML model to detect if there is any potholes in the uploaded image, if pothole is detected, it will be marked with red bucket


to run in local:

1.have python 3.6

2.pip install -r requirements.txt

3.pip install -r pothole/requirements.txt

4.install tensorflow if not yet following here:
  
  1)git clone https://github.com/tensorflow/models.git
  
  2)ls

  3)cd models/research/

  4)protoc object_detection/protos/*.proto --python_out=.

  5)cp object_detection/packages/tf2/setup.py .

  6)python -m pip install .

5.run python application.py to start the app
