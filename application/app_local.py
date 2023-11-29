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
from math import radians, sin, cos, sqrt, atan2
app = Flask(__name__)

# GraphQL endpoint URL
graph_url = "http://localhost:1337/graphql"

response_data = 0
template_data = 0

# Define the request headers
headers = {
    "Content-Type": "application/json",
}

assembly_keywords = {
    'assembly': 'all',
    'assembly service': 'all',
    'assembly services': 'all',
    'ets': 'ETS-Assembly',
    'ets assembly': 'ETS-Assembly',
    'steel': 'ETS-Assembly',
    'steel assembly': 'ETS-Assembly',
    'outbox': 'Outbox-Assembly',
    'outbox assembly': 'Outbox-Assembly',
    'box assembly': 'Outbox-Assembly',
    'cardboard assembly': 'Outbox-Assembly',
    'abs': 'ABS-Assembly',
    'abs assembly': 'ABS-Assembly',
    'brake': 'ABS-Assembly',
    'brake assembly': 'ABS-Assembly',
    'brake system assembly': 'ABS-Assembly',
    'wirth': 'Wirth-Werkzeugbau',
    'wirth-werkzeugbau': 'Wirth-Werkzeugbau',
    'car assembly': 'Wirth-Werkzeugbau',
    'car engine assembly': 'Wirth-Werkzeugbau',
    'automotive assembly': 'Wirth-Werkzeugbau',
    'circuit': 'PCBA-Assembly',
    'circuit board': 'PCBA-Assembly',
    'circuit board assembly': 'PCBA-Assembly',
    'furniture': 'Zapf-umzüge',
    'furniture assembly': 'Zapf-umzüge',
    'kitchen': 'Zapf-umzüge',
    'kitchen assembly': 'Zapf-umzüge',
    'industrial': 'Reiner-Assembly',
    'industrial assembly': 'Reiner-Assembly',
    'supply chain assembly': 'Reiner-Assembly'
}

@app.route('/')
def index():
    return render_template('index.html')

def haversine(lat1, lon1, lat2, lon2):
    # Radius of the Earth in miles
    R = 3959.0

    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])

    # Calculate the change in coordinates
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    # Haversine formula
    a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))

    # Calculate the distance
    distance = R * c

    return distance

@app.route('/search', methods=['POST'])
def search():
    request_data = request.get_json()
    radius_val_user = request_data['message']['intent']['provider']['locations'][0]['circle']['radius']['value']
    gps_coordinates_user = request_data['message']['intent']['provider']['locations'][0]['circle']['gps']   
    user_lat, user_lon = map(float, gps_coordinates_user.split(','))
    user_input = str(request_data['message']['intent']['category']['descriptor']['code']) # comparing the user_input with assembly_keywords
    user_input = user_input.lower().strip()
    user_rating_filter = request_data['message']['intent']['provider']['rating'] # the result would be like gt, gte, lt and lte, for example gte>4
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
    # Loop through each provider in the GraphQL response
    for provider_data in response_data["data"]["providers"]["data"]:
        # Extract provider attributes
        provider_attributes = provider_data["attributes"]
        provider_data_id         = provider_data["id"]
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
        location_data    = provider_attributes["location_id"]["data"]["attributes"]
        location_country = location_data["country"]
        location_state   = location_data["state"]
        location_city    = location_data["city"]
        location_lat     = location_data["latitude"]
        location_long    = location_data["longitude"]
        location_zip     = location_data["zip"]
        
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
        rating      = str(get_provider_rating(provider_name))
        location    = get_provider_location(provider_name, location_lat, location_long, location_city,location_zip )
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
                "price":price,            
            }
            for item in items_data
        ] 
       
        # Construct the provider object
        provider_obj = {
            "id": provider_data_id,
            "rating": rating,
            "location":location,
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

    # Check if the user provided a radius filter
    if radius_val_user != '0.0':
        radius_filter_enabled = True
    else:
        radius_filter_enabled = False 

    if user_rating_filter != 'lte<5':
        rating_filter_enabled = True
    else:
        rating_filter_enabled = False 

    # Initialize selected_provider to a default value
    selected_provider = 'default'

    # Check if user_input is in the assembly_keywords dictionary
    if user_input in assembly_keywords:
        selected_provider = assembly_keywords[user_input]

    if selected_provider == 'all':
         # Include all providers in providers_list
        if (radius_filter_enabled == True) or (rating_filter_enabled ==True):
            filtered_providers = []
            for provider in providers_list:
                provider_location = provider['location'][0]['gps']
                provider_lat, provider_lon = map(float, provider_location.split(','))
                distance_from_user = haversine(user_lat, user_lon, provider_lat, provider_lon) 
                provider_rating = float(provider['rating'])
                if 'gte>' in user_rating_filter:
                    user_rating_operator = 'gte'
                    user_rating_value = float(user_rating_filter.replace('gte>', ''))
                elif 'gt' in user_rating_filter:
                    user_rating_operator = 'gt'
                    user_rating_value = float(user_rating_filter.replace('gt>', ''))
                elif 'lte<' in user_rating_filter:
                    user_rating_operator = 'lte'
                    user_rating_value = float(user_rating_filter.replace('lte<', ''))
                elif 'lt<' in user_rating_filter:
                    user_rating_operator = 'lt'
                    user_rating_value = float(user_rating_filter.replace('lt<', ''))          

                if (radius_filter_enabled and distance_from_user > float(radius_val_user)) or (rating_filter_enabled and not (
                                                                            (user_rating_operator == 'gt' and provider_rating > user_rating_value) or
                                                                            (user_rating_operator == 'gte' and provider_rating >= user_rating_value) or
                                                                            (user_rating_operator == 'lt' and provider_rating < user_rating_value) or
                                                                            (user_rating_operator == 'lte' and provider_rating <= user_rating_value)
                    )) :
                        continue  # Skip to the next provider if the distance filter is not satisfied

                # If the provider satisfies both distance and rating filters, add it to the list
                filtered_providers.append(provider)

            providers_list = filtered_providers
        else:
            pass
    else:
        providers_list = [provider for provider in providers_list if provider['descriptor']['name'] == selected_provider]
    # Update template_data with the providers list
    template_data['context']['domain'] = domain_id
    template_data['context']['bpp_id'] = provider_id
    template_data['context']['bpp_uri'] = provider_uri
    template_data['context']['country'] = location_country
    template_data['message']['catalog']['descriptor']['name'] = 'Assembly Service'
    template_data['message']['catalog']['providers'] = providers_list
    return jsonify(template_data)


def get_provider_rating(provider_name):
    if provider_name == "ETS-Assembly":
        return 3.7
    elif provider_name == "Outbox-Assembly":
        return 2.9
    elif provider_name == "Wirth-Werkzeugbau":
        return 4.5
    elif provider_name == "ABS-Assembly":
        return 4.0
    elif provider_name == "PCBA-Assembly":
        return 4.2
    elif provider_name == "Zapf-umzüge":
        return 3.1
    elif provider_name == "Reiner-Assembly":
        return 3.8

def get_provider_location(provider_name, location_lat, location_long, location_city,location_zip ):
    location = []

    if provider_name == "ETS-Assembly":
        location = [
           {
             "gps": f"{location_lat}, {location_long}",
             "city":{
                "name": location_city,
                "code": location_zip
             }  
           }
        ]
    elif provider_name == "Zapf-umzüge":
        location = [
           {
             "gps": f"{location_lat}, {location_long}",
             "city":{
                "name": location_city,
                "code": location_zip
             }  
           }
        ]
    elif provider_name == "Outbox-Assembly":
        location = [
           {
             "gps": f"{location_lat}, {location_long}",
             "city":{
                "name": location_city,
                "code": location_zip
             }  
           }
        ]
    elif provider_name == "PCBA-Assembly":
        location = [
           {
             "gps": f"{location_lat}, {location_long}",
             "city":{
                "name": location_city,
                "code": location_zip
             }  
           }
        ]
    elif provider_name == "Wirth-Werkzeugbau":
        location = [
           {
             "gps": f"{location_lat}, {location_long}",
             "city":{
                "name": location_city,
                "code": location_zip
             }  
           }
        ]
    elif provider_name == "Reiner-Assembly":
        location = [
           {
             "gps": f"{location_lat}, {location_long}",
             "city":{
                "name": location_city,
                "code": location_zip
             }  
           }
        ]
    elif provider_name == "ABS-Assembly":
        location = [
           {
             "gps": f"{location_lat}, {location_long}",
             "city":{
                "name": location_city,
                "code": location_zip
             }  
           }
        ]
    return location

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
    elif provider_name == "Zapf-umzüge":
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
                        "value": "Furniture Assembly"
                    }
                ],
                "display": True
            },
            # Add other tags as needed
        ]
        price = {
            "currency": "EUR",
            "value": "starting from 60 EUR"
        }
    elif provider_name == "Outbox-Assembly":
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
    elif provider_name == "PCBA-Assembly":
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
                        "value": "Circuit Board Assembly"
                    }
                ],
                "display": True
            },
            # Add other tags as needed
        ]
        price = {
            "currency": "EUR",
            "value": "starting from 150 EUR"
        }
    elif provider_name == "Wirth-Werkzeugbau":
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
                        "value": "Car Engine Assembly"
                    }
                ],
                "display": True
            },
            # Add other tags as needed
        ]
        price = {
            "currency": "EUR",
            "value": "starting from 700 EUR"
        }
    elif provider_name == "Reiner-Assembly":
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
                        "value": "Industrial Assembly"
                    }
                ],
                "display": True
            },
            # Add other tags as needed
        ]
        price = {
            "currency": "EUR",
            "value": "starting from 700 EUR"
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
    app.run(debug=False)
