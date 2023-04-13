import json
import mysql.connector
import pymysql
from google.cloud import storage
import re
import datetime

def create_mysql_connection():
    connection = pymysql.connect(
        host="HOST_NAME",
        user="USER",
        password="PASSWORD",
        database="DB"
    )
    return connection

def parse_ingredient(ingredient_str):
    # Example implementation; adjust regex based on the ingredient string format.
    match = re.match(r'(?P<quantity>[\d/]+)?\s*(?P<unit>\w+)?\s*(?P<name>.+)', ingredient_str)

    if match:
        return match.group('name').strip(), match.group('quantity'), match.group('unit')
    else:
        return ingredient_str.strip(), None, None

# Transform SimplyRecipes
def transform_simplyrecipes_json(recipe_json):
    transformed_recipe = {
        "title": recipe_json["title"],
        "instructions": " ".join(recipe_json["instructions"]),
        "ingredients": [{"name": ingredient} for ingredient in recipe_json["ingredients"]],
        "category": recipe_json.get("category", None),
        "cuisine": recipe_json.get("cuisine", None),
        "cook_time_minutes": recipe_json.get("cook_time_minutes", None),
        "total_time_minutes": recipe_json.get("total_time_minutes", None),
        "yields": recipe_json.get("yields", None),
        "created_at": recipe_json.get("created_at", None),
        "updated_at": recipe_json.get("updated_at", None)
    }

    return transformed_recipe

def transform_simplyrecipes_data(recipe_data):
    return [transform_simplyrecipes_json(recipe) for recipe in recipe_data]

def transform_edamam_data(response):
    transformed_data = []
    recipe_data = response

    for recipe in recipe_data:
        if not isinstance(recipe, dict):
            print(f"Unexpected data type: {type(recipe)}, value: {recipe}")
            continue

        try:
            nutrients = recipe.get("totalNutrients", {})

            # Check if nutrient values are negative or None, and set to 0 if they are
            def check_nutrient_value(value):
                if value is None or value < 0:
                    return 0
                return value

            nutrition = {
                "calories": check_nutrient_value(round(recipe.get("calories", 0))),
                "protein": check_nutrient_value(round(nutrients.get("PROCNT", {}).get("quantity", 0))) if "PROCNT" in nutrients else 0,
                "fat": check_nutrient_value(round(nutrients.get("FAT", {}).get("quantity", 0))) if "FAT" in nutrients else 0,
                "carbohydrates": check_nutrient_value(round(nutrients.get("CHOCDF", {}).get("quantity", 0))) if "CHOCDF" in nutrients else 0,
                "sugar": check_nutrient_value(round(nutrients.get("SUGAR", {}).get("quantity", 0))) if "SUGAR" in nutrients else 0,
                "fiber": check_nutrient_value(round(nutrients.get("FIBTG", {}).get("quantity", 0))) if "FIBTG" in nutrients else 0,
                "cholesterol": check_nutrient_value(round(nutrients.get("CHOLE", {}).get("quantity", 0))) if "CHOLE" in nutrients else 0,
                "sodium": check_nutrient_value(round(nutrients.get("NA", {}).get("quantity", 0))) if "NA" in nutrients else 0
            }

            # Check if the title, source_url, or image_url are empty or None, and set to an empty string if they are
            title = recipe.get("label", "")
            source_url = recipe.get("url", "")
            image_url = recipe.get("image", "")

            if not title or not source_url or not image_url:
                print(f"Skipping recipe with missing data: title={title}, source_url={source_url}, image_url={image_url}")
                continue

            transformed_item = {
                "title": title,
                "source_url": source_url,
                "image_url": image_url,
                "instructions": "",
                "ingredients": [{"name": ing} for ing in recipe.get("ingredientLines", [])],
                "nutrition": nutrition,
                "category": recipe.get("dishType", [])[0] if "dishType" in recipe and recipe["dishType"] else None,
                "cuisine": recipe.get("cuisineType", [])[0] if "cuisineType" in recipe and recipe["cuisineType"] else None,
                "cook_time_minutes": None,  # not available in the JSON
                "total_time_minutes": recipe.get("totalTime", None),
                "yields": recipe.get("yield", None),
                "created_at": None,  # not available in the JSON
                "updated_at": None  # not available in the JSON
            }

            transformed_data.append(transformed_item)
        except Exception as e:
            print(f"Error while processing recipe:{recipe}, Exception: {e}")
            continue

    return transformed_data


# Transform Tasty

def transform_tastyapi_data(raw_data):
    transformed_data = []

    for item in raw_data:
        try:
            instructions = item.get("instructions", [])
            nutrition = item.get("nutrition", {})
            ingredients = []
            for section in item.get("sections", []):
                for component in section.get("components", []):
                    ingredients.append(component["ingredient"]["name"])

            transformed_recipe = {
                "title": item.get("name"),
                "image_url": item.get("thumbnail_url"),
                "source_url": item.get("url"),
                "instructions": " ".join(instruction["display_text"] for instruction in instructions),
                "ingredients": ingredients,
                "nutrition": {
                    "calories": nutrition.get("calories"),
                    "protein": nutrition.get("protein"),
                    "fat": nutrition.get("fat"),
                    "carbohydrates": nutrition.get("carbohydrates"),
                    "sugar": nutrition.get("sugar"),
                    "fiber": nutrition.get("fiber"),
                    "cholesterol": nutrition.get("cholesterol"),
                    "sodium": nutrition.get("sodium")
                },
                "category": item.get("category", None),
                "cuisine": item.get("cuisine", None),
                "cook_time_minutes": item.get("cook_time_minutes", None),
                "total_time_minutes": item.get("total_time_minutes", None),
                "yields": item.get("yields", None),
                "created_at": item.get("created_at", None),
                "updated_at": item.get("updated_at", None)
            }

            transformed_data.append(transformed_recipe)
        except Exception as e:
            print(f"Error processing item: {item}")
            print(f"Error message: {str(e)}")

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
            "category": item.get("strCategory", None),
            "cuisine": item.get("strArea", None),
            "cook_time_minutes": item.get("cook_time_minutes", None),
            "total_time_minutes": item.get("total_time_minutes", None),
            "yields": item.get("yields", None),
            "created_at": item.get("created_at", None),
            "updated_at": item.get("updated_at", None)
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

def insert_recipe(title, instructions, image_url=None, source_url=None, category='', cuisine='', cook_time_minutes=0, total_time_minutes=0, yields=1, created_at=None, updated_at=None):
    connection = create_mysql_connection()
    recipe_id = None
    
    # Truncate the image_url value if it's too long
    if image_url and len(image_url) > 255:
        image_url = image_url[:255]

    # Set default values for created_at and updated_at if not provided
    if created_at is None:
        created_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    if updated_at is None:
        updated_at = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    try:
        with connection.cursor() as cursor:
            sql_query = """
            INSERT INTO recipe (
                title, instructions, source_url, image_url, category, cuisine,
                cook_time_minutes, total_time_minutes, yields, created_at, updated_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
            """

            cursor.execute(sql_query, (
                title,
                instructions,
                source_url,
                image_url,
                category,
                cuisine,
                cook_time_minutes,
                total_time_minutes,
                yields,
                created_at,
                updated_at
            ))
            recipe_id = cursor.lastrowid
        connection.commit()
    finally:
        connection.close()

    return recipe_id


def insert_ingredients(recipe_id, ingredients):
    connection = create_mysql_connection()

    try:
        with connection.cursor() as cursor:
            for ingredient in ingredients:
                sql_query = """
                INSERT INTO recipe_ingredient (recipe_id, ingredient_id, quantity, unit)
                VALUES (%s, %s, %s, %s);
                """

                cursor.execute(sql_query, (
                    recipe_id,
                    ingredient_id,
                    ingredient.get("quantity", None),
                    ingredient.get("unit", None)
                ))
        connection.commit()
    finally:
        connection.close()

def insert_recipe_ingredient(recipe_id, name, quantity, unit):
    connection = create_mysql_connection()

    try:
        with connection.cursor() as cursor:
            # First, insert the ingredient if it doesn't already exist
            sql_query = """
            INSERT INTO ingredient (name) VALUES (%s)
            ON DUPLICATE KEY UPDATE id=LAST_INSERT_ID(id);
            """

            cursor.execute(sql_query, (name,))
            ingredient_id = cursor.lastrowid

            # Then, insert the association between the recipe and the ingredient
            sql_query = """
            INSERT INTO recipe_ingredient (recipe_id, ingredient_id, quantity, unit)
            VALUES (%s, %s, %s, %s);
            """

            cursor.execute(sql_query, (recipe_id, ingredient_id, quantity, unit))
        
        connection.commit()
    finally:
        connection.close()

        
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

# Simply Recipes

def insert_simplyrecipes_data(transformed_data):
    for recipe in transformed_data:

        recipe_id = insert_recipe(
            recipe["title"],
            recipe["instructions"],
            recipe.get("image_url", None),
            recipe.get("source_url", None),
            recipe.get("category", None),
            recipe.get("cuisine", None),
            recipe.get("cook_time_minutes", None),
            recipe.get("total_time_minutes", None),
            recipe.get("yields", None),
            recipe.get("created_at", None),
            recipe.get("updated_at", None)
        )

        for ingredient in recipe["ingredients"]:
            name, quantity, unit = parse_ingredient(ingredient["name"])
            insert_recipe_ingredient(recipe_id, name, quantity, unit)

        insert_instructions(recipe["instructions"], recipe_id)
        
        nutrition_data = recipe.get("nutrition", None)
        if nutrition_data is not None:
            insert_nutrition(nutrition_data, recipe_id)

# Edamam

def insert_edamam_data(transformed_data):
    for recipe in transformed_data:
        recipe_id = insert_recipe(
            recipe["title"],
            recipe["instructions"],
            recipe.get("image_url", None),
            recipe.get("url", None),  # source_url
            recipe.get("category", None),  # category
            recipe.get("cuisine", None),  # cuisine
            recipe.get("cook_time_minutes", None),  # cook_time_minutes
            recipe.get("total_time_minutes", None),  # total_time_minutes
            recipe.get("yields", None)  # yields
        )

        for ingredient in recipe["ingredients"]:
            name, quantity, unit = parse_ingredient(ingredient["name"])
            insert_recipe_ingredient(recipe_id, name, quantity, unit)

        insert_instructions(recipe["instructions"], recipe_id)
        insert_nutrition(recipe["nutrition"], recipe_id)

# TastyAPI

def insert_tastyapi_data(transformed_data):
    for recipe in transformed_data:
        recipe_id = insert_recipe(
            recipe["title"],
            recipe["instructions"],
            recipe.get("image_url", None),
            recipe.get("source_url", None),  # source_url
            recipe.get("category", None),  # category
            recipe.get("cuisine", None),  # cuisine
            recipe.get("cook_time_minutes", None),
            recipe.get("total_time_minutes", None),
            recipe.get("servings", None)  # yields
        )

        for ingredient_name in recipe["ingredients"]:
            name, quantity, unit = parse_ingredient(ingredient_name)
            insert_recipe_ingredient(recipe_id, name, quantity, unit)

        insert_instructions(recipe["instructions"], recipe_id)
        insert_nutrition(recipe["nutrition"], recipe_id)

# TheMealDB

def insert_themealdb_data(transformed_data):
    for recipe in transformed_data:
        recipe_id = insert_recipe(
            recipe["title"],
            recipe["instructions"],
            recipe.get("image_url", None),
            recipe.get("source", None),  # source_url
            recipe.get("category", None),
            recipe.get("cuisine", None),  # cuisine
            recipe.get("cook_time_minutes", None),  # cook_time_minutes
            recipe.get("total_time_minutes", None),  # total_time_minutes
            recipe.get("yields", None)  # yields
        )

        for ingredient in recipe["ingredients"]:
            name, quantity, unit = parse_ingredient(ingredient["name"])
            insert_recipe_ingredient(recipe_id, name, quantity, unit)

        insert_instructions(recipe["instructions"], recipe_id)

        if "nutrition" in recipe:
            insert_nutrition(recipe["nutrition"], recipe_id)

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
            try:
                insert_fn(transformed_data)
                print(f"{filename} data processed.")
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    process_data("edamam-output.json", transform_edamam_data, insert_edamam_data)
    process_data("simplyrecipes-output.json", transform_simplyrecipes_data, insert_simplyrecipes_data)
    process_data("tasty-output.json", transform_tastyapi_data, insert_tastyapi_data)
    process_data("themealdb-output.json", transform_themealdb_data, insert_themealdb_data)

    # Return a response to indicate success
    return "Data inserted successfully"




