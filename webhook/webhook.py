from flask import Flask, request, jsonify
import requests
import os
import json
from dotenv import load_dotenv

connect_url = 'http://localhost:5000/connect' 
# Load environment variables from .env file
load_dotenv()
app = Flask(__name__)

@app.route('/', methods=['POST'])
def get_hello(self, body):
    try:
        # Get the JSON data from the POST request body
        data = request.get_json()
        ets_url = ''
        # Check if the 'actions' key exists in the JSON data
        if 'financial' in body['context']['action']:
            ets_url = f"{os.environ.get('ETSURL')}/{body['context']['action']}"
        print('called', ets_url)
        response = requests.post(ets_url, json=body)
       
        if not response.json().get('context'):
            print('Invalid response from ets assembly bpp api')
            return

        response_data = response.json()
        response_data['context']['message_id'] = body['context']['message_id']
        response_data['context']['bap_id'] = body['context']['bap_id']
        response_data['context']['bap_uri'] = body['context']['bap_uri']
        response_data['context']['transaction_id'] = body['context']['transaction_id']
        response_data['context']['domain'] = body['context']['domain']

        if body['context'].get('bpp_id'):
            response_data['context']['bpp_id'] = body['context']['bpp_id']

        if body['context'].get('bpp_uri'):
            response_data['context']['bpp_uri'] = body['context']['bpp_uri']

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

        bpp_client_url = f"{os.environ.get('BPPCLIENTURL')}/{request_action}"

        def send_post_request():
            print('\n\n', '-----------------------------------------------------------', '\n',
                f"Making post request to: {bpp_client_url}", '\n', '\n', f"Body: {json.dumps(body)}", '\n',
                    '-----------------------------------------------------------')

            try:
                response = requests.post(bpp_client_url, json=response_data)
            except Exception as e:
                print('error=>', e)

        # Delayed post request (similar to setTimeout in JavaScript)
        import time
        time.sleep(2)
        send_post_request()
    except Exception as err:
        print(err)

    #     if 'actions' in data:
    #         actions = data['actions']
    #     if actions == 'select':
    #         ets_url = f"{os.environ.get('ETSURL')}/connect"
    #         response = requests.post(ets_url)
    #         # Check the response status code and return the JSON response to Postman
    #         if response.status_code == 200:
    #             return response.json()
    #         else:
    #             return jsonify({'error': 'Machine is not available'}), 500
    #     else:
    #         return jsonify({'error': 'Actions not found in the request body'}), 400
    # except Exception as e:
    #     return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True,port=5001)
