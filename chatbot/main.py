from fastapi import FastAPI
from fastapi import Request
from fastapi.responses import JSONResponse
import db
import helper

app = FastAPI()

inprogress_orders = {}


@app.post("/")
async def handle_request(request: Request):
    # Retrieve the JSON data from the request
    payload = await request.json()

    # Extract the necessary information from the payload
    # based on the structure of the WebhookRequest from Dialogflow
    intent = payload['queryResult']['intent']['displayName']
    parameters = payload['queryResult']['parameters']
    output_contexts = payload['queryResult']['outputContexts']
    session_id = helper.extract_session_id(output_contexts[0]['name'])

    intent_handler_dict = {
        'order.add': add_to_order,
        'order.remove': remove_from_order,
        'order.complete': complete_order,
        'track.order - context: ongoing-tracking': track_order
    }

    return intent_handler_dict[intent](parameters, session_id)
   

def track_order(parameters:dict, session_id:str):
        order_id = int(parameters['number'])
        status = db.get_order_status(order_id)

        if status:
            fulltext = f"The order status for the order {order_id} is '{status}' "
        else:
            fulltext = f"No order found with order ID '{order_id}' "

        return JSONResponse(content={
        "fulfillmentText": fulltext
    })

        


def add_to_order(parameters:dict, session_id:str):
     fooditems = parameters['food-item']
     quantity = parameters['number']

     if len(fooditems) != len(quantity):
          fulltext = 'Can u specify the food items and quantities more clearly?'
     else:
          food_dict = dict(zip(fooditems,quantity))
          if session_id in inprogress_orders:
            current_food_dict = inprogress_orders[session_id]
            current_food_dict.update(food_dict)
            inprogress_orders[session_id] = current_food_dict
          else:
            inprogress_orders[session_id] = food_dict

          order_str = helper.get_str_from_food_dict(inprogress_orders[session_id])
          fulltext = f"So far you have: {order_str}. Do you need anything else?"
          

     return JSONResponse(content={
        "fulfillmentText": fulltext
    })



def save_to_db(order: dict):
    next_order_id = db.get_next_order_id()

    # Insert individual items along with quantity in orders table
    for food_item, quantity in order.items():
        rcode = db.insert_order_item(
            food_item,
            quantity,
            next_order_id
        )

        if rcode == -1:
            return -1

    # Now insert order tracking status
    db.insert_order_tracking(next_order_id, "in progress")

    return next_order_id

          

def complete_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        fulltext = "I'm having a trouble finding your order. Sorry! Can you place a new order please?"
    else:
        order = inprogress_orders[session_id]
        order_id = save_to_db(order)
        if order_id == -1:
            fulltext = "Sorry, I couldn't process your order due to a backend error. " \
                               "Please place a new order again"
        else:
            order_total = db.get_total_order_price(order_id)

            fulltext = f"Awesome. We have placed your order. " \
                           f"Here is your order id # {order_id}. " \
                           f"Your order total is {order_total} which you can pay at the time of delivery!"

        del inprogress_orders[session_id]

    
    return JSONResponse(content={
        "fulfillmentText": fulltext
    })



def remove_from_order(parameters: dict, session_id: str):
    if session_id not in inprogress_orders:
        return JSONResponse(content={
            'fulfillmentMessages': [
                {
                    'text': {
                        'text': [
                            "I'm having a trouble finding your order. Sorry! Can you place a new order please?"
                        ]
                    }
                }
            ]
        })
    
    food_items = parameters["food-item"]
    current_order = inprogress_orders[session_id]

    removed_items = []
    no_such_items = []

    for item in food_items:
        if item not in current_order:
            no_such_items.append(item)
        else:
            removed_items.append(item)
            del current_order[item]

    if len(removed_items) > 0:
        fulltext = f'Removed {",".join(removed_items)} from your order!'

    if len(no_such_items) > 0:
        fulltext = f' Your current order does not have {",".join(no_such_items)}'

    if len(current_order.keys()) == 0:
        fulltext += " Your order is empty!"
    else:
        order_str = helper.get_str_from_food_dict(current_order)
        fulltext += f" Here is what is left in your order: {order_str}"

    
    return JSONResponse(content={
        "fulfillmentText": fulltext
    })
