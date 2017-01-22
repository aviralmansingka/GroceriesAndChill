from . import secrets
from flask import Flask
from flask import request
import json
import requests
import pandas as pd
import numpy as np
from scipy import spatial
import csv

import csv

app = Flask(__name__)

@app.route('/', methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):

        if not request.args.get("hub.verify_token") == secrets.VALIDATION_TOKEN:

            return "Verification token mismatch", 403

        return request.args["hub.challenge"], 200

    return "Hello world", 200

@app.route('/', methods=['POST'])
def webhook():
    data = request.get_json()

    sender_id = data['entry'][0]['messaging'][0]['sender']['id']
    text =  data['entry'][0]['messaging'][0]['message']['text']

    intent = text.split('\n')

    reply_text = build_reply(intent)

    send_message(sender_id, reply_text)

    return 'Thanks', 200

def send_message(rid, text):
    params = {
            "access_token": secrets.PAGE_ACCESS_TOKEN
            }
    headers = {
            "Content-Type": "application/json"
            }
    data = json.dumps({
        "recipient": {
            "id": rid
            },
        "message": {
            "text": text
            }
        })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)

def print_shopping_list(shopping_list, table):
    print_list = [get_col_name(item, table) for item in shopping_list if item > 0]
    return print_list

def build_reply(intent):
    """Construct replies based on the intent and the text sent by the user if needed"""

    unparsed_item_list = intent

    table = prepare_data()

    item_list = parse_list(unparsed_item_list, table)

    items_to_buy = getRecommendations(item_list, table, 4)

    return generate_reply_from_list(items_to_buy)

def parse_list(item_list, table):
    """TODO: Mahimna or Shubhang PLEASE FINISH THIS FUNCTION ALL YOUR PYTHON COMES HERE"""

    shopping_list = np.zeros((100,), dtype=np.int)

    my_elements = print_shopping_list(range(1,100), table)

    my_set = set(my_elements)

    for item in item_list:
        item = item.upper()
        if item in my_set:
            shopping_list[my_elements.index(item)] += 1
            print(item)

    return shopping_list

def prepare_data():
    """Sample function responsible for parsing and cleaning all the imported data"""
    table = pd.read_csv('./8451_recommender_table.csv')
    return table

def getRecommendations(shopping_list, table, k):
    """function takes as input the shopping list categories and recommends to the users new items"""

    non_zero = [index for (index, item) in enumerate(shopping_list) if item > 0]
    print(non_zero)

    entries = [table.loc[table.ix[:,index] > 0] for index in non_zero]
    entries = pd.concat(entries)

    my_data = pd.Series(shopping_list).ix[:]
    cosine_data = entries.ix[:,1:101].as_matrix()

    similarity_list = [(index, 1 - spatial.distance.cosine(my_data, item)) for (index, item) in enumerate(cosine_data)]
    similarity_list.sort(key=lambda x: x[1], reverse=True)
    similarity_list = similarity_list[:10]

    similarity_rows = [row for (row, similarity) in similarity_list]
    similarity_rows.sort()

    similarity_data = table.iloc[similarity_rows, :].as_matrix()
    summed_similarities = np.sum(similarity_data, axis=0)

    item_pairs = [(index, value) for (index,value) in enumerate(summed_similarities)]
    item_pairs.sort(key=lambda x: x[1], reverse=True)
    item_pairs = item_pairs[:k]

    print(item_pairs)

    return_list = [get_col_name(index, table).lower() for (index, score) in item_pairs]
    del return_list[0]

    return return_list

def get_col_name(index, table):
        return table.columns.values[index]

def generate_reply_from_list(items_to_buy):
    """Responsible for making more readable replies from shopping lists"""
    return 'Some items you should consider are ' + ', '.join(items_to_buy)
