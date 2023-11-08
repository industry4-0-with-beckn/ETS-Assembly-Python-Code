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

app = Flask(__name__)

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
