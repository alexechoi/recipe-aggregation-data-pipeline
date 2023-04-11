import os
import requests
import json
import random
import string
from bs4 import BeautifulSoup
from google.cloud import storage
from flask import jsonify

E_APP_ID = "E_APP_ID"  # EDAMAM
E_APP_KEY = "E_APP_KEY"
E_BASE_URL = "E_BASE_URL"

R_API_KEY = "R_API_KEY"
R_BASE_URL = "R_BASE_URL"

M_API_KEY = "M_API_KEY "
M_BASE_URL = "https://www.themealdb.com/api/json/v1/{}/".format(M_API_KEY)

# Save to Bucket

def save_to_bucket(json_data, bucket_name, destination_blob_name):
    storage_client = storage.Client()
    bucket = storage_client.get_bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_string(json.dumps(json_data, indent=2))
    print(f"Data saved to {destination_blob_name} in bucket {bucket_name}.")

#Edamam

def get_recipes_by_random_character():
    random_character = random.choice(string.ascii_lowercase)
    querystring = {"q": random_character, "app_id": E_APP_ID, "app_key": E_APP_KEY}
    response = requests.get(E_BASE_URL, params=querystring)

    if response.status_code == 200:
        return response.json()
    else:
        print("Error: Unable to fetch recipes. Status code:", response.status_code)
        return None

def save_to_json_file(data, file_path):
    file_exists = os.path.isfile(file_path)

    recipes = data.get("hits", [])
    flattened_recipes = []
    for recipe in recipes:
        flattened_recipe = recipe["recipe"].copy()
        flattened_recipe["ingredients"] = recipe["recipe"]["ingredientLines"]
        flattened_recipes.append(flattened_recipe)

    with open(file_path, "a" if file_exists else "w") as f:
        if file_exists:
            f.write(",\n")
        json.dump(flattened_recipes, f, indent=2)


def edamam_retrieve():
    recipes = get_recipes_by_random_character()

    if recipes:
        bucket_name = "BUCKET_NAME"  # Replace with your bucket name
        destination_blob_name = "edamam-output.json"
        save_to_bucket(recipes, bucket_name, destination_blob_name)
    else:
        print("No recipes found.")
        
# SimplyRecipes

# Add prerequisite functions
# Extract Ingredients
def extract_ingredients(ingredients_section):
    ingredients_list = ingredients_section.find_all(class_="structured-ingredients__list-item")
    ingredients = []

    for ingredient in ingredients_list:
        ingredients.append(ingredient.get_text().strip())

    return ingredients

# Extract instructions
def extract_instructions(instructions_section):
    instructions_list = instructions_section.find_all(class_="comp mntl-sc-block-group--LI mntl-sc-block mntl-sc-block-startgroup")
    instructions = []

    for instruction in instructions_list:
        instructions.append(instruction.get_text().strip())

    return instructions

def get_recipe_data(root_url, limit=1):
    try:
        # Fetch and parse the main page content
        response = requests.get(root_url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the first `limit` recipe cards
        recipe_cards = soup.find_all(class_="comp mntl-card-list-items mntl-document-card mntl-card card", limit=limit)

        recipes = []

        # Iterate through recipe cards
        for card in recipe_cards:
            # Fetch and parse the recipe page content
            recipe_url = card['href']
            recipe_response = requests.get(recipe_url)
            recipe_soup = BeautifulSoup(recipe_response.text, 'html.parser')

            # Extract recipe information
            title = recipe_soup.find('h1').get_text().strip()
            ingredients_section = recipe_soup.find(class_="comp section--ingredients section")
            instructions_section = recipe_soup.find(class_="comp section--instructions section")

            ingredients = extract_ingredients(ingredients_section)
            instructions = extract_instructions(instructions_section)

            # Store the recipe information in a dictionary
            recipe = {
                'title': title,
                'ingredients': ingredients,
                'instructions': instructions
            }

            recipes.append(recipe)

        if recipes:
            bucket_name = "BUCKET_NAME"  # Replace with your bucket name
            destination_blob_name = "simplyrecipes-output.json"
            save_to_bucket(recipes, bucket_name, destination_blob_name)

        return "Recipe data has been successfully saved"

    except Exception as e:
        raise e


# Tasty

headers = {
    "X-RapidAPI-Key": R_API_KEY,
    "X-RapidAPI-Host": "tasty.p.rapidapi.com"
}

def get_recipes():
    querystring = {"from": "0", "size": "20", "tags": "under_30_minutes"}
    response = requests.get(R_BASE_URL, headers=headers, params=querystring)

    if response.status_code == 200:
        return response.json()
    else:
        print("Error: Unable to fetch recipes. Status code:", response.status_code)
        return None

def save_to_json_file(data, file_path):
    file_exists = os.path.isfile(file_path)
    
    recipes = data.get("results", [])

    with open(file_path, "a" if file_exists else "w") as f:
        if file_exists:
            f.write(",\n")
        json.dump(recipes, f, indent=2)


def get_tasty():
    recipes = get_recipes()

    if recipes:
        bucket_name = "BUCKET_NAME"  # Replace with your bucket name
        destination_blob_name = "tasty-output.json"
        save_to_bucket(recipes, bucket_name, destination_blob_name)
    else:
        print("No recipes found.")

# MealDB

def get_random_recipe():
    random_url = "{}random.php".format(M_BASE_URL)
    response = requests.get(random_url)

    if response.status_code == 200:
        return response.json()
    else:
        print("Error: Unable to fetch recipes. Status code:", response.status_code)
        return None

def save_to_json_file(data, file_path):
    meals = data.get("meals", [])

    if os.path.exists(file_path):
        with open(file_path, 'r') as f:
            try:
                existing_data = json.load(f)
            except json.decoder.JSONDecodeError:
                existing_data = []
    else:
        existing_data = []

    existing_data.extend(meals)

    with open(file_path, "w") as f:
        json.dump(existing_data, f, indent=2)

def get_mealdb():
    output_dir = "./"
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, "themealdb-output.json")

    random_recipe = get_random_recipe()

    if random_recipe:
        save_to_json_file(random_recipe, output_file)
        print("Random recipe saved to:", output_file)
    else:
        print("No recipe found.")

# FUNCTION TO CALL:

def meal_db_get_reciples(number_of_recipes):
    random_recipe = get_random_recipe()

    if random_recipe:
        bucket_name = "BUCKET_NAME"  # Replace with your bucket name
        destination_blob_name = "themealdb-output.json"
        save_to_bucket(random_recipe, bucket_name, destination_blob_name)
    else:
        print("No recipe found.")
            
# Google Cloud Function entry point
def collection(event, context=None):
    edamam_retrieve()
    get_recipe_data("https://www.simplyrecipes.com/recipes-5090746", limit=1)
    get_tasty()
    meal_db_get_reciples(1)

    # Return a success message upon completion
    return jsonify({"message": "Recipe data has been successfully collected and saved."})