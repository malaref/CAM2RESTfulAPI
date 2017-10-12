"""The routes accepted by the RESTful API

This is the module that contains the routes accepted
by the API. 
the app's cache and configuration. Also, it includes
the clients used by other modules like the database
client and the storage client. Generally, this includes
all the global (shared) objects (Singleton pattern).

"""

from CAM2RESTfulAPI import app, database_client, storage_client, load_user

from flask import request,  jsonify, send_file, after_this_request, render_template, redirect, abort
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from clients.job_client import JobClient

import os

# NOTE May move this method to the DatabaseClient class
def _get_submission(username, submission_id):
	'''Helper function to get the submission from the database by the username and the submission id'''
	return database_client.query_db('SELECT * FROM Submissions WHERE username=? AND submission_id=?', args=(username, submission_id), one=True)

@app.route('/', methods=['GET'])
def root():
	'''Redirects to the dashboard'''
	return redirect('/dashboard/')

@app.route('/authenticate/', methods=['GET'])
def authenticate():
	'''Renders the authorization page'''
	return render_template('authenticate.html')

@app.route('/dashboard/', methods=['GET'])
@login_required
def dashboard():
	'''Renders the HTML dashboard interface'''
	username = str(current_user.id)
	return render_template('dashboard.html', submissions=database_client.query_db('SELECT * FROM Submissions WHERE username=?', args=(username,)))

@app.route('/submit/', methods=['POST'])
@login_required
def submit():
	'''Accepts an authenticated request. Passes the needed parameter to the back-end to start a new job'''
	username = str(current_user.id)
	submission_id = request.form['submission_id']
	if not request.files.has_key('conf'):
		return 'No configuration file'
	elif not request.files.has_key('analyzer'):
		return 'No analyzer script'
	conf = request.files['conf']
	analyzer = request.files['analyzer']
	if conf.filename == '':
		return 'No selected configuration file'
	elif analyzer.filename == '':
		return 'No selected analyzer script'
	elif not conf.filename.endswith('.json'):
		return 'The configuration file must be a JSON file'
	elif not analyzer.filename.endswith('.py'):
		return 'The analyzer script must be a Python script'
	if _get_submission(username, submission_id) is not None:
		return 'Cannot have two submissions with the same "submission_id"'
	JobClient.submit_job(username, submission_id, conf, analyzer)
	return 'Job submitted!'

@app.route('/status/', methods=['POST'])
@login_required
def status():
	'''Accepts an authenticated request. Returns the status of a given submission, provided it exists'''
	username = str(current_user.id)
	submission_id = request.form['submission_id']
	submission = _get_submission(username, submission_id)
	not_found = 'Could not find a submission with "submission_id" = "{}"'.format(submission_id)
	
	if submission is None:
		return not_found
	return jsonify(submission)

@app.route('/terminate/', methods=['POST'])
@login_required
def terminate():
	'''Accepts an authenticated request. Terminates the given submission, provided it is running'''
	username = str(current_user.id)
	submission_id = request.form['submission_id']
	submission = _get_submission(username, submission_id)
	terminated = 'Submission with "submission_id" = "{}" terminated!'.format(submission_id)
	not_running = 'Submission with "submission_id" = "{}" is not running!'.format(submission_id)
	not_found = 'Could not find a submission with "submission_id" = "{}"'.format(submission_id)
	
	if submission is None:
		return not_found
	if submission['status'] == 'RUNNING' and JobClient.terminate_job(username, submission_id):
		return terminated
	return not_running

@app.route('/download/', methods=['POST'])
@login_required
def download():
	'''Accepts an authenticated request. Sends the results of the submission back to the user, provided it is completed'''
	username = str(current_user.id)
	submission_id = request.form['submission_id']
	submission = _get_submission(username, submission_id)
	not_found = 'Could not find a submission with "submission_id" = "{}"'.format(submission_id)
	running = 'Submission with "submission_id" = "{}" is running!'.format(submission_id)
	
	if submission is None:
		return not_found
	elif submission['status'] == 'RUNNING':
		return running
	file_name = storage_client.prepare_result_as_zip_file(username, submission_id)
	
	@after_this_request
	def remove_file(response):
		os.remove(file_name)
		return response
	return send_file(file_name)

@app.route('/delete/', methods=['POST'])
@login_required
def delete():
	'''Accepts an authenticated request. Deletes a submission and is results, provided it exists'''
	username = str(current_user.id)
	submission_id = request.form['submission_id']
	submission = _get_submission(username, submission_id)
	not_found = 'Could not find a submission with "submission_id" = "{}"'.format(submission_id)
	running = 'Submission with "submission_id" = "{}" is running!'.format(submission_id)
	deleted = 'Submission with "submission_id" = "{}" deleted!'.format(submission_id)
	
	if submission is None:
		return not_found
	elif submission['status'] == 'RUNNING':
		return running
	
	database_client.update_db('DELETE FROM Submissions WHERE submission_id=?', args=(submission_id,))
	storage_client.delete_result(username, submission_id)
	return deleted

@app.route('/submissions/', methods=['POST'])
@login_required
def submissions():
	'''Accepts an authenticated request. Returns a summery of a user's jobs'''
	username = str(current_user.id)
	
	submissions = database_client.query_db('SELECT submission_id, status FROM Submissions WHERE username=?', args=(username,))
	return jsonify(submissions)

@app.route('/login/', methods=['POST'])
def login():
	'''Logs a user in'''
	username = request.form['username']
	password = request.form['password']
	missing = 'Authentication fields missing'
	not_found = 'Could not find a user with "username" = "{}"!'.format(username)
	fail = 'Authentication failed!'
	success = 'Logged in successfully!'
	
	if username is None or password is None:
		return missing
	user = database_client.query_db('SELECT * FROM Users WHERE username=?', args=(username,), one=True)
	if user is None:
		return not_found
	if not check_password_hash(user['password_hash'], password):
		return fail
	login_user(load_user(unicode(username)))
	return success

@app.route('/logout/', methods=['POST'])
@login_required
def logout():
	'''Logs a user out'''
	success = 'Logged out successfully!'
	
	logout_user()
	return success

@app.route('/register/', methods=['POST'])
def register():
	'''Registers a new user'''
	username = request.form['username']
	password = request.form['password']
	registered = 'A user with "username" = "{}" added!'.format(username)
	exists = 'A user with "username" = "{}" already exists!'.format(username)
	
	if database_client.query_db('SELECT * FROM Users WHERE username=?', args=(username,), one=True) is None:
		database_client.update_db('INSERT INTO Users(username, password_hash) VALUES (?, ?);', args=(username, generate_password_hash(password)))
		return registered
	return exists

@app.route('/unregister/', methods=['POST'])
@login_required
def unregister():
	'''Unregister a user from the system'''
	username = str(current_user.id)
	unregistered = 'The user with "username" = "{}" has been removed!'.format(username)
	not_found = 'Could not find a user with "username" = "{}"!'.format(username)
	running = 'Cannot unregister a user with running submission(s)!'.format(username)
	
	if database_client.query_db('SELECT * FROM Users WHERE username=?', args=(username,), one=True) is None:
		return not_found
	if database_client.query_db('SELECT * FROM Submissions WHERE username=? AND status=?', args=(username, 'RUNNING'), one=True) is not None:
		return running
	database_client.update_db('DELETE FROM Submissions WHERE username=?', args=(username,))
	database_client.update_db('DELETE FROM Users WHERE username=?', args=(username,))
	storage_client.delete_user(username)
	return unregistered
