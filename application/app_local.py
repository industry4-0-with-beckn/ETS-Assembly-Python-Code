from flask import Flask, render_template, request, url_for, jsonify, Response
from flask import jsonify
import threading
import logging
import datetime
import configparser
import time
import random
import json
import os
import requests
app = Flask(__name__)

# GraphQL endpoint URL
graph_url = "http://localhost:1337/graphql"

# Define the request headers
headers = {
    "Content-Type": "application/json",
}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search():
    file_path = os.path.join(os.path.dirname(__file__), 'response', 'response.search.json')
    with open(file_path, 'r') as json_file:
        template_data = json.load(json_file)
    query_path = os.path.join(os.path.dirname(__file__), 'template', 'assembly-Search.graphql')
    # Read the GraphQL query from the template file
    with open(query_path, 'r') as query_template_file:
        query = query_template_file.read()
    # Create the request payload
    data = {
        "query": query,
    }
    # Initialize variables to store the values
    category_codes = []
    category_id = []
    category_values = []
    item_names = []
    item_image_urls = []
    item_id = [] 
    # Send the GraphQL request
    response = requests.post(graph_url, json=data, headers=headers)

    # Check for a successful response
    if response.status_code == 200:
        # Parse the JSON response
        response_data = response.json()
        # Extract the data you need
        providers_data = response_data["data"]["providers"]["data"]
        for provider in providers_data:
            # Fetching Categories data
            category_ids = provider["attributes"]["category_ids"]["data"]
            for category in category_ids:
                category_id.append(category["id"])
                category_codes.append(category["attributes"]["category_code"])
                category_values.append(category["attributes"]["value"])
            # Fetching items data
            items_data = provider["attributes"]["items"]["data"]
            for item in items_data:
                item_id.append(item["id"])
                item_names.append(item["attributes"]["name"])
                item_image_urls.append(item["attributes"]["image"]["data"][0]["attributes"]["url"])
            # Fetching location data
            location_data = provider["attributes"]["location_id"]["data"]["attributes"]
            location_country = location_data["country"]
            location_state = location_data["state"]
            location_city  = location_data["city"]
            location_zip  = location_data["zip"]
            logo_data = provider["attributes"]["logo"]["data"]["attributes"]
            logo_id = provider["attributes"]["logo"]["data"]["id"]
            logo_url = logo_data["url"]
            domain_id = provider["attributes"]["domain_id"]["data"]["attributes"]["DomainName"]
            provider_id = provider["attributes"]["provider_id"]
            provider_name = provider["attributes"]["provider_name"]
            provider_uri = provider["attributes"]["provider_uri"]
            short_desc = provider["attributes"]["short_desc"]
            long_desc = provider["attributes"]["long_desc"]
        # Updating the response
        template_data['context']['domain'] = domain_id
        template_data['context']['bpp_id'] = provider_id
        template_data['context']['bpp_uri'] = provider_uri
        template_data['context']['country'] = location_country
        template_data['context']['city'] = location_city
        template_data['message']['catalog']['providers'][0]['descriptor']['images'][0]['url'] = logo_url
        template_data['message']['catalog']['providers'][0]['id'] = logo_id
        template_data['message']['catalog']['providers'][0]['descriptor']['name'] = provider_name
        template_data['message']['catalog']['providers'][0]['descriptor']['short_desc'] = short_desc
        template_data['message']['catalog']['providers'][0]['descriptor']['long_desc'] = long_desc
        template_data['message']['catalog']['providers'][0]['items'][0]['id']  = item_id[0]
        template_data['message']['catalog']['providers'][0]['items'][0]['descriptor']['images'][0]['url']  = item_image_urls[0]
        template_data['message']['catalog']['providers'][0]['items'][0]['descriptor']['name']  = item_names[0]
        template_data['message']['catalog']['providers'][0]['categories'] = [
            {
                "id": category_id[0],
                "descriptor": {
                        "code": category_codes[0],
                        "name": category_values[0]
                    }
            },
            {
                "id": category_id[1],
                "descriptor": {
                        "code": category_codes[1],
                        "name": category_values[1]
                    }
            },
            {
                "id": category_id[2],
                "descriptor": {
                        "code": category_codes[2],
                        "name": category_values[2]
                    }
            },
            {
                "id": category_id[3],
                "descriptor": {
                        "code": category_codes[3],
                        "name": category_values[3]
                    }
            }
        ]
        return jsonify(template_data)
    else:
        print("GraphQL request failed with status code:", response.status_code)
        return jsonify({'Not ok': True})


@app.route('/select', methods=['POST'])
def select():

    file_path = os.path.join(os.path.dirname(__file__), 'response', 'response.select.json')
    with open(file_path, 'r') as json_file:
        response_data = json.load(json_file)
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True)
