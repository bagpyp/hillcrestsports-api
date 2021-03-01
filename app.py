from flask import Flask, request
from flask_cors import CORS
import json
import os
import pandas as pd

app = Flask(__name__)
CORS(app)

@app_route('/')
def index():
	return 'Hello, World!'
