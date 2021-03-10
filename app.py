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

@app.route('/picklist')
def picklist():

	# get refresh date
	with open('picklist/date.txt') as f:
		date = f.read()

	# check for picked picks
	with open('picklist/picked.json') as f:
		picked = json.load(f)

	data = pd.read_pickle('picklist/picklist.pkl')
	data['picked'] = data.app_id.map(picked).fillna(False)

	return {
		'data':json.loads(data.to_json(orient='records')),
		'date':date.split('.')[0].replace(' ','T')
	}

@app.route('/picklist/send', methods=['POST'])
def picklist_send():
	data = request.json
	picklist = pd.DataFrame(data)

	# store date
	with open('picklist/date.txt','w') as f:
		f.write(f'{dt.datetime.now()-dt.timedelta(hours=hours)}')

	# fuck with pickle
	picklist['app_id'] = picklist.id + ' ' + picklist.sku
	picklist['tag'] = picklist.channel.map(prefix_map) + ' ' + picklist.id
	picklist['app_name'] = (picklist.name.str.title() + ' ' + picklist.year.fillna('')).str.strip(' ')
	picklist['app_color'] = picklist[['color','alt_color']].apply(lambda x: ', aka '.join(x.dropna()),axis=1)
	picklist['app_num_other_items'] = picklist.num_items.apply(lambda x: x-1 if x>1 else 0)
	picklist.to_pickle('picklist/picklist.pkl')

	return 'success'

@app.route('/picklist/pick', methods=['PUT'])
def picklist_pick():
	app_id = request.args['app_id']

	# store state info
	with open('picklist/picked.json') as f:
		picked = json.load(f)
	if app_id in picked:
		picked[app_id] = not picked[app_id]
	else:
		picked[app_id] = True
	with open('picklist/picked.json','w') as f:
		json.dump(picked,f)

	return json.dumps(picked[app_id])

	
@app.route('/reports')
def reports():
	# get refresh date
	with open('reports/date.txt') as f:
		date = f.read()
	data = pd.read_pickle('reports/report.pkl')

	return {
		'data':json.loads(data.to_json(orient='records')),
		'date':date.split('.')[0].replace(' ','T')
	}


@app.route('/reports/send', methods=['POST'])
def reports_send():
	data = request.json
	reports = pd.DataFrame(data)

	# store date
	with open('reports/date.txt','w') as f:
		f.write(f'{dt.datetime.now()-dt.timedelta(hours=hours)}')

	# fuck with pickle
	reports.to_pickle('reports/report.pkl')

	return 'success'


if __name__ == '__main__':
    app.run(debug=(ENV=='DEV'))