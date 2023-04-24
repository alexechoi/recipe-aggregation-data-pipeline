import requests
import json
import os
import random
import string

API_KEY = "c95b8b6459msheafd8f7c7d4aafdp19ce79jsn3bb738211983"  # Replace this with your actual API key
BASE_URL = "https://tasty.p.rapidapi.com/recipes/list"

headers = {
    "X-RapidAPI-Key": API_KEY,
    "X-RapidAPI-Host": "tasty.p.rapidapi.com"
}

def get_recipes():
    querystring = {"from": "0", "size": "20", "tags": "under_30_minutes"}
    response = requests.get(BASE_URL, headers=headers, params=querystring)

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
    if __name__ == "__main__":
    output_dir = "../output"
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, "tasty-output.json")

    recipes = get_recipes()
    
    if recipes:
        save_to_json_file(recipes, output_file)
        print("Recipes saved to:", output_file)
    else:
        print("No recipes found.")