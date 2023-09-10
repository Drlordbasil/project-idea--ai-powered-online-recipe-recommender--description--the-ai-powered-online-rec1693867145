import requests
from bs4 import BeautifulSoup
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import json


class RecipeScraper:
    def __init__(self):
        self.base_url = "https://www.allrecipes.com"

    def get_recipe_urls(self, num_recipes):
        recipe_urls = []
        page_num = 1
        while len(recipe_urls) < num_recipes:
            url = f"{self.base_url}/recipes/?page={page_num}"
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")
            links = soup.find_all(
                "a", class_="card__titleLink manual-link-behavior")
            recipe_urls.extend([self.base_url + link["href"]
                               for link in links])
            next_button = soup.find("a", class_="card__next")
            if next_button:
                page_num += 1
            else:
                break
        recipe_urls = recipe_urls[:num_recipes]
        return recipe_urls

    def scrape_recipe_data(self, url):
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        title = soup.find("h1", class_="headline").text.strip()
        ingredients = [li.text.strip()
                       for li in soup.find_all("li", class_="ingredients-item")]
        instructions = [li.text.strip()
                        for li in soup.find_all("li", class_="step")]
        rating = float(soup.find("div", class_="rating-stars")
                       ["data-ratingstars"])
        return {
            "title": title,
            "ingredients": ingredients,
            "instructions": instructions,
            "rating": rating
        }


class UserPreferenceAnalyzer:
    def __init__(self):
        self.preference_data = {
            "cuisine_preferences": [],
            "dietary_restrictions": [],
            "ingredient_preferences": []
        }

    def get_user_preferences(self):
        print("Please enter your cuisine preferences (comma-separated): ")
        cuisines = input().strip().split(",")
        self.preference_data["cuisine_preferences"] = [
            cuisine.strip().lower() for cuisine in cuisines]

        print("Please enter your dietary restrictions (comma-separated): ")
        restrictions = input().strip().split(",")
        self.preference_data["dietary_restrictions"] = [
            restriction.strip().lower() for restriction in restrictions]

        print("Please enter your ingredient preferences (comma-separated): ")
        ingredients = input().strip().split(",")
        self.preference_data["ingredient_preferences"] = [
            ingredient.strip().lower() for ingredient in ingredients]

    def analyze_preferences(self, recipe_data):
        analyzed_data = []
        for recipe in recipe_data:
            analyzed_recipe = {
                "title": recipe["title"],
                "ingredients": recipe["ingredients"],
                "instructions": recipe["instructions"],
                "rating": recipe["rating"],
                "match_score": 0
            }
            for cuisine in self.preference_data["cuisine_preferences"]:
                if cuisine in recipe["title"].lower():
                    analyzed_recipe["match_score"] += 1

            for restriction in self.preference_data["dietary_restrictions"]:
                for ingredient in recipe["ingredients"]:
                    if restriction in ingredient.lower():
                        analyzed_recipe["match_score"] += 1

            for preference in self.preference_data["ingredient_preferences"]:
                for ingredient in recipe["ingredients"]:
                    if preference in ingredient.lower():
                        analyzed_recipe["match_score"] += 1

            analyzed_data.append(analyzed_recipe)

        analyzed_data.sort(key=lambda x: (
            x["match_score"], x["rating"]), reverse=True)
        return analyzed_data


class RecipeRecommendationEngine:
    def __init__(self, recipe_data):
        self.recipe_data = recipe_data

    def get_similar_recipes(self, recipe_title):
        tfidf_vectorizer = TfidfVectorizer()
        recipe_titles = [recipe["title"] for recipe in self.recipe_data]
        tfidf_matrix = tfidf_vectorizer.fit_transform(recipe_titles)
        title_index = recipe_titles.index(recipe_title)
        cosine_similarities = cosine_similarity(
            tfidf_matrix[title_index], tfidf_matrix).flatten()
        similar_indices = cosine_similarities.argsort()[::-1][1:4]
        similar_recipes = [self.recipe_data[idx]["title"]
                           for idx in similar_indices]
        return similar_recipes


class NutritionalAnalyzer:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.spoonacular.com/recipes"

    def get_nutritional_info(self, recipe_title):
        response = requests.get(
            f"{self.base_url}/complexSearch?query={recipe_title}&number=1&apiKey={self.api_key}"
        )
        recipe_id = response.json()["results"][0]["id"]
        response = requests.get(
            f"{self.base_url}/{recipe_id}/nutritionWidget.json?apiKey={self.api_key}"
        )
        nutritional_info = response.json()
        return nutritional_info


class UserInterface:
    def __init__(self, recipe_data):
        self.recipe_data = recipe_data

    def show_menu(self):
        print("==== Recipe Recommender ====")
        print("1. Get personalized recipe recommendations")
        print("2. Get similar recipes for a specific recipe")
        print("3. Get nutritional information for a recipe")
        print("4. Exit")

    def get_user_choice(self):
        choice = input("Enter your choice: ")
        return choice

    def get_recommendations(self, analyzer):
        user_preferences = UserPreferenceAnalyzer()
        user_preferences.get_user_preferences()
        analyzed_data = analyzer.analyze_preferences(self.recipe_data)
        print("Recommended Recipes:")
        for recipe in analyzed_data:
            print(f"Title: {recipe['title']}")
            print(f"Ingredients: {', '.join(recipe['ingredients'])}")
            print(f"Instructions: {', '.join(recipe['instructions'])}")
            print(f"Rating: {recipe['rating']}")
            print()

    def get_similar_recipes(self, recommender):
        recipe_title = input("Enter the title of the recipe: ")
        similar_recipes = recommender.get_similar_recipes(recipe_title)
        print("Similar Recipes:")
        for recipe in similar_recipes:
            print(recipe)

    def get_nutritional_info(self, analyzer):
        recipe_title = input("Enter the title of the recipe: ")
        nutritional_info = analyzer.get_nutritional_info(recipe_title)
        print("Nutritional Information:")
        print(json.dumps(nutritional_info, indent=2))


class RecipeRecommender:
    def __init__(self, num_recipes, api_key):
        self.scraper = RecipeScraper()
        self.recipe_data = self.scrape_recipes(num_recipes)
        self.preference_analyzer = UserPreferenceAnalyzer()
        self.recommendation_engine = RecipeRecommendationEngine(
            self.recipe_data)
        self.nutritional_analyzer = NutritionalAnalyzer(api_key)
        self.ui = UserInterface(self.recipe_data)

    def scrape_recipes(self, num_recipes):
        scraper = RecipeScraper()
        recipe_urls = scraper.get_recipe_urls(num_recipes)
        recipe_data = []
        for url in recipe_urls:
            recipe_data.append(scraper.scrape_recipe_data(url))
        return recipe_data

    def run(self):
        while True:
            self.ui.show_menu()
            choice = self.ui.get_user_choice()

            if choice == "1":
                self.ui.get_recommendations(self.preference_analyzer)
            elif choice == "2":
                self.ui.get_similar_recipes(self.recommendation_engine)
            elif choice == "3":
                self.ui.get_nutritional_info(self.nutritional_analyzer)
            elif choice == "4":
                break
            else:
                print("Invalid choice. Please try again.")


def main():
    api_key = "YOUR_SPOONACULAR_API_KEY"
    num_recipes = 100
    recommender = RecipeRecommender(num_recipes, api_key)
    recommender.run()


if __name__ == "__main__":
    main()
