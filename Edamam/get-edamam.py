import requests
import json
import os
import random
import string

APP_ID = "***REMOVED***"  # Replace this with your actual App ID
APP_KEY = "***REMOVED***"  # Replace this with your actual App Key
BASE_URL = "https://api.edamam.com/search"

def get_recipes_by_random_character():
    random_character = random.choice(string.ascii_lowercase)
    querystring = {"q": random_character, "app_id": APP_ID, "app_key": APP_KEY}
    response = requests.get(BASE_URL, params=querystring)

    if response.status_code == 200:
        return response.json()
    else:
        print("Error: Unable to fetch recipes. Status code:", response.status_code)
        return None

def save_to_json_file(data, file_path):
    file_exists = os.path.isfile(file_path)

    with open(file_path, "a" if file_exists else "w") as f:
        if file_exists:
            f.write(",\n")
        json.dump(data, f, indent=2)

def edamam_retrieve():
    if __name__ == "__main__":
    output_dir = "../output"
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, "edamam-output.json")

    recipes = get_recipes_by_random_character()
    
    if recipes:
        save_to_json_file(recipes, output_file)
        print("Recipes saved to:", output_file)
    else:
        print("No recipes found.")
