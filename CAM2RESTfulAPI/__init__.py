"""The root module of the RESTful API

This is the module that contains the Flask's app,
the app's cache and configuration. Also, it includes
the clients used by other modules like the database
client and the storage client. Generally, this includes
all the global (shared) objects (Singleton pattern).

"""

from flask import Flask, request, redirect, abort
from flask_login import LoginManager, UserMixin
from clients.storage_client import StorageClient
from clients.database_client import DatabaseClient
from collections import deque
import os, json, atexit

app = Flask(__name__)
app.secret_key = 'some_secret'

# Cache
cache_path = os.path.join(os.path.expanduser('~'), '.CAM2RESTfulAPI')
if not os.path.exists(cache_path):
	os.makedirs(cache_path)

# Configuration
config_path = os.path.join(cache_path, 'config.json')
if not os.path.exists(config_path):
	master_url = raw_input('Spark master URL: ')
	namenode_url = raw_input('HDFS namenode URL: ')
	with open(config_path, 'w') as f:
		config = json.dump({'master_url': master_url, 'namenode_url':namenode_url}, f)
else:
	with open(config_path, 'r') as f:
		config = json.load(f)
	master_url = config['master_url']
	namenode_url = config['namenode_url']

# Database
database_path = os.path.join(cache_path, 'database.db')
if not os.path.exists(database_path):
	with app.open_resource('db.sql') as schema:
		import sqlite3
		conn = sqlite3.connect(database_path)
		conn.executescript(schema.read())
		from werkzeug.security import generate_password_hash
		conn.execute('INSERT INTO Users(username, password_hash) VALUES ("admin", ?);', (generate_password_hash(raw_input('Admin password: ')),))
		conn.commit()
		conn.close()

# The collection that includes all the running jobs
jobs = deque()

# Initializing the storage client
storage_client = StorageClient(namenode_url)

# Initializing the database client
database_client = DatabaseClient(database_path)
atexit.register(database_client.close_connection)

# Flask-Login setup
login_manager = LoginManager()
login_manager.init_app(app)
@login_manager.user_loader
def load_user(user_id):
	'''Loads a user from a user_id as needed by Flask-Login'''
	if database_client.query_db('SELECT * FROM Users WHERE username=?', args=(str(user_id),), one=True) is not None:
		user = UserMixin()
		user.id = user_id
		return user
	return None
@login_manager.unauthorized_handler
def unauthorized():
	'''Handler function to be called by Flask-Login when the @login_required check fails'''
	if request.user_agent.browser is None:
		return "Unauthorized access!\nPlease login with valid credentials and try again!"
	return redirect('/authenticate/')

# Including the routes
import routes
