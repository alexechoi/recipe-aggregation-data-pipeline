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
    file_exists = os.path.isfile(file_path)

    with open(file_path, "a" if file_exists else "w") as f:
        if file_exists:
            f.write(",\n")
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    output_dir = "../output"
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, "themealdb-output.json")

    random_recipe = get_random_recipe()
    
    if random_recipe:
        save_to_json_file(random_recipe, output_file)
        print("Random recipe saved to:", output_file)
    else:
        print("No recipe found.")
