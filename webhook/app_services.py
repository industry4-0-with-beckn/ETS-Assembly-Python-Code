import os
import json
import requests

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class AppService:
    def get_hello(self, body):
        try:
            sandbox_url = ''
            if 'financial' in body['context']['action']:
                sandbox_url = f"{os.environ.get('SANDBOXURL')}/financial-services/{body['context']['action']}"
            elif 'dsep' in body['context']['domain']:
                sandbox_url = f"{os.environ.get('SANDBOXURL')}/dsep/{body['context']['action']}"
            elif 'dent' in body['context']['domain']:
                sandbox_url = f"{os.environ.get('SANDBOXURL')}/dent/{body['context']['action']}"
            else:
                sandbox_url = f"{os.environ.get('SANDBOXURL')}/mobility/{body['context']['action']}"
            
            print('called', sandbox_url)

            response = requests.post(sandbox_url, json=body)

            if not response.json().get('context'):
                print('Invalid response from sandbox bpp api')
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


# Example usage:
body = {
    'context': {
        'domain': 'financial',
        'action': 'search',
        'message_id': 123,
        'bap_id': 456,
        'bap_uri': 'example.com',
        'transaction_id': 789,
        'bpp_id': 101,
        'bpp_uri': 'example.org',
    }
}

app_service = AppService()
app_service.get_hello(body)
