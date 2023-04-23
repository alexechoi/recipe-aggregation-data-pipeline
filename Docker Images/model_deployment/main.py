import joblib
from flask import Flask, request, jsonify
import logging
from flask_cors import CORS, cross_origin
from google.cloud import storage
import io

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Function to load a model from a GCS bucket
def load_model_from_gcs(bucket_name, model_path):
    storage_client = storage.Client.create_anonymous_client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(model_path)
    model_data = blob.download_as_bytes()
    model = joblib.load(io.BytesIO(model_data))
    return model

def remove_negative_predictions(predictions):
    return [max(0, prediction) for prediction in predictions]

bucket_name = 'data-engineering-recipe-serving'
linear_regression_model_path = 'models/linear_regression_model.pkl'
random_forest_model_path = 'models/random_forest_model.pkl'

linear_regression_model = load_model_from_gcs(bucket_name, linear_regression_model_path)
random_forest_model = load_model_from_gcs(bucket_name, random_forest_model_path)

@app.route('/predict_linear_regression', methods=['POST'])
@cross_origin()
def predict_linear_regression():
    try:
        data = request.get_json()
        input_features = [data['input_features']]
        prediction = linear_regression_model.predict(input_features)
        prediction = remove_negative_predictions(prediction)
        return jsonify(prediction.tolist())
    except Exception as e:
        logging.exception("Error occurred during prediction")
        return str(e), 500

@app.route('/predict_random_forest', methods=['POST'])
@cross_origin()
def predict_random_forest():
    data = request.get_json()
    input_features = [data['input_features']]
    prediction = random_forest_model.predict(input_features)
    return jsonify(prediction.tolist())

logging.basicConfig(level=logging.DEBUG)
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
