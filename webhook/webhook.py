from flask import Flask, request, jsonify
import requests
import os
import json
import asyncio
from dotenv import load_dotenv
from math import radians, sin, cos, sqrt, atan2
connect_url = 'http://localhost:5000/connect' 
# Load environment variables from .env file
load_dotenv()
app = Flask(__name__)

# Target location to the east of the user
target_lat = 30.876877
target_lon = 73.868969 + 0.035  # Adjusted longitude to be approximately 2.5 miles east


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

async def handler_asyn(body):
    try:
        ets_url = ''
        #gps_coordinates = body['message']['intent']['provider']['locations'][0]['circle']['gps']  
        #radius_val = body['message']['intent']['provider']['locations'][0]['circle']['gps']['radius']['value'] 
        #user_lat, user_lon = map(float, gps_coordinates.split(','))
        #location_range_value = float(body['message']['intent']['provider']['locations'][0]['circle']['radius']['value']) # the value would be in miles
        #distance_cal =  haversine(user_lat, user_lon, target_lat, target_lon)
        #if body['context']['domain'] == "supply-chain-services:assembly": 
            # Check if the 'actions' key exists in the JSON data
        ets_url = f"{os.environ.get('ETSURL')}/{body['context']['action']}"
        print('Assembly URL Called', ets_url)
        response = requests.post(ets_url, json=body)

        if not response.json().get('context'):
            print('No response from search request')
            return
        
        response_data = response.json()
        response_data['context']['message_id'] = body['context']['message_id']
        response_data['context']['bap_id'] = body['context']['bap_id']
        response_data['context']['bap_uri'] = body['context']['bap_uri']
        response_data['context']['transaction_id'] = body['context']['transaction_id']

        await asyncio.sleep(2)

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
