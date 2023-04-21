import os
import mysql.connector
import random
from datetime import datetime, timedelta

"""
Credentials
"""

def get_db_credentials():
    return {
        "host": "HOST_NAME",
        "user": "USER",
        "password": "PASSWORD",
        "database": "DATABASE"
    }

"""
Set augmentations for time data and nutritional data
"""

def augment_time_data(cook_time, total_time):
    # Add a random percentage to the time values
    if cook_time is not None:
        cook_time *= (1 + random.uniform(-0.1, 0.1))
    if total_time is not None:
        total_time *= (1 + random.uniform(-0.1, 0.1))
    return cook_time, total_time

def augment_nutrition(cursor, recipe_id):
    # Fetch nutrition data for the recipe
    cursor.execute("SELECT calories, protein, fat, carbohydrates, sugar, fiber, cholesterol, sodium FROM nutrition WHERE recipe_id = %s", (recipe_id,))
    nutrition = cursor.fetchone()
    if nutrition is not None:
        # Add random percentage to the nutritional values
        augmented_nutrition = [x * (1 + random.uniform(-0.1, 0.1)) if x is not None else None for x in nutrition]

        # Insert the augmented nutrition data
        insert_query = "INSERT INTO nutrition (recipe_id, calories, protein, fat, carbohydrates, sugar, fiber, cholesterol, sodium) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(insert_query, (recipe_id,) + tuple(augmented_nutrition))

"""
Manage and insert
"""

def augment_and_insert_data(cursor, recipe):
    recipe_id, cook_time, total_time = recipe
    augmented_cook_time, augmented_total_time = augment_time_data(cook_time, total_time)

    insert_query = f"""INSERT INTO recipe (title, source_url, image_url, category, cuisine, instructions,
                      cook_time_minutes, total_time_minutes, yields, created_at, updated_at)
                      SELECT title, source_url, image_url, category, cuisine, instructions,
                      %s, %s, yields, created_at, NOW()
                      FROM recipe WHERE id = %s"""
    cursor.execute(insert_query, (augmented_cook_time, augmented_total_time, recipe_id))

def data_augmentation(request):
    try:
        # Connect to the MySQL database
        connection = mysql.connector.connect(**get_db_credentials())
        cursor = connection.cursor(buffered=True)

        # Fetch recipes from the database
        cursor.execute("SELECT id, cook_time_minutes, total_time_minutes FROM recipe LIMIT 1000") # Limit number fetched to improve serverless processing time
        recipes = cursor.fetchall()

        # Augment the data and insert it back into the database
        for recipe in recipes:
            if random.random() < 0.2:  # Augment 20%
                augment_and_insert_data(cursor, recipe)
                augment_nutrition(cursor, recipe[0])
            else:
                insert_query = "UPDATE recipe SET updated_at = NOW() WHERE id = %s"
                cursor.execute(insert_query, (recipe[0],))

        # Commit the changes and close the database connection
        connection.commit()
        cursor.close()
        connection.close()

        return 'Data augmentation completed successfully', 200

    except Exception as e:
        return str(e), 500
