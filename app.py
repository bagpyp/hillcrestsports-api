from flask import Flask, request
from flask_cors import CORS
import json
import os
import pandas as pd

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
	data = pd.read_pickle('picklist.pkl')
	return data.to_json()

@app.route('/send', methods=['GET','POST'])
def send():
	data = request.json
	picklist = pd.DataFrame(data)
	picklist.to_pickle('picklist.pkl')
	return picklist.to_json()
