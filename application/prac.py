
import requests
form_url = "https://2f62-194-95-60-104.ngrok-free.app/status"
order_status = requests.post(form_url)

ful = order_status.json()
print(ful.get('message'))