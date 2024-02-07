from flask import Flask, render_template, request, url_for, jsonify, Response
from flask import jsonify
import threading
import opcua
from opcua import Client
import logging
import datetime
import configparser
import pandas as pd
import time
import random
import json
import os
import requests

# Define your OPC UA connection settings here
assembly_process      = False
selected_color        = None
client_ControlStation = None
root_ControlStation   = None
    # Declaring global root and client variables for Pallet Store
client_PalletStore    = None
root_PalletStore      = None
    # Declaring global root and client variables for Handling
client_Handling       = None
root_Handling         = None
    # Declaring global root and client variables for Press
client_Press          = None
root_Press            = None
selected_quantity     = None
Assembly_Status       = None
Tracking_Status       = None
order_lock = threading.Lock()

app = Flask(__name__)

# Global variable to keep track of the form number
form_counter = 1

@app.route('/config')
def index():
    return render_template('config.html')

def confirm_order_async():
    thread = threading.Thread(target=confirm_order)
    thread.start()

@app.route('/get_tracking_status', methods=['GET'])
def get_tracking_status():
    global Tracking_Status
    return jsonify({'message': Tracking_Status})

# Tracking Form
@app.route('/track', methods=['GET', 'POST'])
def track():
    global Tracking_Status
    Tracking_Status = "Real-Time Tracking"  
    if request.method == 'POST':
        # Retrieve the tracking status from the form submission
        Tracking_Status = request.form.get('trackingStatusInput')
        return jsonify({'message': Tracking_Status})
        #return jsonify({'message': f'Tracking status updated to {Tracking_Status}'})

    return render_template('track.html')

@app.route('/status', methods=['POST'])
def status():
    global Assembly_Status
    print("The Assembly Status in /status is:", Assembly_Status)
    response = jsonify({"status": Assembly_Status})
    return response

@app.route('/confirm', methods=['POST'])
def confirm():
    confirm_order_async()
    return jsonify('True')

def confirm_order():
    global Assembly_Status
    Assembly_Status = "Order Received"
    connect_status = True #Dummy Implementation
    #connect_status = connect_opcua() # Actual Implementation
    if connect_status == True:
        print('ETS Machine Successfully Connected')
        #set color and quantity
        #color_status = set_color()# Actual Implementation
        color_status = True # Dummy Implementation
        if color_status==True:
            print('Color Set')
            Tracking_Status = "Assembly process started"
            time.sleep(10)
            #process_status = process_order() # Actual Implementation
            process_status = process_order_dummy() # Dummy Implementation
            if process_status == True:
                #Order Successful               
                Assembly_Status = 'Completed'
                #print('The assembly status is: ',Assembly_Status)
                return True
            else:
                #Order not Successful
                print('Order not successful')
        else:
            #Order not Successful
            print('Order not sucessful')
    else:
        print('ETS Machine not connected')
        return False
        #return status that machine is not avaible

def process_order_dummy():
    global Assembly_Status
    global Tracking_Status
    time.sleep(5)
    Assembly_Status = "Order Received"
    print('The status is: ',Assembly_Status)
    time.sleep(10)
    Tracking_Status = "Assembly process started"
    print('The Tracking status is: ',Tracking_Status)
    time.sleep(5)
    Assembly_Status = "In Progress"
    print('The status is: ',Assembly_Status)
    Tracking_Status = "Process has started for Box Number 1234."
    print('The Tracking status is: ',Tracking_Status)
    time.sleep(5)
    Tracking_Status = "Palet is successfully moved to the handling process"
    print('The Tracking status is: ',Tracking_Status)
    time.sleep(5)
    Tracking_Status = "Handling process has started"
    print('The Tracking status is: ',Tracking_Status)
    time.sleep(10)
    Tracking_Status = "Handling process has successfully completed" 
    print('The Tracking status is: ',Tracking_Status)
    time.sleep(5)
    Tracking_Status = "Lid pressing process has started" 
    print('The Tracking status is: ',Tracking_Status)
    time.sleep(5)
    Tracking_Status = "Lid pressing process has successfully completed"
    print('The Tracking status is: ',Tracking_Status)
    time.sleep(5)
    Tracking_Status = "The assembled box is successfully stored in the pallet storage"
    print('The Tracking status is: ',Tracking_Status)
    time.sleep(5)
    Tracking_Status = "Container is successfully assembled"
    print('The Tracking status is: ',Tracking_Status)
    time.sleep(5)
    Tracking_Status = "The Order is successfully completed"
    print('The Tracking status is: ',Tracking_Status)
    Assembly_Status = "Order Completed"
    print('The status is: ',Assembly_Status)
    time.sleep(5)
    Assembly_Status = "Order ready to pickup"
    print('The status is: ',Assembly_Status)
    return True

@app.route('/submit', methods=['POST'])
def submit():
    global form_counter
    global selected_color
    global selected_quantity
    color             = request.form.get('color')
    quantity          = request.form.get('quantity')
    if color == 'red':
        selected_color = 1
    elif color == 'blue':
        selected_color = 4
    # Calculate the value by multiplying quantity by 10
    quotation         = int(quantity) * 10
    selected_quantity = quantity

    # Create a JSON object
    data = {'color of the lid': color, 'quantity': int(quantity), 'Total_Cost': quotation}

    # Increment the form counter and use it in the formId
    form_id = f"ETS-{form_counter}"
    form_counter += 1

    # GraphQL mutation
    url = "https://suppliflow-strapi-database.hof-university.de/graphql"  # Replace with your GraphQL server endpoint

    mutation_query = """
    mutation createInputDetail($formId: String!, $formData: JSON!){
      createInputDetail(
        data:{
            form_id:$formId, form_data:$formData
        } 
      ) {
        data{
            id
            attributes{
                form_id
                form_data
                }
            }
        }
    }
    """
    variables = {
        "formId": form_id,  
        "formData": json.dumps(data)  # Convert Python dictionary to JSON string
    }

    headers = {
        "Content-Type": "application/json",
    }

    # Make the GraphQL request
    response = requests.post(url, json={"query": mutation_query, "variables": variables}, headers=headers)

    # Check the response
    if response.status_code == 200:
        #return jsonify(response.json())
        #send_select_req()
        #return '', 204
        return jsonify("ETS Machine configured")
    else:
        print("Mutation failed. Status code:", response.status_code)
        #return jsonify(response.text)
        return jsonify("Data not Submitted to BPP")

if __name__ == '__main__':
    app.run(debug=False)




