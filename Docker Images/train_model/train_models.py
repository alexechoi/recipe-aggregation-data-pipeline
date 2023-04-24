import os
import pandas as pd
from neo4j import GraphDatabase
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
import io
import pyarrow as pa
import pyarrow.parquet as pq
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import joblib
from google.cloud import storage
from flask import Flask, request
import logging

# Intialise Flask
app = Flask(__name__)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

@app.route('/train', methods=['POST'])
def train_models():
    # Neo4j connection
    neo4j_connection = GraphDatabase.driver(
        uri="neo4j+s://52fe4988.databases.neo4j.io",
        auth=("neo4j", "xjpTjnzkjRapCy1LbO64Objiic2MBtfbKvHSA88xMM0")
    )

    def upload_to_gcs(local_file, gcs_path):
        blob = bucket.blob(gcs_path)
        blob.upload_from_filename(local_file)

    def fetch_data(tx):
        query = """
        MATCH (r:Recipe)-[:HAS_NUTRITION]->(n:Nutrition)
        RETURN r.total_time_minutes as total_time_minutes,
               n.carbohydrates as carbohydrates, n.sodium as sodium, n.fiber as fiber,
               n.protein as protein, n.fat as fat, n.cholesterol as cholesterol,
               n.calories as calories, n.sugar as sugar
        """
        result = tx.run(query)
        return result.data()
        
    def remove_negative_predictions(predictions):
        return [max(0, prediction) for prediction in predictions]


    with neo4j_connection.session() as session:
        data = session.read_transaction(fetch_data)

    neo4j_connection.close()

    # Convert the data to a pandas DataFrame
    df = pd.DataFrame(data)

    # Drop rows containing missing values
    df.dropna(inplace=True)

    # Prepare the input features (X) and target variable (y) for the first model (Linear Regression)
    X = df[["carbohydrates", "protein", "fat", "calories"]]
    y = df["total_time_minutes"]

    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train the linear regression model
    reg = LinearRegression()
    reg.fit(X_train, y_train)

    # Make predictions and evaluate the model
    y_pred = reg.predict(X_test)
    y_pred = remove_negative_predictions(y_pred)  # Remove negative predictions
    mse = mean_squared_error(y_test, y_pred)

    logging.info(f"Mean Squared Error: {mse}")

    """
    RANDOM FOREST
    """

    # Neo4j connection
    neo4j_connection = GraphDatabase.driver(
        uri="neo4j+s://52fe4988.databases.neo4j.io",
        auth=("neo4j", "xjpTjnzkjRapCy1LbO64Objiic2MBtfbKvHSA88xMM0")
    )

    def fetch_data(tx):
        query = """
        MATCH (r:Recipe)-[:HAS_NUTRITION]->(n:Nutrition)
        RETURN n.carbohydrates as carbohydrates, n.sodium as sodium, n.fiber as fiber,
        n.protein as protein, n.fat as fat, n.cholesterol as cholesterol,
        n.calories as calories, n.sugar as sugar
        """
        result = tx.run(query)
        return result.data()
    
    with neo4j_connection.session() as session:
        data = session.read_transaction(fetch_data)

    neo4j_connection.close()

    # Convert the data to a pandas DataFrame
    df = pd.DataFrame(data)

    # Drop rows containing missing values
    df.dropna(inplace=True)

    # Prepare the input features (X) and target variable (y) for the second model (Random Forest)
    X = df[["carbohydrates", "sodium", "fiber", "protein"]]
    y = df["calories"]

    # Split the data into training and testing sets
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train the Random Forest Regressor model
    rf = RandomForestRegressor(n_estimators=100, random_state=42)
    rf.fit(X_train, y_train)

    # Make predictions and evaluate the model
    y_pred = rf.predict(X_test)
    mse = mean_squared_error(y_test, y_pred)
    mae = mean_absolute_error(y_test, y_pred)
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mse)

    logging.info(f"Mean Squared Error: {mse}")
    logging.info(f"Mean Absolute Error: {mae}")
    logging.info(f"R-squared: {r2}")
    logging.info(f"Root Mean Squared Error: {rmse}")

    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'keyfile.json'

    # Save the models to disk
    joblib.dump(reg, 'linear_regression_model.pkl')
    joblib.dump(rf, 'random_forest_model.pkl')

    # Initialize the Google Cloud Storage client
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'keyfile.json'
    storage_client = storage.Client()
    bucket_name = 'data-engineering-recipe-serving'
    bucket = storage_client.get_bucket(bucket_name)

    # Upload the Linear Regression model
    upload_to_gcs('linear_regression_model.pkl', 'models/linear_regression_model.pkl')

    # Upload the Random Forest Regressor model
    upload_to_gcs('random_forest_model.pkl', 'models/random_forest_model.pkl')

    return("Models uploaded to Google Cloud Storage.")
    
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
