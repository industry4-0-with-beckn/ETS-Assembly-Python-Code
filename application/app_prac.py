selected_obj = None

def create_select_response(selected_id):
    global selected_obj
    global strapi_data
    global domain_id 
    global provider_id 
    global provider_uri 
    global location_country
    fulfillments = [
        {"id": "f1", "type": "Delivery", "tracking": False},
        {"id": "f2", "type": "Self-Pickup", "tracking": False}
    ]
    # Declaring an empty list
    selected_obj = []
    # Loop through each provider in the GraphQL response
    for provider_data in strapi_data["data"]["providers"]["data"]:
        # check provider id
        if provider_data["id"] == selected_id:
            provider_attributes = provider_data["attributes"]
            # Extract logo url
            logo_url = logo_data["url"]
            # Extract provider name
            provider_name = provider_attributes["provider_name"]
            short_desc = provider_attributes["short_desc"]
            long_desc = provider_attributes["long_desc"]
            quote_data = {
                "price": {
                    "currency":"Euro",
                    "value":"100"
                }
            }
            xinput_data = {
                "required":true,
                "form":{
                     "mime_type":"text/html",
                     "url":"https://0096-194-95-60-104.ngrok-free.app",
                     "resubmit":false,
                     "auth":{
                        "descriptor":{
                           "code":"jwt"
                        },
                        "value":"eyJhbGciOiJIUzI.eyJzdWIiOiIxMjM0NTY3O.SflKxwRJSMeKKF2QT4"
                    }
                }
            }
            tags, price = update_tags_and_price(provider_name)
            categories_list = [
            {
                "id": category["id"],
            }
            for category in category_ids
            ]
            items_data = provider_attributes["items"]["data"]
            items_list = [
                {
                    "id": item["id"],
                    "descriptor": {
                        "images": [{"url": item["attributes"]["image"]["data"][0]["attributes"]["url"]}],
                        "name": item["attributes"]["name"]
                    },
                    "category_id": categories_list 
                    "tags": tags,
                    "xinput": xinput_data
                    "price":price,            
                }
                for item in items_data
            ] 
            # Construct the provider object
            selected_obj = {
                "provider": {
                    "id": provider_data["id"],
                    "descriptor": {
                        "images": [{"url": logo_url}],
                        "name": provider_name,
                        "short_desc": short_desc,
                        "long_desc": long_desc
                    }
                },
                "items": items_list
                "fulfillments":fulfillments
                "quote": quote_data 
            }



        # Extract location data
        location_data    = provider_attributes["location_id"]["data"]["attributes"]
        location_country = location_data["country"]
        location_state   = location_data["state"]
        location_city    = location_data["city"]
        location_lat     = location_data["latitude"]
        location_long    = location_data["longitude"]
        location_zip     = location_data["zip"]
        
        # Extract other provider attributes
        domain_id = provider_attributes["domain_id"]["data"]["attributes"]["DomainName"]
        provider_id = provider_attributes["provider_id"]
        provider_name = provider_attributes["provider_name"]
        provider_uri = provider_attributes["provider_uri"]
        short_desc = provider_attributes["short_desc"]
        long_desc = provider_attributes["long_desc"]
        # Call the function to update tags and price
        tags, price = update_tags_and_price(provider_name)
        rating      = str(get_provider_rating(provider_name))
        location    = get_provider_location(provider_name, location_lat, location_long, location_city,location_zip )
       
