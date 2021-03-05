from flask import Flask, request
from flask_cors import CORS
import json
import os
import pandas as pd
import datetime as dt


ENV = 'PROD'
app = Flask(__name__)
CORS(app)

if ENV == 'DEV':
	os.system("export FLASK_APP=app && export FLASK_ENV=development")
	hours = 0
else: hours = 8

# another place where building out can break ya/
prefix_map = {
    'EBAY':'EBAY',
    'GOOGLE':'GOOGLE',
    'SIDELINE':'SLS',
    'BIGCOMMERCE':'BC'
}

@app.route('/')
def index():

	# get refresh date
	with open('date.txt') as f:
		date = f.read()

	# check for picked picks
	with open('picked.json') as f:
		picked = json.load(f)

	data = pd.read_pickle('picklist.pkl')
	data['picked'] = data.app_id.map(picked).fillna(False)

	return {
		'data':json.loads(data.to_json(orient='records')),
		'date':date.split('.')[0]
	}

@app.route('/send', methods=['POST'])
def send():
	data = request.json
	picklist = pd.DataFrame(data)

	# store date
	with open('date.txt','w') as f:
		f.write(f'{dt.datetime.now()-dt.timedelta(hours=hours)}')

	# fuck with pickle
	picklist['app_id'] = picklist.id + ' ' + picklist.sku
	picklist['tag'] = picklist.channel.map(prefix_map) + ' ' + picklist.id
	picklist['app_name'] = (picklist.name.str.title() + ' ' + picklist.year.fillna('')).str.strip(' ')
	picklist['app_color'] = picklist[['color','alt_color']].apply(lambda x: ', aka '.join(x.dropna()),axis=1)
	picklist['app_num_other_items'] = picklist.num_items.apply(lambda x: x-1 if x>1 else 0)
	picklist.to_pickle('picklist.pkl')

	return 'success'

@app.route('/pick', methods=['PUT'])
def pick():
	app_id = request.args['app_id']

	# store state info
	with open('picked.json') as f:
		picked = json.load(f)
	if app_id in picked:
		picked[app_id] = not picked[app_id]
	else:
		picked[app_id] = True
	with open('picked.json','w') as f:
		json.dump(picked,f)

	return json.dumps(picked[app_id])

	




if __name__ == '__main__':
    app.run(debug=(ENV=='DEV'))