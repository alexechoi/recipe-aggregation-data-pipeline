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

# Neo4j connection
neo4j_connection = GraphDatabase.driver(
    uri="URI",
    auth=("neo4j", "AUTH")
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

with neo4j_connection.session() as session:
    data = session.execute_read(fetch_data)

neo4j_connection.close()

# Convert the data to a pandas DataFrame
df = pd.DataFrame(data)

# Drop rows containing missing values
df.dropna(inplace=True)

# Prepare the input features (X) and target variable (y)
X = df.drop(columns=["total_time_minutes"])
y = df["total_time_minutes"]

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the linear regression model
reg = LinearRegression()
reg.fit(X_train, y_train)

# Make predictions and evaluate the model
y_pred = reg.predict(X_test)
mse = mean_squared_error(y_test, y_pred)

print(f"Mean Squared Error: {mse}")

# Convert cleaned DataFrame to PyArrow table
table = pa.Table.from_pandas(df)

# Write table to Parquet file on disk
pq.write_table(table, 'data.parquet')

# Read table from Parquet file on disk
table = pq.read_table('data.parquet')

# Convert table to pandas DataFrame
df = table.to_pandas()

# Prepare the input features (X) and target variable (y)
X = df.drop(columns=["total_time_minutes"])
y = df["total_time_minutes"]

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the linear regression model
reg = LinearRegression()
reg.fit(X_train, y_train)

# Make predictions and evaluate the model
y_pred = reg.predict(X_test)
mse = mean_squared_error(y_test, y_pred)

print(f"Mean Squared Error: {mse}")

"""
RANDOM FOREST
"""

# Neo4j connection
neo4j_connection = GraphDatabase.driver(
    uri="URI",
    auth=("neo4j", "AUTH")
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
    data = session.execute_read(fetch_data)

neo4j_connection.close()

# Convert the data to a pandas DataFrame
df = pd.DataFrame(data)

# Drop rows containing missing values
df.dropna(inplace=True)

# Save cleaned DataFrame to Parquet file
pq.write_table(pa.Table.from_pandas(df), 'data2.parquet')

# Read the Parquet data into a pandas DataFrame
df = pd.read_parquet('data2.parquet')

# Prepare the input features (X) and target variable (y)
X = df.drop(columns=["calories"])
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

print(f"Mean Squared Error: {mse}")
print(f"Mean Absolute Error: {mae}")
print(f"R-squared: {r2}")
print(f"Root Mean Squared Error: {rmse}")

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

# Upload the Parquet files
upload_to_gcs('data.parquet', 'parquet_files/data.parquet')
upload_to_gcs('data2.parquet', 'parquet_files/data2.parquet')

print("Models and parquet files uploaded to Google Cloud Storage.")