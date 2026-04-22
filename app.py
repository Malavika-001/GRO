from flask import Flask, request, jsonify, render_template
import tensorflow as tf
from keras.layers import TFSMLayer
from keras.models import Sequential
import numpy as np
from tensorflow.keras.preprocessing import image
import os

# -----------------------
# Flask App
# -----------------------
app = Flask(__name__)

# -----------------------
# Load Model
# -----------------------
# NEW ✅
saved_model_layer = TFSMLayer(
    "model/gro_model_v6_savedmodel",
    call_endpoint="serving_default"
)

model = Sequential([saved_model_layer])

# -----------------------
# Class Names
# -----------------------
class_names = [
'Apple___Apple_scab','Apple___Cedar_apple_rust','Apple___Healthy',
'Corn___Common_rust','Corn___Gray_leaf_spot','Corn___Healthy','Corn___Northern_Leaf_Blight',
'Grape___Black_rot','Grape___Esca','Grape___Healthy','Grape___Leaf_blight',
'Pepper_bell___Bacterial_spot','Pepper_bell___Healthy',
'Potato___Early_blight','Potato___Healthy','Potato___Late_blight',
'Strawberry___Healthy','Strawberry___Leaf_scorch',
'Tomato___Bacterial_spot','Tomato___Early_blight','Tomato___Healthy',
'Tomato___Late_blight','Tomato___Leaf_mold','Tomato___Septoria_leaf_spot',
'Tomato___Spider_mites','Tomato___Target_spot',
'Tomato___Tomato_mosaic_virus','Tomato___Yellow_Leaf_Curl_Virus',
'not_leaf'
]

# -----------------------
# Treatment Data
# -----------------------
treatment_data = {
"Apple___Apple_scab":{"treatment":"Apply sulfur or copper-based fungicides.","prevention":"Remove infected leaves and ensure good airflow."},
"Apple___Cedar_apple_rust":{"treatment":"Apply myclobutanil fungicide during early infection.","prevention":"Remove nearby cedar hosts."},
"Apple___Healthy":{"treatment":"No treatment required.","prevention":"Maintain proper pruning."},

"Corn___Common_rust":{"treatment":"Apply triazole fungicide.","prevention":"Use rust-resistant hybrids."},
"Corn___Gray_leaf_spot":{"treatment":"Apply foliar fungicide.","prevention":"Practice crop rotation."},
"Corn___Healthy":{"treatment":"No treatment required.","prevention":"Maintain soil fertility."},
"Corn___Northern_Leaf_Blight":{"treatment":"Apply fungicide if severe.","prevention":"Use resistant varieties."},

"Grape___Black_rot":{"treatment":"Apply myclobutanil.","prevention":"Remove infected berries."},
"Grape___Esca":{"treatment":"Prune infected wood.","prevention":"Disinfect tools."},
"Grape___Healthy":{"treatment":"No treatment required.","prevention":"Ensure vine airflow."},
"Grape___Leaf_blight":{"treatment":"Apply copper fungicide.","prevention":"Improve airflow."},

"Pepper_bell___Bacterial_spot":{"treatment":"Apply copper bactericide.","prevention":"Avoid overhead irrigation."},
"Pepper_bell___Healthy":{"treatment":"No treatment required.","prevention":"Maintain irrigation."},

"Potato___Early_blight":{"treatment":"Apply chlorothalonil.","prevention":"Rotate crops."},
"Potato___Healthy":{"treatment":"No treatment required.","prevention":"Use certified seeds."},
"Potato___Late_blight":{"treatment":"Apply systemic fungicide.","prevention":"Ensure drainage."},

"Strawberry___Healthy":{"treatment":"No treatment required.","prevention":"Maintain soil drainage."},
"Strawberry___Leaf_scorch":{"treatment":"Remove infected leaves.","prevention":"Improve air circulation."},

"Tomato___Bacterial_spot":{"treatment":"Apply copper bactericide.","prevention":"Use certified seeds."},
"Tomato___Early_blight":{"treatment":"Apply chlorothalonil.","prevention":"Rotate crops."},
"Tomato___Healthy":{"treatment":"No treatment required.","prevention":"Maintain irrigation."},
"Tomato___Late_blight":{"treatment":"Apply systemic fungicide.","prevention":"Avoid humid conditions."},
"Tomato___Leaf_mold":{"treatment":"Apply fungicide.","prevention":"Reduce humidity."},
"Tomato___Septoria_leaf_spot":{"treatment":"Apply mancozeb.","prevention":"Remove infected leaves."},
"Tomato___Spider_mites":{"treatment":"Apply miticide.","prevention":"Maintain humidity."},
"Tomato___Target_spot":{"treatment":"Apply fungicide.","prevention":"Remove debris."},
"Tomato___Tomato_mosaic_virus":{"treatment":"Remove infected plants.","prevention":"Disinfect tools."},
"Tomato___Yellow_Leaf_Curl_Virus":{"treatment":"Control whiteflies.","prevention":"Use resistant varieties."},

"not_leaf":{"treatment":"Upload a clear leaf image.","prevention":"Ensure the image contains only a leaf."}
}

# -----------------------
# Routes
# -----------------------

# ---------------- Home Page ----------------

@app.route("/")
def home():
    return render_template("home.html")


# ---------------- Detection Page ----------------

@app.route("/detect")
def detect():
    return render_template("detect.html")


# ---------------- Crops Page ----------------

@app.route("/crops")
def crops():
    return render_template("crops.html")


@app.route("/predict", methods=["POST"])
def predict():
    try:

        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"})

        file = request.files['file']
        filepath = "temp.jpg"
        file.save(filepath)

        # -------- Image Load (IMPORTANT FIX) --------
        img = image.load_img(filepath, target_size=(224,224), color_mode="rgb")

        # -------- Blur Check --------
        width, height = img.size
        if width < 150 or height < 150:
            os.remove(filepath)
            return jsonify({
                "prediction": "Image Too Blurry",
                "confidence": 0,
                "treatment": "Please upload a clearer image.",
                "prevention": "Ensure the leaf is clearly visible."
            })

        # -------- Preprocessing (CRITICAL FIX) --------
        img_array = image.img_to_array(img) / 255.0
        img_array = np.expand_dims(img_array, axis=0)

        # -------- Prediction --------
        outputs = model(img_array)

        if isinstance(outputs, dict):
            prediction = list(outputs.values())[0].numpy()
        else:
            prediction = outputs.numpy()

        probs = prediction[0]
        predicted_index = np.argmax(probs)
        predicted_class = class_names[predicted_index]
        confidence = float(probs[predicted_index])

        print("CLASS:", predicted_class)
        print("CONFIDENCE:", confidence)

        os.remove(filepath)

        # -------- Not Leaf --------
        if predicted_class == "not_leaf":
            return jsonify({
                "prediction": "Not a Leaf",
                "confidence": confidence,
                "treatment": "The uploaded image is not a plant leaf.",
                "prevention": "Upload a clear leaf image."
            })

        # -------- Unsupported Crop --------
        if predicted_class == "unsupported_leaf":
            return jsonify({
                "prediction": "Unsupported Crop",
                "confidence": confidence,
                "treatment": "This crop is not supported by GRO.",
                "prevention": "Supported crops: Apple, Corn, Grape, Pepper, Potato, Strawberry, Tomato."
            })

        # -------- Low Confidence Guard --------
        if confidence < 0.55:
            return jsonify({
                "prediction": "Low Confidence",
                "confidence": confidence,
                "treatment": "Model is unsure. Try a clearer image.",
                "prevention": "Use proper lighting and focus."
            })

        # -------- Normal Result --------
        solution = treatment_data.get(predicted_class, {
            "treatment": "No data available.",
            "prevention": "No data available."
        })

        return jsonify({
            "prediction": predicted_class,
            "confidence": confidence,
            "treatment": solution["treatment"],
            "prevention": solution["prevention"]
        })

    except Exception as e:
        print("ERROR:", e)
        return jsonify({
            "error": "Prediction failed"
        })

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)