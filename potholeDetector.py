import os
import pathlib
import numpy as np
import tensorflow as tf
from PIL import Image
from six import BytesIO
from object_detection.utils import config_util
from object_detection.builders import model_builder
from object_detection.utils import label_map_util
from object_detection.utils import visualization_utils as viz_utils
import matplotlib
import matplotlib.pyplot as plt


def prepare_files_for_model(modeName):

  filenames = list(pathlib.Path('models/'+modeName+'/').glob('*.index'))

  filenames.sort()
  #recover our saved model
  pipeline_config = 'models/'+modeName+'/mobilenet_v2.config'
  #generally you want to put the last ckpt from training in here
  # model_dir = str(filenames[-1]).replace('.index','')
  configs = config_util.get_configs_from_pipeline_file(pipeline_config)
  model_config = configs['model']
  global detection_model 
  detection_model = model_builder.build(
      model_config=model_config, is_training=False)

  # Restore checkpoint
  ckpt = tf.compat.v2.train.Checkpoint(
      model=detection_model)
  ckpt.restore(os.path.join(str(filenames[-1]).replace('.index','')))

  label_map_path =  'models/'+modeName+'/label_map.pbtxt' #configs['eval_input_config'].label_map_path
  label_map = label_map_util.load_labelmap(label_map_path)
  categories = label_map_util.convert_label_map_to_categories(
    label_map,
    max_num_classes=label_map_util.get_max_label_map_index(label_map),
    use_display_name=True)
  global category_index 
  category_index= label_map_util.create_category_index(categories)
 

def get_model_detection_function(model):
  """Get a tf.function for detection."""

  @tf.function
  def detect_fn(image):
    """Detect objects in image."""
    
    image, shapes = model.preprocess(image)
    
    prediction_dict = model.predict(image, shapes)
  
    detections = model.postprocess(prediction_dict, shapes)
 
    return detections

  return detect_fn



def load_image_into_numpy_array(path):
    img_data = tf.io.gfile.GFile(path, 'rb').read()
    image = Image.open(BytesIO(img_data))
    (im_width, im_height) = image.size
    return np.array(image.getdata()).reshape(
    (im_height, im_width, 3)).astype(np.uint8)

def detect(modelName, image_path, file_path, storeimg):
    prepare_files_for_model(modelName)
    detect_fn = get_model_detection_function(detection_model)
    image_np = load_image_into_numpy_array(image_path)
    input_tensor = tf.convert_to_tensor(
    np.expand_dims(image_np, 0), dtype=tf.float32)
    detections = detect_fn(input_tensor)
    if(storeimg):
      label_id_offset = 1
      image_np_with_detections = image_np.copy()

      viz_utils.visualize_boxes_and_labels_on_image_array(
       image_np_with_detections,
       detections['detection_boxes'][0].numpy(),
       (detections['detection_classes'][0].numpy() + label_id_offset).astype(int),
       detections['detection_scores'][0].numpy(),
       category_index,
       use_normalized_coordinates=True,
       max_boxes_to_draw=200,
       min_score_thresh=.5,
       agnostic_mode=False,
      ) 
      plt.figure(figsize=(12,16))
      plt.imshow(image_np_with_detections)
      plt.savefig(file_path) 
    return detections['detection_scores'][0].numpy()

