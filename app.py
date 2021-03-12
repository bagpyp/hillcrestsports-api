import datetime as dt
import json
import os
import pandas as pd
import psycopg2
from flask import Flask, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

ENV = 'PROD'

app = Flask(__name__)
CORS(app)

if ENV == 'DEV':
	os.system("export FLASK_APP=app && export FLASK_ENV=development")
	hours = 0
	if 'DATABASE_URL' not in os.environ:
		from subprocess import PIPE, Popen
		os.environ['DATABASE_URL'] = Popen('echo $(heroku config:get DATABASE_URL)',shell=True, stdout=PIPE).stdout.read().decode("utf-8")[:-1]
else: 
	hours = 8
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ['DATABASE_URL']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Date(db.Model):
	__tablename__ = 'date'
	_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	date = db.Column(db.String(50), nullable=False, unique=True)

	def __init__(self, date):
		self.date = date

	def text(self):
		return self.date
	
class Picklist(db.Model):
	__tablename__ = 'picklist'
	_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	BRAND = db.Column(db.String(200))
	CAT = db.Column(db.String(500))
	app_color = db.Column(db.String, nullable=True)
	app_id = db.Column(db.String(50), nullable=False)
	app_name = db.Column(db.String(500))
	app_num_other_items = db.Column(db.Integer)
	created_date = db.Column(db.BigInteger)
	qty = db.Column(db.Integer)
	qty0 = db.Column(db.Integer)
	size = db.Column(db.String(20), nullable=True)
	sku = db.Column(db.String(50))
	tag = db.Column(db.String(50))
	v_image_url = db.Column(db.String(5000))

	def __init__(self, data):
		self.created_date = data['created_date']
		self.qty = data['qty']
		self.sku = data['sku']
		self.CAT = data['CAT']
		self.BRAND = data['BRAND']
		self.size = data['size']
		self.v_image_url = data['v_image_url']
		self.qty0 = data['qty0']
		self.app_id = data['app_id']
		self.tag = data['tag']
		self.app_name = data['app_name']
		self.app_color = data['app_color']
		self.app_num_other_items = data['app_num_other_items']

	def json(self):
		return {
			'created_date':self.created_date,
			'qty':self.qty,
			'sku':self.sku,
			'CAT':self.CAT,
			'BRAND':self.BRAND,
			'size':self.size,
			'v_image_url':self.v_image_url,
			'qty0':self.qty0,
			'app_id':self.app_id,
			'tag':self.tag,
			'app_name':self.app_name,
			'app_color':self.app_color,
			'app_num_other_items':self.app_num_other_items
		}

class Picked(db.Model):
	__tablename__ = 'picked'
	_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
	app_id = db.Column(db.String(20), nullable=False)
	picked = db.Column(db.Boolean, default = False)

	def __init__(self, app_id, picked):
		self.app_id = app_id
		self.picked = picked

	def dictionary(self):
		return {self.app_id:self.picked}

@app.route('/picklist',  methods=['GET','POST'])
def picklist():
	if request.method == 'GET':

		date = db.session.query(Date).first().text().split('.')[0].replace(' ','T')
		data = sorted([_.json() for _ in db.session.query(Picklist).all()], key = lambda x: -x['created_date'])
		picked = {k:v for p in [_.dictionary() for _ in db.session.query(Picked).all()] for k,v in p.items()}
		data = pd.DataFrame(data)
		data['picked'] = data.app_id.map(picked).fillna(False)
		data = json.loads(data.to_json(orient='records'))

		return {
			'data':data,
			'date':date
		}

	elif request.method == 'POST':

		data = request.json

		stored_app_ids = [_[0] for _ in db.session.query(Picklist.app_id).all()]
		incoming_app_ids = [_['app_id'] for _ in data]

		# delete dangling 'picked' fields
		for p in db.session.query(Picked).filter(~(Picked.app_id.in_(incoming_app_ids))).all():
			db.session.delete(p)
		db.session.commit()

		# add new Picks to DB
		for d in data:
			if d['app_id'] not in stored_app_ids:
				db.session.add(Picklist(d))

		# reomve old Picks
		for app_id in stored_app_ids:
			if app_id not in incoming_app_ids:
				db.session.query(Picklist).filter(Picklist.app_id == app_id).delete()

		# replace date value with current time
		db.session.query(Date).delete()
		db.session.add(Date(str(dt.datetime.now()-dt.timedelta(hours=hours))))
		db.session.commit()

		return 'OK'

@app.route('/picklist/pick', methods=['PUT'])
def picklist_pick():
	app_id = request.args['app_id']

	stored_app_ids = [_[0] for _ in db.session.query(Picked.app_id).all()]

	if app_id in stored_app_ids:
		pick = db.session.query(Picked).filter(Picked.app_id==app_id).first()
		pick.picked = not pick.picked
		res = pick.picked
	else:
		db.session.add(Picked(app_id,True))
		res = True

	db.session.commit()

	return json.dumps(res)

if __name__ == '__main__':
    app.run(debug=(ENV=='DEV'))