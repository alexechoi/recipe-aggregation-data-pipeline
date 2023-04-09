import requests
import json
import os

API_KEY = "1"
BASE_URL = "https://www.themealdb.com/api/json/v1/{}/".format(API_KEY)

def get_random_recipe():
    random_url = "{}random.php".format(BASE_URL)
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
    output_dir = "../output"
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
    if __name__ == "__main__":
        for _ in range(number_of_recipes): # call the function a specified number of times to get multiple recipes
            get_mealdb()