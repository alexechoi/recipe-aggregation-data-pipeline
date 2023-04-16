FROM python:3.8-slim

WORKDIR /app

# Install the necessary dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the saved models
COPY linear_regression_model.pkl /app/linear_regression_model.pkl
COPY random_forest_model.pkl /app/random_forest_model.pkl

# Copy the prediction script
COPY main.py /app/main.py

EXPOSE 8080

CMD ["python", "main.py"]
