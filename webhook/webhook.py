from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

connect_url = 'http://localhost:5000/connect' 
# Load environment variables from .env file
load_dotenv()
app = Flask(__name__)

@app.route('/get_hello', methods=['POST'])
def get_hello():
    try:
        # Get the JSON data from the POST request body
        data = request.get_json()
        ets_url = ''
        # Check if the 'actions' key exists in the JSON data
        if 'actions' in data:
            actions = data['actions']
        if actions == 'select':
            ets_url = f"{os.environ.get('ETSURL')}/connect"
            response = requests.post(ets_url)
            # Check the response status code and return the JSON response to Postman
            if response.status_code == 200:
                return response.json()
            else:
                return jsonify({'error': 'Machine is not available'}), 500
        else:
            return jsonify({'error': 'Actions not found in the request body'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True,port=5001)
