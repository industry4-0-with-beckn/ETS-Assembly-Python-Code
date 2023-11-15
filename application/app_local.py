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

# Target location to the east of the user
target_lat = 30.876877
target_lon = 73.868969 + 0.035  # Adjusted longitude to be approximately 2.5 miles east
response_data = 0
template_data = 0

# Define the request headers
headers = {
    "Content-Type": "application/json",
}

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search', methods=['POST'])
def search():
    request_data = request.get_json()
    radius_val = request_data['message']['intent']['provider']['locations'][0]['circle']['radius']['value']
    print("The requested filter distance is: ", radius_val)
    file_path = os.path.join(os.path.dirname(__file__), 'response', 'response.search.ets.json')
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
    fulfillments = [
        {"id": "f1", "type": "Delivery", "tracking": False},
        {"id": "f2", "type": "Self-Pickup", "tracking": False}
    ]    
    # Send the GraphQL request
    response = requests.post(graph_url, json=data, headers=headers)
    # Initialize an empty list to store providers
    providers_list = []
    response_data = response.json()
    if int(radius_val) >= 3:
        # Loop through each provider in the GraphQL response
        for provider_data in response_data["data"]["providers"]["data"]:
            # Extract provider attributes
            provider_attributes = provider_data["attributes"]
            # Extract category data
            category_ids = provider_attributes["category_ids"]["data"]
            categories_list = [
                {
                    "id": category["id"],
                    "descriptor": {
                        "code": category["attributes"]["category_code"],
                        "name": category["attributes"]["value"]
                    }
                }
                for category in category_ids
            ]

            # Extract location data
            location_data = provider_attributes["location_id"]["data"]["attributes"]
            location_country = location_data["country"]
            location_state = location_data["state"]
            location_city = location_data["city"]

            # Extract logo data
            logo_data = provider_attributes["logo"]["data"]["attributes"]
            logo_id = provider_attributes["logo"]["data"]["id"]
            logo_url = logo_data["url"]

            # Extract other provider attributes
            domain_id = provider_attributes["domain_id"]["data"]["attributes"]["DomainName"]
            provider_id = provider_attributes["provider_id"]
            provider_name = provider_attributes["provider_name"]
            provider_uri = provider_attributes["provider_uri"]
            short_desc = provider_attributes["short_desc"]
            long_desc = provider_attributes["long_desc"]
            # Call the function to update tags and price
            tags, price = update_tags_and_price(provider_name)
            # Extract item data
            items_data = provider_attributes["items"]["data"]
            items_list = [
                {
                    "id": item["id"],
                    "descriptor": {
                        "images": [{"url": item["attributes"]["image"]["data"][0]["attributes"]["url"]}],
                        "name": item["attributes"]["name"]
                    }, 
                    "tags": tags,
                    "price":price               
                }
                for item in items_data
            ] 
       
            # Construct the provider object
            provider_obj = {
                "id": logo_id,
                "descriptor": {
                    "images": [{"url": logo_url}],
                    "name": provider_name,
                    "short_desc": short_desc,
                    "long_desc": long_desc
                },
                "categories": categories_list,
                "items": items_list,
                "fulfillments": fulfillments
                # Add other provider attributes as needed
            }
            # Append the provider to the list
            providers_list.append(provider_obj)
        # Update template_data with the providers list
        template_data['context']['domain'] = domain_id
        template_data['context']['bpp_id'] = provider_id
        template_data['context']['bpp_uri'] = provider_uri
        template_data['context']['country'] = location_country
        template_data['message']['catalog']['descriptor']['name'] = 'Assembly Service'
        template_data['message']['catalog']['providers'] = providers_list
        return jsonify(template_data)
    else:
        return jsonify({'Not ok': True})

def update_tags_and_price(provider_name):
    tags = []
    price = {}

    if provider_name == "ETS-Assembly":
        tags = [
            {
                "descriptor": {
                    "code": "product-info",
                    "name": "Product Information"
                },
                "list": [
                    {
                        "descriptor": {
                            "name": "product-type"
                        },
                        "value": "Steel container Box Assembly"
                    }
                ],
                "display": True
            },
            # Add other tags as needed
        ]
        price = {
            "currency": "EUR",
            "value": "starting from 100 EUR"
        }
    elif provider_name == "Roggendorf Assmebly":
        tags = [
            {
                "descriptor": {
                    "code": "product-info",
                    "name": "Product Information"
                },
                "list": [
                    {
                        "descriptor": {
                            "name": "product-type"
                        },
                        "value": "Cardboard Box Assembly"
                    }
                ],
                "display": True
            },
            # Add other tags as needed
        ]
        price = {
            "currency": "EUR",
            "value": "starting from 25 EUR"
        }
    elif provider_name == "ABS-Assembly":
        tags = [
            {
                "descriptor": {
                    "code": "product-info",
                    "name": "Product Information"
                },
                "list": [
                    {
                        "descriptor": {
                            "name": "product-type"
                        },
                        "value": "Brake System Assembly"
                    }
                ],
                "display": True
            },
            # Add other tags as needed
        ]
        price = {
            "currency": "EUR",
            "value": "starting from 580 EUR"
        }

    return tags, price

@app.route('/select', methods=['POST'])
def select():

    file_path = os.path.join(os.path.dirname(__file__), 'response', 'response.select.json')
    with open(file_path, 'r') as json_file:
        response_data = json.load(json_file)
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True)
