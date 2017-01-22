from . import secrets
from flask import Flask
from flask import request
import json
import requests
import pandas as pd
import numpy as np
from scipy import spatial

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

def build_reply(intent):
    """Construct replies based on the intent and the text sent by the user if needed"""

    unparsed_item_list = intent

    item_list = parse_list(unparsed_item_list)

    table = prepare_data()

    items_to_buy = getRecommendations(item_list, table, 4)

    return generate_reply_from_list(items_to_buy)


def binSearch(str, read_data):
    str = str.upper();
    start = 1
    end = len(read_data) - 1
    while(start <= end):
        mid = (start + end)/2
        mid_element = read_data[mid][5];
        if(str == mid_element):
            return read_data[mid][4]
        elif(str < mid_element):
            end = mid - 1
        else:
            start = mid + 1

    return -1

def read():
    csv_file = "categories.csv"
    lines = csv.reader(open(csv_file,"rb"))

    read_data = list(lines)
    return read_data


def parse_list(item_list):
    """TODO: Mahimna or Shubhang PLEASE FINISH THIS FUNCTION ALL YOUR PYTHON COMES HERE"""

    shopping_list = np.zeros((101,), dtype=np.int)
    dictionary = {"":1,"BASKET_ID ":2,"BABY HBC":3,"BACON":4,"BAG SNACKS":5,"BAKED BREAD/BUNS/ROLLS":6,"BAKED SWEET GOODS":7,"BAKING MIXES":8,"BAKING NEEDS":9,"BATH TISSUES":10,"BATTERIES":11,"BEANS - CANNED GLASS & MW":12,"BEEF":13,"BREAD":14,"BREAKFAST SAUSAGE/SANDWICHES":15,"BROOMS AND MOPS":16,"BUTTER":17,"CAKES":18,"CANDY - CHECKLANE":19,"CANDY - PACKAGED":20,"CANNED JUICES":21,"CANNED MILK":22,"CAT FOOD":23,"CHEESE":24,"CHEESES":25,"CHICKEN":26,"CHICKEN/POULTRY":27,"CHIPS&SNACKS":28,"CIGARETTES":29,"COFFEE FILTERS":30,"COLD CEREAL":31,"CONDIMENTS/SAUCES":32,"CONVENIENT BRKFST/WHLSM SNACKS":33,"COOKIES/CONES":34,"CRACKERS/MISC BKD FD":35,"DELI MEATS":36,"DINNER MXS:DRY":37,"DISHWASH DETERGENTS":38,"DRY BN/VEG/POTATO/RICE":39,"DRY MIX DESSERTS":40,"DRY NOODLES/PASTA":41,"DRY SAUCES/GRAVY":42,"EASTER":43,"EGGS":44,"ELECTRICAL SUPPPLIES":45,"ETHNIC PERSONAL CARE":46,"FEMININE HYGIENE":47,"FLUID MILK PRODUCTS":48,"FROZEN MEAT":49,"FROZEN PIE/DESSERTS":50,"FROZEN PIZZA":51,"FRUIT - SHELF STABLE":52,"FRZN BREAKFAST FOODS":53,"FRZN FRUITS":54,"FRZN MEAT/MEAT DINNERS":55,"FRZN NOVELTIES/WTR ICE":56,"FRZN POTATOES":57,"FRZN VEGETABLE/VEG DSH":58,"GRAPES":59,"GREETING CARDS/WRAP/PARTY SPLY":60,"HAIR CARE PRODUCTS":61,"HISPANIC":62,"HOT CEREAL":63,"HOT DOGS":64,"ICE CREAM/MILK/SHERBTS":65,"LAUNDRY ADDITIVES":66,"LAUNDRY DETERGENTS":67,"LUNCHMEAT":68,"MEAT - SHELF STABLE":69,"MELONS":70,"MILK BY-PRODUCTS":71,"MISC. DAIRY":72,"MOLASSES/SYRUP/PANCAKE MIXS":73,"ONIONS":74,"ORAL HYGIENE PRODUCTS":75,"ORGANICS FRUIT & VEGETABLES":76,"PAPER HOUSEWARES":77,"PAPER TOWELS":78,"PASTA SAUCE":79,"PEPPERS-ALL":80,"PNT BTR/JELLY/JAMS":81,"POTATOES":82,"PREPARED FOOD":83,"REFRGRATD JUICES/DRNKS":84,"REFRIGERATES":85,"SALAD MIX":86,"SEAFOOD - FROZEN":87,"SEAFOOD - SHELF STABLE":88,"SOAP - LIQUID & BAR":89,"SOFT DRINKS":90,"SOUP":91,"SUGARS/SWEETNERS":92,"TEAS":93,"TOBACCO OTHER":94,"TOMATOES":95,"TROPICAL FRUIT":96,"UNKNOWN":97,"VEGETABLES - ALL OTHERS":98,"VEGETABLES - SHELF STABLE":99,"VEGETABLES SALAD":100,"YOGURT":101}

    dataset = read()
    for i in range(len(item_list)):
        sub_category = binSearch(item_list,dataset)
        if dictionary.has_key(sub_category):
            shopping_list[dictionary[sub_category] - 1] += 1
        else:
            shopping_list[0] += 1

    
'''
    shopping_list[7] = 3
    shopping_list[14] = 4
    shopping_list[22] = 4
    shopping_list[28] = 5
'''
    return shopping_list

def prepare_data():
    """Sample function responsible for parsing and cleaning all the imported data"""
    table = pd.read_csv('./8451_recommender_table.csv')
    return table

def getRecommendations(shopping_list, table, k):
    """function takes as input the shopping list categories and recommends to the users new items"""

    non_zero = [index for (index, item) in enumerate(shopping_list) if item > 0]

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
