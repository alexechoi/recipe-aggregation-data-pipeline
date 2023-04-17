import os
import requests
import json
import random
import string
from bs4 import BeautifulSoup
from google.cloud import storage
from flask import jsonify

E_APP_ID = "CREDENTIAL"  # EDAMAM
E_APP_KEY = "CREDENTIAL"
E_BASE_URL = "https://api.edamam.com/search"

R_API_KEY = "CREDENTIAL"
R_BASE_URL = "https://tasty.p.rapidapi.com/recipes/list"

M_API_KEY = "CREDENTIAL"
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

def save_to_json_file_edamam(data):
    recipes = data.get("hits", [])
    flattened_recipes = []
    for recipe in recipes:
        flattened_recipe = recipe["recipe"].copy()
        flattened_recipe["ingredients"] = recipe["recipe"]["ingredientLines"]
        flattened_recipes.append(flattened_recipe)

    return flattened_recipes

def edamam_retrieve():
    recipes = get_recipes_by_random_character()

    if recipes:
        # Save the recipes to a JSON file and get the modified data
        modified_recipes = save_to_json_file_edamam(recipes)

        # Save the modified data to the bucket
        bucket_name = "BUCKET_NAME"  # Replace with your bucket name
        destination_blob_name = "edamam-output.json"
        save_to_bucket(modified_recipes, bucket_name, destination_blob_name)
    else:
        print("No recipes found.")
        
# SimplyRecipes

# Add prerequisite functions
# Extract Ingredients
def extract_ingredients(ingredients_section):
    if ingredients_section is None:
        return None

    ingredients_list = ingredients_section.find_all(class_="structured-ingredients__list-item")
    ingredients = []

    for ingredient in ingredients_list:
        ingredients.append(ingredient.get_text().strip())

    return ingredients

# Extract instructions
def extract_instructions(instructions_section):
    if instructions_section is None:
        return None

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

def save_to_json_file_tasty(data):
    recipes = data.get("results", [])
    return recipes

def get_tasty():
    recipes = get_recipes()

    if recipes:
        # Save the recipes to a JSON file and get the modified data
        modified_recipes = save_to_json_file_tasty(recipes)

        # Save the modified data to the bucket
        bucket_name = "BUCKET_NAME"  # Replace with your bucket name
        destination_blob_name = "tasty-output.json"
        save_to_bucket(modified_recipes, bucket_name, destination_blob_name)
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

def save_to_json_file_themealdb(data):
    meals = data.get("meals", [])
    return meals

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
        modified_recipes = save_to_json_file_themealdb(random_recipe)
        bucket_name = "BUCKET_NAME"  # Replace with your bucket name
        destination_blob_name = "themealdb-output.json"
        save_to_bucket(modified_recipes, bucket_name, destination_blob_name)
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