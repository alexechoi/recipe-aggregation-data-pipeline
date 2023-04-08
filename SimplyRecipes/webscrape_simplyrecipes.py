import requests
from bs4 import BeautifulSoup
import json
import os

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

def get_recipe_data(root_url, limit=2):
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

        output_path = '../output/simplyrecipes.json'

        # Check if the output directory exists, if not create it
        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Check if the output file exists
        if os.path.isfile(output_path):
            # If it exists, read the existing data
            with open(output_path, 'r') as f:
                existing_data = json.load(f)
        else:
            # If it doesn't exist, create an empty list for the existing data
            existing_data = []

        # Append the new recipes to the existing data
        existing_data.extend(recipes)

        # Write the updated data back to the output file
        with open(output_path, 'w') as f:
            json.dump(existing_data, f, indent=2)

        return "Recipe data has been successfully saved"

    except Exception as e:
        raise e
