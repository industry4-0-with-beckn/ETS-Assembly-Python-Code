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
Leitstand             = "opc.tcp://192.168.97.101:4840"
Palettenlager         = "opc.tcp://192.168.97.102:4840"
Handling              = "opc.tcp://192.168.97.103:4840"
Presse_Press          = "opc.tcp://192.168.97.104:4840"
assembly_process      = False
user                  = "MES"
password              = "training"
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
order_lock = threading.Lock()

webhook_url = 'https://9b57-194-95-60-104.ngrok-free.app/'
app = Flask(__name__)

# Global variable to keep track of the form number
form_counter = 1

@app.route('/config')
def index():
    return render_template('index.html')

def confirm_order_async():
    thread = threading.Thread(target=confirm_order)
    thread.start()

@app.route('/status', methods=['POST'])
def status():
    global Assembly_Status
    print("The status sent")
    response = jsonify({"status": Assembly_Status})
    return response

@app.route('/confirm', methods=['POST'])
def confirm():
    confirm_order_async()
    return jsonify('True')

def confirm_order():
    global Assembly_Status
    Assembly_Status = "Order Started"
    connect_status = connect_opcua()
    print('ETS Machine Connected')
    if connect_status == True:
        #set color and quantity
        #color_status = set_color()
        color_status = True
        if color_status==True:
            print('Color Set')
            process_status = process_order_dummy()
            if process_status == True:
                #Order Successful
                Assembly_Status = 'Completed'
                print('The assembly status is: ',Assembly_Status)
                return True
            else:
                #Order not Successful
                print('Order not successful')
        else:
            #Order not Successful
            print('Order not sucessful')
    else:
        return False
        #return status that machine is not avaible

def process_order_dummy():
    global Assembly_Status
    time.sleep(3)
    Assembly_Status = "Assembly process started for the Order Number:  1234"
    time.sleep(3)
    Assembly_Status = "Process has started for Box Number 1234."
    time.sleep(3)
    Assembly_Status = "Palet is successfully moved to the handling process"
    time.sleep(3)
    Assembly_Status = "Handling process has started"
    time.sleep(3)
    Assembly_Status = "Handling process has successfully completed" 
    time.sleep(3)
    Assembly_Status = "Lid pressing process has started" 
    time.sleep(3)
    Assembly_Status = "Lid pressing process has successfully completed"
    time.sleep(3)
    Assembly_Status = "The assembled box is successfully stored in the pallet storage"
    time.sleep(3)
    Assembly_Status = "Box Number 1234 is successfully assembled"
    time.sleep(3)
    Assembly_Status = "The Order number 1234 is successfully completed"
    time.sleep(3)
    return True

def process_order():
    global assembly_process
    global Assembly_Status
    global Order_Number
    global order_lock
    global selected_quantity
    if request.method == 'POST':
        # Try to acquire the lock
        if order_lock.acquire(blocking=False):  
            try:      
                for quantity in range(1,selected_quantity+1):
                    order_status_check = root_ControlStation.get_children()[0].get_children()[4].get_children()[8].get_value()
                    if order_status_check and assembly_process==False:
                        assembly_process = True
                        Pallet_Storage_1 = root_PalletStore.get_children()[0].get_children()[4].get_children()[5].get_value()
                        Pallet_Storage_2 = root_PalletStore.get_children()[0].get_children()[4].get_children()[6].get_value()
                        # Check if the Pallet storage has 10 pallets or 0 pallet
                        if Pallet_Storage_1 == 10:
                            assembly_process = False
                            return jsonify({'message':'Order cannot be placed. The Pallets in the pallet storage must be less than 10'})
                        elif Pallet_Storage_1 == 0:
                            assembly_process = False
                            return jsonify({'message':'Order cannot be placed. Add Pallets to the pallet storage'})
                        elif Pallet_Storage_2 == 12:
                            assembly_process = False
                            return jsonify({'message': 'Order cannot be placed. Empty the Pallets from pallet storage 2'}) 
                        # Setting the order number 
                        Order_Number = random.randint(1000,9999)
                        dv_order = opcua.ua.DataValue(opcua.ua.Variant(Order_Number, opcua.ua.VariantType.Int16))
                        dv_order.ServerTimestamp = None
                        dv_order.SourceTimestamp = None
                        # Setting the order value
                        root_ControlStation.get_children()[0].get_children()[4].get_children()[0].set_value(dv_order)
                        Assembly_Status = f"Assembly process started for the Order Number:  {Order_Number}."
                        time.sleep(5)
                        # Give the order if the status is true
                        give_order_true = opcua.ua.DataValue(opcua.ua.Variant(True, opcua.ua.VariantType.Boolean))
                        give_order_true.ServerTimestamp = None
                        give_order_true.SourceTimestamp = None
                        root_ControlStation.get_children()[0].get_children()[4].get_children()[6].set_value(give_order_true)                
                        while root_PalletStore.get_children()[0].get_children()[4].get_children()[3].get_value() != 2:
                            pass
                        Assembly_Status = f"Process has started for Box Number {quantity}."

                        while root_ControlStation.get_children()[0].get_children()[4].get_children()[7].get_value() != True:
                            pass
                        give_order_false = opcua.ua.DataValue(opcua.ua.Variant(False, opcua.ua.VariantType.Boolean))
                        give_order_false.ServerTimestamp = None
                        give_order_false.SourceTimestamp = None
                        root_ControlStation.get_children()[0].get_children()[4].get_children()[6].set_value(give_order_false) 

                        while root_PalletStore.get_children()[0].get_children()[4].get_children()[3].get_value() != 4:
                            pass
                        Assembly_Status = "Palet is successfully moved to the handling process"

                        while  root_Handling.get_children()[0].get_children()[4].get_children()[3].get_value() == 0:
                            pass
                        Assembly_Status = "Handling process has started" 

                        while  root_Handling.get_children()[0].get_children()[4].get_children()[3].get_value() != 0:
                            pass
                        Assembly_Status = "Handling process has successfully completed" 
                   
                        while  root_Press.get_children()[0].get_children()[4].get_children()[3].get_value() == 0:
                            pass
                        Assembly_Status = "Lid pressing process has started" 

                        while root_Press.get_children()[0].get_children()[4].get_children()[3].get_value() != 4:
                            pass
                        Assembly_Status = "Lid pressing process has successfully completed" 
                            
                        while root_PalletStore.get_children()[0].get_children()[4].get_children()[3].get_value() != 2:
                            pass
                        Assembly_Status = "The assembled box is successfully stored in the pallet storage" 
                        time.sleep(10) # Waiting for the Palet storage to update its values
                        if (root_PalletStore.get_children()[0].get_children()[4].get_children()[6].get_value() == (Pallet_Storage_2 + 1)) and (root_PalletStore.get_children()[0].get_children()[4].get_children()[5].get_value() == (Pallet_Storage_1 - 1)): 
                            Assembly_Status = f"Box Number {quantity} is successfully assembled"
                            assembly_process = False
                            if(quantity == selected_quantity):
                                Assembly_Status = f"The Order number {Order_Number} is successfully completed"                                
                                assembly_process = False
                                return True
                                # return jsonify({'message': f"The Order number {Order_Number} is successfully completed"})                   
                        else:
                            Assembly_Status = "Assembly process not completed successfully" 
                            Assembly_Status = 'No order for processing'
                            assembly_process = False
                            return False
                            #return jsonify({'message': f"The Order number {Order_Number} cannot be completed due to some error"})  
                        # Giving delay to the next order to start    
                        time.sleep(10)                 
                    else:
                        #return jsonify({'Assembly Process', assembly_process })
                        #return jsonify({'message': f"The Assembly Process is  {assembly_process}"})
                        #return jsonify({'message': 'Order status is not true. Cannot give an order.' })
                        return False
            except Exception as e:
                #return jsonify({'error': str(e)}), 500  # Handle errors gracefully and return a 500 status code
                return False   
            finally:
                # Release the lock after processing
                order_lock.release()   
        else:
            #return jsonify({'message': 'Order is already being processed'}), 403
            return False 
    else:
        #return jsonify({'message': 'Invalid request method'}), 400
        return False 

def set_color():
    global selected_color
    # Create a DataValue with the selected color
    dv_color = opcua.ua.DataValue(opcua.ua.Variant(selected_color, opcua.ua.VariantType.Byte))
    dv_color.ServerTimestamp = None
    dv_color.SourceTimestamp = None
    # Set the color value in OPC UA
    root_ControlStation.get_children()[0].get_children()[4].get_children()[1].set_value(dv_color)
    # Reading the updated value of the color
    updated_color = root_ControlStation.get_children()[0].get_children()[4].get_children()[1].get_value()            
    # Check if the color was set correctly
    if updated_color == selected_color:
        status_color = True
    else:
        status_color = False
    return status_color
       
def connect_opcua():
   # Declaring global root and client variables for control station
    global client_ControlStation
    global root_ControlStation
    # Declaring global root and client variables for Pallet Store
    global client_PalletStore
    global root_PalletStore
    # Declaring global root and client variables for Handling
    global client_Handling
    global root_Handling
    # Declaring global root and client variables for Press
    global client_Press
    global root_Press
    try:
        # Create an instance of the OPC UA Client and connecting it
        client_ControlStation = Client(Leitstand)
        client_ControlStation.set_user(user)
        client_ControlStation.set_password(password)
        client_ControlStation.connect()
        root_ControlStation = client_ControlStation.get_root_node()
        status1= '1. Connected to OPC UA Leitstand server successfully.'

        client_PalletStore = Client(Palettenlager)
        client_PalletStore.set_user(user)
        client_PalletStore.set_password(password)
        client_PalletStore.connect()
        root_PalletStore = client_PalletStore.get_root_node()
        status2= '2. Connected to OPC UA Palettenlager server successfully.'

        client_Handling = Client(Handling)
        client_Handling.set_user(user)
        client_Handling.set_password(password)
        client_Handling.connect()
        root_Handling = client_Handling.get_root_node()
        status3= '3. Connected to OPC UA Handling server successfully.'

        client_Press = Client(Presse_Press)
        client_Press.set_user(user)
        client_Press.set_password(password)
        client_Press.connect()
        root_Press = client_Press.get_root_node()
        status4= '4. Connected to OPC UA Press server successfully.'
        status = status1 + '<br>' +  status2 + '<br>' + status3 + '<br>' + status4
        availablity_check = True
    except Exception as e:
        status1 = f'Error connecting to OPC UA Leitstand server: {str(e)}'
        status2 = f'Error connecting to OPC UA Palettenlager server: {str(e)}'
        status3 = f'Error connecting to OPC UA Handling server: {str(e)}'
        status4 = f'Error connecting to OPC UA Press server: {str(e)}'
        status = status1 + '<br>' +  status2 + '<br>' + status3 + '<br>' + status4
        availablity_check = False
    return availablity_check 
@app.route('/submit', methods=['POST'])
def submit():
    global form_counter
    global selected_color
    global selected_quantity
    color             = request.form.get('color')
    quantity          = request.form.get('quantity')

    # Calculate the value by multiplying quantity by 10
    quotation         = int(quantity) * 10
    selected_color    = color
    selected_quantity = quantity
    # Create a JSON object
    data = {'color of the lid': color, 'quantity': int(quantity), 'Total_Cost': quotation}

    # Increment the form counter and use it in the formId
    form_id = f"ETS-{form_counter}"
    form_counter += 1

    # GraphQL mutation
    url = "https://9520-194-95-60-104.ngrok-free.app/graphql"  # Replace with your GraphQL server endpoint

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
        send_select_req()
        return '', 204
        #return jsonify("Data Submitted to BPP")
    else:
        print("Mutation failed. Status code:", response.status_code)
        #return jsonify(response.text)
        return jsonify("Data not Submitted to BPP")

def send_select_req():
    query_path = os.path.join(os.path.dirname(__file__), 'templates', 'request_select.json')
    # Read the GraphQL query from the template file
    with open(query_path, 'r') as query_template_file:
        select_request = json.load(query_template_file)

    # Send a POST request to the specified URL with the JSON data
    response = requests.post(webhook_url, json=select_request)

    # Print the response
    if response.status_code == 200:
        #return jsonify(response.json())
        print("Data Submitted to Webhook")
    else:
        print("Mutation failed. Status code:", response.status_code)
        #return jsonify(response.text)
        print("Data not Submitted to Webhook")

if __name__ == '__main__':
    app.run(debug=False)


    # def fetch_graphql_provider_data():

