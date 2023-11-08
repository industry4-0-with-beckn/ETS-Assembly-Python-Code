from flask import Flask, request, jsonify
import requests
import os
import json
import asyncio
from dotenv import load_dotenv
connect_url = 'http://localhost:5000/connect' 
# GraphQL endpoint URL
graph_url = "http://localhost:1337/graphql"

# Define the request headers
headers = {
    "Content-Type": "application/json",
}

# Load environment variables from .env file
load_dotenv()
app = Flask(__name__)

def search_response():
    file_path = os.path.join(os.path.dirname(__file__), 'response', 'response.search.json')
    with open(file_path, 'r') as template_file:
        template_data = json.load(template_file)
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
            location_address = location_data["address"]
            location_country = location_data["country"]
            location_state = location_data["state"]
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
            }
        ]
        return template_data
    else:
        print("GraphQL request failed with status code:", response.status_code)
        return jsonify({'Not ok': True})  

async def handler_asyn(body):
    try:
        request_action = None
        request_action_map = {
            'search': 'on_search',
            'select': 'on_select',
            'init': 'on_init',
            'confirm': 'on_confirm',
            'status': 'on_status',
            'track': 'on_track',
            'cancel': 'on_cancel',
            'update': 'on_update',
            'rating': 'on_rating',
            'support': 'on_support',
            'get_cancellation_reasons': 'cancellation_reasons',
            'get_rating_categories': 'rating_categories',
        }
        request_action = request_action_map.get(body['context']['action'], None)
        if request_action is None:
            print(f'Invalid request action -> {request_action}')
            return
        if body['context']['action'] == "search":
            on_search = search_response()
            print("on_search response",on_search)
            bpp_client_url = f"{os.environ.get('BPPCLIENTURL')}/{request_action}"
            def send_post_request():
                print('\n\n', '-----------------------------------------------------------', '\n',
                    f"Making post request to: {bpp_client_url}", '\n', '\n', f"Body: {json.dumps(on_search)}", '\n',
                    '-----------------------------------------------------------')
                try:
                    response = requests.post(bpp_client_url, json=on_search)
                    print(response)
                except Exception as e:
                    print('error=>', e)
            await asyncio.sleep(2)  # Add a delay before making the post request
            send_post_request()
        # else:
        #     ets_url = ''
        #     # Check if the 'actions' key exists in the JSON data

        #     ets_url = f"{os.environ.get('ETSURL')}/{body['context']['action']}"
        #     print('called', ets_url)
        #     response = requests.post(ets_url, json=body)

        #     if not response.json().get('context'):
        #         print('Invalid response from ets assembly bpp api')
        #         return
        
        #     response_data = response.json()
        #     response_data['context']['message_id'] = body['context']['message_id']
        #     response_data['context']['bap_id'] = body['context']['bap_id']
        #     response_data['context']['bap_uri'] = body['context']['bap_uri']
        #     response_data['context']['transaction_id'] = body['context']['transaction_id']
        #     response_data['context']['domain'] = body['context']['domain']

        #     await asyncio.sleep(2)

        #     if body['context'].get('bpp_id'):
        #         response_data['context']['bpp_id'] = body['context']['bpp_id']

        #     if body['context'].get('bpp_uri'):
        #         response_data['context']['bpp_uri'] = body['context']['bpp_uri']


        #     bpp_client_url = f"{os.environ.get('BPPCLIENTURL')}/{request_action}"

        #     def send_post_request():
        #         print('\n\n', '-----------------------------------------------------------', '\n',
        #             f"Making post request to: {bpp_client_url}", '\n', '\n', f"Body: {json.dumps(response_data)}", '\n',
        #             '-----------------------------------------------------------')
        #         try:
        #             response = requests.post(bpp_client_url, json=response_data)
        #             print()
        #         except Exception as e:
        #             print('error=>', e)
        #     await asyncio.sleep(2)  # Add a delay before making the post request
        #     send_post_request()
    except Exception as err:
        print('The error is:',err)

# async def handler_asyn(body):
#     try:
#         ets_url = ''
#         # Check if the 'actions' key exists in the JSON data

#         ets_url = f"{os.environ.get('ETSURL')}/{body['context']['action']}"
#         print('called', ets_url)
#         response = requests.post(ets_url, json=body)

#         if not response.json().get('context'):
#             print('Invalid response from ets assembly bpp api')
#             return
        
#         response_data = response.json()
#         response_data['context']['message_id'] = body['context']['message_id']
#         response_data['context']['bap_id'] = body['context']['bap_id']
#         response_data['context']['bap_uri'] = body['context']['bap_uri']
#         response_data['context']['transaction_id'] = body['context']['transaction_id']
#         response_data['context']['domain'] = body['context']['domain']

#         await asyncio.sleep(2)

#         if body['context'].get('bpp_id'):
#             response_data['context']['bpp_id'] = body['context']['bpp_id']

#         if body['context'].get('bpp_uri'):
#             response_data['context']['bpp_uri'] = body['context']['bpp_uri']

#         request_action = None
#         request_action_map = {
#             'search': 'on_search',
#             'select': 'on_select',
#             'init': 'on_init',
#             'confirm': 'on_confirm',
#             'status': 'on_status',
#             'track': 'on_track',
#             'cancel': 'on_cancel',
#             'update': 'on_update',
#             'rating': 'on_rating',
#             'support': 'on_support',
#             'get_cancellation_reasons': 'cancellation_reasons',
#             'get_rating_categories': 'rating_categories',
#         }

#         request_action = request_action_map.get(body['context']['action'], None)

#         if request_action is None:
#             print(f'Invalid request action -> {request_action}')
#             return

#         bpp_client_url = f"{os.environ.get('BPPCLIENTURL')}/{request_action}"

#         def send_post_request():
#             print('\n\n', '-----------------------------------------------------------', '\n',
#                 f"Making post request to: {bpp_client_url}", '\n', '\n', f"Body: {json.dumps(response_data)}", '\n',
#                 '-----------------------------------------------------------')

#             try:
#                 response = requests.post(bpp_client_url, json=response_data)
#                 print()
#             except Exception as e:
#                 print('error=>', e)

#         await asyncio.sleep(2)  # Add a delay before making the post request
#         send_post_request()
#     except Exception as err:
#         print('The error is:',err)

@app.route('/', methods=['POST'])
def bpp_handler():
    try:
        print('Request received')
        body = request.get_json()
        # Start the asynchronous task and immediately return the acknowledgment response
        asyncio.run(handler_asyn(body))
        return jsonify({
            'message': {
                'ack': {
                    'status': 'ACK'
                }
            }
        })
    except Exception as err:
        import traceback
        traceback.print_exc()  # Print the traceback for debugging
        print(err)
        return jsonify({'error': 'Internal Server Error'}, 500)

@app.route('/ping', methods=['GET'])
def ping():    
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(debug=False,port=5004)
