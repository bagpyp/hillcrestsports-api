from flask import Flask, request
from flask_cors import CORS
import json
import os
import pandas as pd


ENV = 'PROD'
app = Flask(__name__)
CORS(app)

if ENV == 'DEV':
	os.system("export FLASK_APP=app && export FLASK_ENV=development")

prefix_map = {
    'EBAY':'EBAY',
    'GOOGLE':'GOOGLE',
    'SIDELINE':'SLS',
    'BIGCOMMERCE':'BC'
}

@app.route('/')
def index():
	data = pd.read_pickle('picklist.pkl')
	return data.to_json(orient='records')

@app.route('/send', methods=['POST'])
def send():
	data = request.json
	picklist = pd.DataFrame(data)

	# fuck with pickle here:
	picklist['app_id'] = picklist.id + ' ' + picklist.sku
	picklist['tag'] = picklist.channel.map(prefix_map) + ' ' + picklist.id
	picklist['app_name'] = (picklist.name.str.title() + ' ' + picklist.year).str.strip(' ')
	picklist['app_color'] = picklist[['color','alt_color']].apply(lambda x: ', aka '.join(x.dropna()),axis=1)
	picklist['app_num_other_items'] = picklist.num_items.apply(lambda x: x-1 if x>1 else 0)

	picklist.to_pickle('picklist.pkl')
	return 'success'

# @app.route('/delete', methods=['DELETE'])

if __name__ == '__main__':
    app.run(debug=(ENV=='DEV'))