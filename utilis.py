import numpy as np
import tensorflow as tf 
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model

corn_model = tf.keras.models.load_model(
    "models/effecientnetb0_tuned_corn.h5",
    compile=False,
)
grape_model = tf.keras.models.load_model(
    "models/efficientnetb0_grape.h5",
    compile=False,
    )

corn_classes = {
    0: "Cercospora_Leaf_Spot",
    1: "Common_Rust",
    2: "Northern_Leaf_BlightHealthy_Corn",
    3: "Healthy_Corn"
}

grape_classes = {
    0: "Black_Rot",
    1: "Esca",
    2: "Leaf_Blight",
    3: "Healthy_Grape"
}


def preprocess_image(img):
    img = img.resize((224,224))
    img = np.expand_dims(img, axis=0)
    return img


def predict_corn(img):
    img = preprocess_image(img)
    pred = corn_model.predict(img)
    class_idx = np.argmax(pred)
    confidence = float(np.max(pred))
    return corn_classes[class_idx],confidence
    

def predict_grape(img):
    img = preprocess_image(img)
    pred = grape_model.predict(img)
    class_idx = np.argmax(pred)
    confidence = float(np.max(pred))
    return grape_classes[class_idx],confidence
