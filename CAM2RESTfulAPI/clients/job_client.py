"""Jobs manager

This module provides client to manage the
jobs. It can submit/terminate a job. Also, it
takes care of removing finished jobs from
the memory.

"""

from CAM2RESTfulAPI import jobs, database_client, master_url, namenode_url

import tempfile, os, json, subprocess, threading

class JobClient(object):
	'''A class to mange the jobs (creation, deletion, monitoring, etc.)'''
	
	@classmethod
	def submit_job(cls, username, submission_id, json_conf, analyzer_script):
		'''Class method to submit a job and keeping tracking of it'''
		jobs.append(cls(username, submission_id, json_conf, analyzer_script))
	
	@classmethod
	def terminate_job(cls, username, submission_id):
		'''Class method to terminate a running job, provided it exists'''
		for job in jobs:
			if job.username == username and job.submission_id == submission_id:
				return job.terminate()
		return False
	
	def __init__(self, username, submission_id, conf, analyzer_script):
		'''Creates a new instance to manage one job. It submits to Spark and monitors it'''
		# Adding attributes
		self.username = username
		self.submission_id = submission_id
		# Create temp files
		self._temp_directory = tempfile.mkdtemp()
		self._temp_conf_file_path = os.path.join(self._temp_directory, 'user_conf.json')
		self._temp_analyzer_script_path = os.path.join(self._temp_directory, 'user_analyzer.py')
		with open(self._temp_conf_file_path, 'w') as f:
			json.dump(conf, f, sort_keys=True, indent=4)
		analyzer_script.save(self._temp_analyzer_script_path)
		# Submit the job
		self._job = subprocess.Popen('exec CAM2DistributedBackend {0} {1} {2} {3} {4} {5}'.format(master_url, namenode_url, self.username, self.submission_id, self._temp_conf_file_path, self._temp_analyzer_script_path), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
		threading.Thread(target=self._handle_stdout).start()
		database_client.update_db('INSERT INTO Submissions(username, submission_id, status, stdout, stderr) VALUES (?, ?, ?, ?, ?);', args=(self.username, self.submission_id, 'RUNNING', 'Will be available upon completion/termination!', 'Will be available upon completion/termination!'))
	
	# TODO Make output available as it arrives
	def _handle_stdout(self):
		'''Internal method to monitor a submitted job and remove it upon completion'''
		stdout, stderr = self._job.communicate()
		self._finalize()
		database_client.update_db('UPDATE Submissions SET stdout=?, stderr=? WHERE username=? AND submission_id=?;', args=(stdout, stderr, self.username, self.submission_id))
		database_client.update_db('UPDATE Submissions SET status=? WHERE username=? AND submission_id=? AND status=?;', args=('COMPLETED', self.username, self.submission_id, 'RUNNING'))
		jobs.remove(self)
	
	def terminate(self):
		'''Terminates the job manages by the client instance'''
		if self._job.poll() is None:
			database_client.update_db('UPDATE Submissions SET status=? WHERE username=? AND submission_id=?;', args=('TERMINATED', self.username, self.submission_id))
			self._job.terminate()
			return True
		else:
			return False
	
	def _finalize(self):
		'''Internal method to clean up after the job is completed/terminated'''
		# Remove temp files
		os.remove(self._temp_conf_file_path)
		os.remove(self._temp_analyzer_script_path)
		os.rmdir(self._temp_directory)
