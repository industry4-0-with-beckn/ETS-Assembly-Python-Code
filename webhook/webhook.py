from flask import Flask, request, jsonify
import requests
import os
import json
import asyncio
from dotenv import load_dotenv
connect_url = 'http://localhost:5000/connect' 
# Load environment variables from .env file
load_dotenv()
app = Flask(__name__)

async def handler_asyn(body):
    try:
        ets_url = ''
        # Check if the 'actions' key exists in the JSON data
        ets_url = f"{os.environ.get('ETSURL')}/{body['context']['action']}"
        print('called', ets_url)
        response = requests.post(ets_url, json=body)
        #response = await asyncio.to_thread(requests.post, ets_url, json=body)

        if not response.json().get('context'):
            print('Invalid response from ets assembly bpp api')
            return
        
        response_data = response.json()
        response_data['context']['message_id'] = body['context']['message_id']
        response_data['context']['bap_id'] = body['context']['bap_id']
        response_data['context']['bap_uri'] = body['context']['bap_uri']
        response_data['context']['transaction_id'] = body['context']['transaction_id']
        response_data['context']['domain'] = body['context']['domain']

        await asyncio.sleep(2)

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
                f"Making post request to: {bpp_client_url}", '\n', '\n', f"Body: {json.dumps(response_data)}", '\n',
                '-----------------------------------------------------------')

            try:
                response = requests.post(bpp_client_url, json=response_data)
                print()
            except Exception as e:
                print('error=>', e)

        await asyncio.sleep(2)  # Add a delay before making the post request
        send_post_request()
    except Exception as err:
        print('The error is:',err)

@app.route('/', methods=['POST'])
def bpp_handler():
    try:
        print('Request received')
        body = request.get_json()
        # Start the asynchronous task and immediately return the acknowledgment response
        #asyncio.create_task(handler_asyn(body))
        asyncio.run(handler_asyn(body))
        #await handler_asyn(body)
        return jsonify({
            'message': {
                'ack': {
                    'status': 'ACK'
                }
            }
        })
    except Exception as err:
        print(err)
        return jsonify({'error': 'Internal Server Error'}, 500)

@app.route('/ping', methods=['GET'])
def ping():
    return jsonify({'ok': True})

if __name__ == '__main__':
    app.run(debug=True,port=5001)
