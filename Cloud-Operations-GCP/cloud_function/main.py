import json
import mysql.connector
import pymysql
from google.cloud import storage

# Transform SimplyRecipes
def transform_simplyrecipes_json(recipe_json):
    transformed_recipe = {
        "title": recipe_json["title"],
        "instructions": " ".join(recipe_json["instructions"]),
        "ingredients": [{"name": ingredient} for ingredient in recipe_json["ingredients"]]
    }
    return transformed_recipe

def transform_simplyrecipes_data(recipe_data):
    return [transform_simplyrecipes_json(recipe) for recipe in recipe_data]

# Transform Edamam
def transform_edamam_data(raw_data):
    transformed_data = []

    for recipe in raw_data:
        nutrients = recipe["totalNutrients"]

        nutrition = {
            "calories": round(recipe["calories"]),
            "protein": round(nutrients["PROCNT"]["quantity"]) if "PROCNT" in nutrients else None,
            "fat": round(nutrients["FAT"]["quantity"]) if "FAT" in nutrients else None,
            "carbohydrates": round(nutrients["CHOCDF"]["quantity"]) if "CHOCDF" in nutrients else None,
            "sugar": round(nutrients["SUGAR"]["quantity"]) if "SUGAR" in nutrients else None,
            "fiber": round(nutrients["FIBTG"]["quantity"]) if "FIBTG" in nutrients else None,
            "cholesterol": round(nutrients["CHOLE"]["quantity"]) if "CHOLE" in nutrients else None,
            "sodium": round(nutrients["NA"]["quantity"]) if "NA" in nutrients else None
        }

        transformed_item = {
            "title": recipe["label"],
            "source_url": recipe["url"],
            "image_url": recipe["image"],
            "instructions": "",
            "ingredients": [{"name": ing} for ing in recipe["ingredientLines"]],
            "nutrition": nutrition,
        }

        transformed_data.append(transformed_item)

    return transformed_data

# Transform Tasty

def transform_tastyapi_data(raw_data):
    transformed_data = []

    for item in raw_data:
        transformed_recipe = {
            "title": item["name"],
            "image_url": item["thumbnail_url"],
        }

        if "instructions" in item:
            transformed_recipe["instructions"] = "\n".join([instruction["display_text"] for instruction in item["instructions"]])

        if "sections" in item:
            transformed_recipe["ingredients"] = [{"name": ing["raw_text"]} for section in item["sections"] for ing in section["components"]]

        if "nutrition" in item:
            transformed_recipe["nutrition"] = {
                "calories": item["nutrition"].get("calories", None),
                "protein": item["nutrition"].get("protein", None),
                "fat": item["nutrition"].get("fat", None),
                "carbohydrates": item["nutrition"].get("carbohydrates", None),
                "sugar": item["nutrition"].get("sugar", None),
                "fiber": item["nutrition"].get("fiber", None),
            }

        transformed_data.append(transformed_recipe)

    return transformed_data

# Transform TheMealDB

def transform_themealdb_data(raw_data):
    transformed_data = []

    for item in raw_data:
        transformed_recipe = {
            "title": item["strMeal"],
            "image_url": item["strMealThumb"],
            "instructions": item["strInstructions"].replace("\r\n", "\n"),
            "ingredients": [],
        }

        for i in range(1, 21):
            ingredient_key = f"strIngredient{i}"
            measure_key = f"strMeasure{i}"

            if item[ingredient_key] and item[ingredient_key].strip():
                transformed_recipe["ingredients"].append({
                    "name": item[ingredient_key].strip(),
                    "quantity": item[measure_key].strip() if item[measure_key] and item[measure_key].strip() else None
                })

        transformed_data.append(transformed_recipe)

    return transformed_data

# Insert data

def create_mysql_connection():
    connection = pymysql.connect(
        host="104.196.180.64",
        user="root",
        password="***REMOVED***",
        database="main"
    )
    return connection

# Simply Recipes

def insert_simplyrecipes_data(recipe_data):
    for recipe in recipe_data:
        # Insert recipe and get recipe_id
        recipe_id = insert_recipe(recipe)

        # Insert instructions
        insert_instructions(recipe["instructions"], recipe_id)

        # Insert ingredients
        ingredient_ids = insert_ingredients(recipe["ingredients"])

        # Insert recipe_ingredient
        insert_recipe_ingredients(recipe_id, ingredient_ids, recipe["ingredients"])

def insert_recipe(recipe_data):
    connection = create_mysql_connection()
    recipe_id = None

    try:
        with connection.cursor() as cursor:
            sql_query = """
            INSERT INTO recipe (title, instructions)
            VALUES (%s, %s);
            """

            cursor.execute(sql_query, (recipe_data.get("title", None), recipe_data.get("instructions", None)))
            recipe_id = cursor.lastrowid
        connection.commit()
    finally:
        connection.close()

    return recipe_id

def insert_ingredients(ingredients):
    connection = create_mysql_connection()
    ingredient_ids = []

    try:
        with connection.cursor() as cursor:
            for ingredient in ingredients:
                sql_query = """
                INSERT INTO ingredient (name)
                VALUES (%s);
                """

                cursor.execute(sql_query, (ingredient.get("name", None),))
                ingredient_ids.append(cursor.lastrowid)
        connection.commit()
    finally:
        connection.close()

    return ingredient_ids

def insert_instructions(instructions, recipe_id):
    connection = create_mysql_connection()

    try:
        with connection.cursor() as cursor:
            for position, instruction in enumerate(instructions.split('\n')):
                sql_query = """
                INSERT INTO instruction (recipe_id, position, text)
                VALUES (%s, %s, %s);
                """

                cursor.execute(sql_query, (recipe_id, position, instruction.strip() if instruction else None))
        connection.commit()
    finally:
        connection.close()

def insert_recipe_ingredients(recipe_id, ingredient_ids, ingredients):
    connection = create_mysql_connection()

    try:
        with connection.cursor() as cursor:
            for ingredient_id, ingredient in zip(ingredient_ids, ingredients):
                sql_query = """
                INSERT INTO recipe_ingredient (recipe_id, ingredient_id, quantity, unit)
                VALUES (%s, %s, %s, %s);
                """

                cursor.execute(sql_query, (recipe_id, ingredient_id, ingredient.get("quantity", None), ingredient.get("unit", None)))
        connection.commit()
    finally:
        connection.close()
        
def insert_nutrition(nutrition_data, recipe_id):
    connection = create_mysql_connection()

    try:
        with connection.cursor() as cursor:
            sql_query = """
            INSERT INTO nutrition (
                recipe_id, calories, protein, fat, carbohydrates, sugar, fiber, cholesterol, sodium
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
            """

            cursor.execute(sql_query, (
                recipe_id,
                nutrition_data.get("calories", None),
                nutrition_data.get("protein", None),
                nutrition_data.get("fat", None),
                nutrition_data.get("carbohydrates", None),
                nutrition_data.get("sugar", None),
                nutrition_data.get("fiber", None),
                nutrition_data.get("cholesterol", None),
                nutrition_data.get("sodium", None)
            ))
        connection.commit()
    finally:
        connection.close()

# Edamam

def insert_edamam_data(recipe_data):
    for recipe in recipe_data:
        # Insert recipe and get recipe_id
        recipe_id = insert_recipe(recipe)

        # Insert instructions
        if "instructions" in recipe:
            insert_instructions(recipe["instructions"], recipe_id)

        # Insert ingredients
        ingredient_ids = insert_ingredients(recipe["ingredients"])

        # Insert recipe_ingredient
        insert_recipe_ingredients(recipe_id, ingredient_ids, recipe["ingredients"])

        # Insert nutrition data
        if "nutrition" in recipe:
            insert_nutrition(recipe["nutrition"], recipe_id)

# TastyAPI

def insert_tastyapi_data(recipe_data):
    for recipe in recipe_data:
        # Insert recipe and get recipe_id
        recipe_id = insert_recipe(recipe)

        # Insert instructions
        if "instructions" in recipe:
            insert_instructions(recipe["instructions"], recipe_id)

        # Insert ingredients
        if "ingredients" in recipe:
            ingredient_ids = insert_ingredients(recipe["ingredients"])

            # Insert recipe_ingredient
            insert_recipe_ingredients(recipe_id, ingredient_ids, recipe["ingredients"])

        # Insert nutrition data
        if "nutrition" in recipe:
            insert_nutrition(recipe["nutrition"], recipe_id)

# TheMealDB

def insert_themealdb_data(recipe_data):
    for recipe in recipe_data:
        # Insert recipe and get recipe_id
        recipe_id = insert_recipe(recipe)

        # Insert instructions
        if "instructions" in recipe:
            insert_instructions(recipe["instructions"], recipe_id)

        # Insert ingredients
        ingredient_ids = insert_ingredients(recipe["ingredients"])

        # Insert recipe_ingredient
        insert_recipe_ingredients(recipe_id, ingredient_ids, recipe["ingredients"])

def main(request):
    bucket_name = "achoi-data-eng-bucket"
    storage_client = storage.Client.from_service_account_json("keyfile.json")
    bucket = storage_client.get_bucket(bucket_name)

    # Read the JSON files from the Google Cloud Storage bucket
    def load_json_file(filename):
        try:
            blob = bucket.blob(filename)
            file_contents = blob.download_as_text()
            return json.loads(file_contents)
        except Exception as e:
            print(f"Error loading {filename}: {e}")
            return None

    def process_data(filename, transform_fn, insert_fn):
        data = load_json_file(filename)
        if data:
            transformed_data = transform_fn(data)
            insert_fn(transformed_data)

    process_data("edamam-output.json", transform_edamam_data, insert_edamam_data)
    process_data("simplyrecipes-output.json", transform_simplyrecipes_data, insert_simplyrecipes_data)
    process_data("tasty-output.json", transform_tastyapi_data, insert_tastyapi_data)
    process_data("themealdb-output.json", transform_themealdb_data, insert_themealdb_data)

    # Return a response to indicate success
    return "Data inserted successfully"


