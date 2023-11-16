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
    file_path = os.path.join(os.path.dirname(__file__), 'response', 'response.search.json')
    with open(file_path, 'r') as json_file:
        response_data = json.load(json_file)
    return jsonify(response_data)

@app.route('/select', methods=['POST'])
def select():

    file_path = os.path.join(os.path.dirname(__file__), 'response', 'response.select.json')
    with open(file_path, 'r') as json_file:
        response_data = json.load(json_file)
    return jsonify(response_data)

if __name__ == '__main__':
    app.run(debug=True)
