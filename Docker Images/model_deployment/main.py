import joblib
from flask import Flask, request, jsonify
import logging
from flask_cors import CORS, cross_origin

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

linear_regression_model = joblib.load('linear_regression_model.pkl')
random_forest_model = joblib.load('random_forest_model.pkl')

@app.route('/predict_linear_regression', methods=['POST'])
@cross_origin()
def predict_linear_regression():
    try:
        data = request.get_json()
        input_features = [data['input_features']]
        prediction = linear_regression_model.predict(input_features)
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
