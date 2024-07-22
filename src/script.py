# Python script that scrapes recipe data from www.allrecipes.com. The script is intended to be run as an AWS Lambda function.

from bs4 import BeautifulSoup
import requests
import json
class Scraper:
    def __init__(self, url):
        self.url = url
    """
    helper method that parses for the details including time information and servings. returns
    a dictionary with keys like "prep time, cook time, total time, servings" and the associated values
    """
    def getTime(self, content):

        details_div = content.find("div", class_="mm-recipes-details")
        details_label = details_div.find_all("div", class_="mm-recipes-details__label")
        details_value = details_div.find_all("div", class_="mm-recipes-details__value")
        time_details = {}
        for idx in range(len(details_label)):
            time_details[details_label[idx].text.lower()[:-1]] = details_value[idx].text
        return time_details

    def getThumbnail(self, content):
        img_divs = content.find_all('div', class_='img-placeholder')
        for div in img_divs:
            images = div.find_all('img')
            for image in images:
                cur_url = image.get('data-src')
                size = image.get("width")
                if cur_url and size and int(size) > 200:
                    # print(cur_url, size)
                    return cur_url
        # returns thumbnail from the webpage (biggest image of the recipe)     
    def getDirections(self, content):
        """
        returns a list of directions for this recipe
        """
        directions = []
        directions_paragraphs = content.find_all("p", class_="comp mntl-sc-block mntl-sc-block-html")
        for step in directions_paragraphs:
            if step.text:
                directions.append(step.text.strip())
        return "".join(directions)
    """
    returns a list of ingredients for this recipe
    """
    def getIngredients(self, content):
        result = []
        list_items = content.find_all("li", class_="mm-recipes-structured-ingredients__list-item")
        for item in list_items:
            if item.text:
                result.append(item.text.strip())            
        return result

    def scrape_page(self):
        recipe = {}
        response = requests.get(self.url)
        soup = BeautifulSoup(response.text, 'html.parser')
        # Scrape the page here
        title = soup.find('h1', class_='article-heading').text
        recipe["title"] = title
        # lets extract a dictionary of the recipe with keys like "title, ingredients, instructions, prep time, cook time, total time, servings, calories, rating, reviews"
        # also lets extract two image urls, both of the recipe
        content = soup.find('div', class_='article-content')
        img_url = self.getThumbnail(content)
        recipe["thumbnail"] = img_url
        
        time_details = self.getTime(content)
        for k,v in time_details.items():
            recipe[k] = v
        
        ingredients = self.getIngredients(content)
        recipe["ingredients"] = ingredients # ingredients is comma seperated list

        directions = self.getDirections(content)
        recipe["directions"] = directions
        return recipe

def is_valid_recipe(recipe):
    # check if the recipe has all the critical details
    # critical details are thumbnail, title, ingredients, directions, prep time or cook time or total time, servings
    if not recipe.get("thumbnail"):
        print("No thumbnail")
        return False
    elif not recipe.get("title"):
        print("No title")
        return False
    elif not recipe.get("ingredients"): 
        print("no ingredients")
        return False
    elif not recipe.get("directions"):
        print("no directions")
        return False
    time_details = ["prep time", "cook time", "total time"]
    for time in time_details:
        if recipe.get(time):
            print("\nrecipe dictionary is valid\n")
            return True # only need one of these time details for the recipe to be valid
    print("error validating recipe")
    return False

def lambda_handler(event, context):
    url = event["queryStringParameters"]["parameter1"] 
    scraper = Scraper(url)
    recipe_data = scraper.scrape_page() # should give back dictionary with relevant recipe details
    # critical details are thumbnail, title, ingredients, directions, prep time or cook time or total time, servings
    if is_valid_recipe(recipe_data):
        data = recipe_data
    else:
        data = {"error": "error getting recipe data"}
    return {
        'statusCode': 200,
        'body': json.dumps('Hello from Lambda!'),
        "param1": url,
        "data": data
    }
