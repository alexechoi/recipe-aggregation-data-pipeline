import mysql.connector
from neo4j import GraphDatabase
from tqdm import tqdm
import re
import nltk
import io
from contextlib import redirect_stdout
import sys
nltk.download("omw-1.4")
nltk.download("punkt")
nltk.download("averaged_perceptron_tagger")
nltk.download("stopwords")
nltk.download("wordnet")

from nltk.corpus import stopwords, wordnet
stop_words = set(stopwords.words("english"))

from flask import Flask, jsonify

app = Flask(__name__)

@app.route("/run-script", methods=["POST"])
def run_script_endpoint():
    try:
        f = io.StringIO()
        with redirect_stdout(f):
            run_script()
        output = f.getvalue()
        return jsonify({"message": "Script executed successfully.", "output": output}), 200
    except Exception as e:
        return jsonify({"message": str(e)}), 500

def run_script():
    def clean_ingredient(ingredient):
        # Remove any text within parentheses
        cleaned_ingredient = re.sub(r'\([^)]*\)', '', ingredient)
        
        # Get individual words from the strings
        words = nltk.word_tokenize(cleaned_ingredient)

        # Filter out stopwords
        filtered_words = [word for word in words if word.lower() not in stop_words]

        # Specifically extract nouns
        nouns = [word for word, pos in nltk.pos_tag(filtered_words) if pos in ['NN', 'NNS']]

        # Use WordNet to match nouns to food items
        food_nouns = []
        for noun in nouns:
            synsets = wordnet.synsets(noun, pos=wordnet.NOUN)
            food_related = any("food" in ss.lexname() for ss in synsets)
            if food_related:
                food_nouns.append(noun)
        
        return ' '.join(food_nouns)

    # Connect to the MySQL database
    cnx = mysql.connector.connect(
        host='***REMOVED***',
        user='root',
        password='***REMOVED***',
        database='main'
    )

    print("Connected to MySQL")

    # Neo4j connection
    neo4j_connection = GraphDatabase.driver(
        uri="***REMOVED***",
        auth=("neo4j", "***REMOVED***")
    )

    # Create a Neo4j session
    neo4j_session = neo4j_connection.session()

    print("Connected to Neo4j")

    # Create a cursor to execute MySQL queries
    cursor = cnx.cursor()

    # Fetch recipes with unique titles from the MySQL database

    cursor.execute("""
        SELECT r.title, r.id, r.image_url, r.category, r.cuisine, r.cook_time_minutes, r.total_time_minutes, r.yields, r.created_at, r.updated_at
        FROM (
            SELECT *,
                   RANK() OVER (PARTITION BY title ORDER BY (cuisine IS NOT NULL) DESC, (category IS NOT NULL) DESC) as recipe_rank
            FROM recipe
        ) as r
        WHERE r.recipe_rank = 1
    """)
    recipes = cursor.fetchall()

    # Create a list of recipes for batch insertion
    recipes_list = []
    unique_titles = set()

    for recipe in tqdm(recipes, desc="Creating Recipe Nodes"):
        title, recipe_id, image_url, category, cuisine, cook_time_minutes, total_time_minutes, yields, created_at, updated_at = recipe
        
        # Only append unique recipe titles
        if title not in unique_titles:
            unique_titles.add(title)
            recipes_list.append({"recipe_id": recipe_id, "title": title, "image_url": image_url, "category": category, "cuisine": cuisine, "cook_time_minutes": cook_time_minutes, "total_time_minutes": total_time_minutes, "yields": yields, "created_at": created_at, "updated_at": updated_at})

    # Batch insert recipes
    neo4j_session.run("""
        UNWIND $recipes_list AS recipe
        MERGE (r:Recipe {id: recipe.recipe_id})
        ON CREATE SET r.title = recipe.title, r.RecipeName = recipe.title, r.image_url = recipe.image_url, r.category = recipe.category, r.cuisine = recipe.cuisine, r.cook_time_minutes = recipe.cook_time_minutes, r.total_time_minutes = recipe.total_time_minutes, r.yields = recipe.yields, r.created_at = recipe.created_at, r.updated_at = recipe.updated_at
    """, {"recipes_list": recipes_list})


    print("Recipes batch inserted.")


    # Query to create ingredient nodes and relationships with recipe nodes
    cursor.execute("SELECT recipe_id, ingredient_id, quantity, unit FROM recipe_ingredient")
    recipe_ingredients = cursor.fetchall()

    # Create a list of recipe_ingredients for batch insertion
    recipe_ingredients_list = []
    for recipe_ingredient in tqdm(recipe_ingredients, desc="Creating ingredients list"):
        recipe_id, ingredient_id, quantity, unit = recipe_ingredient
        cursor.execute("SELECT name FROM ingredient WHERE id = %s", (ingredient_id,))
        ingredient_name = cursor.fetchone()[0]
        
        cleaned_ingredient_name = clean_ingredient(ingredient_name)

        recipe_ingredients_list.append({"recipe_id": recipe_id, "ingredient_name": cleaned_ingredient_name, "quantity": quantity, "unit": unit})

    # Batch insert ingredients and relationships
    neo4j_session.run("""
        UNWIND $recipe_ingredients_list AS ri
        MATCH (r:Recipe {id: ri.recipe_id})
        MERGE (i:Ingredient {name: ri.ingredient_name})
        MERGE (r)-[rel:REQUIRES_INGREDIENT]->(i)
        ON CREATE SET rel.quantity = ri.quantity, rel.unit = ri.unit
    """, {"recipe_ingredients_list": recipe_ingredients_list})

    print("Ingredients and relationships batch inserted.")


    # Query to create cuisine nodes and relationships with recipe nodes
    cursor.execute("SELECT DISTINCT cuisine FROM recipe WHERE cuisine IS NOT NULL")
    cuisines = cursor.fetchall()

    # Create a list of cuisines for batch insertion
    cuisines_list = []
    for cuisine in tqdm(cuisines, desc="Creating Cuisine Nodes"):
        (cuisine_name,) = cuisine
        cuisines_list.append({"cuisine_name": cuisine_name})

    # Batch insert cuisines
    neo4j_session.run("""
        UNWIND $cuisines_list AS cuisine
        MERGE (c:Cuisine {name: cuisine.cuisine_name})
    """, {"cuisines_list": cuisines_list})

    print("Cuisines batch inserted.")

    # Query to create category nodes and relationships with recipe nodes
    cursor.execute("SELECT DISTINCT category FROM recipe WHERE category IS NOT NULL")
    categories = cursor.fetchall()

    # Create a list of categories for batch insertion
    categories_list = []
    for category in tqdm(categories, desc="Creating Category Nodes"):
        (category_name,) = category
        categories_list.append({"category_name": category_name})

    # Batch insert categories
    neo4j_session.run("""
        UNWIND $categories_list AS category
        MERGE (c:Category {name: category.category_name})
    """, {"categories_list": categories_list})

    print("Categories batch inserted.")

    neo4j_session.run("""
        UNWIND $recipes_list AS recipe
        MATCH (r:Recipe {id: recipe.recipe_id})
        WHERE recipe.cuisine IS NOT NULL
        MATCH (c:Cuisine {name: recipe.cuisine})
        MERGE (r)-[:BELONGS_TO]->(c)
    """, {"recipes_list": recipes_list})

    print("Cuisine relationships created.")


    neo4j_session.run("""
        UNWIND $recipes_list AS recipe
        MATCH (r:Recipe {id: recipe.recipe_id})
        WHERE recipe.category IS NOT NULL
        MATCH (cat:Category {name: recipe.category})
        MERGE (r)-[:HAS_CATEGORY]->(cat)
    """, {"recipes_list": recipes_list})

    print("Category relationships created.")


    # Fetch nutrition data from MySQL
    cursor.execute("""
        SELECT n.id, n.recipe_id, n.calories, n.protein, n.fat, n.carbohydrates, n.sugar, n.fiber, n.cholesterol, n.sodium, r.title
        FROM nutrition n
        INNER JOIN recipe r ON n.recipe_id = r.id
    """)
    nutrition_data_list = cursor.fetchall()

    # Create a list of nutritions for batch insertion
    nutrition_list = []
    for nutrition_data in tqdm(nutrition_data_list, desc="Creating Nutrition Data Nodes"):
        nutrition_id, recipe_id, calories, protein, fat, carbohydrates, sugar, fiber, cholesterol, sodium, recipe_title = nutrition_data
        nutrition_list.append({"nutrition_id": nutrition_id, "recipe_id": recipe_id, "recipe_title": recipe_title, "calories": calories, "protein": protein, "fat": fat, "carbohydrates": carbohydrates, "sugar": sugar, "fiber": fiber, "cholesterol": cholesterol, "sodium": sodium})
        
    # Batch insert nutrition nodes into the graph database
    neo4j_session.run("""
        UNWIND $nutrition_list AS nutrition
        MERGE (n:Nutrition {id: nutrition.nutrition_id})
        ON CREATE SET n.calories = nutrition.calories, n.protein = nutrition.protein, n.fat = nutrition.fat, n.carbohydrates = nutrition.carbohydrates, n.sugar = nutrition.sugar, n.fiber = nutrition.fiber, n.cholesterol = nutrition.cholesterol, n.sodium = nutrition.sodium
    """, {"nutrition_list": nutrition_list})

    print("Nutrition data batch inserted.")


    # Create relationships between recipe nodes and nutrition nodes
    neo4j_session.run("""
        UNWIND $nutrition_list AS nutrition
        MATCH (r:Recipe {title: nutrition.recipe_title})
        MATCH (n:Nutrition {id: nutrition.nutrition_id})
        MERGE (r)-[:HAS_NUTRITION]->(n)
    """, {"nutrition_list": nutrition_list})

    # Close the Neo4j session
    neo4j_session.close()

    # Close the MySQL cursor and connection
    cursor.close()
    cnx.close()

    print("Nutrition relationships created.")



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
