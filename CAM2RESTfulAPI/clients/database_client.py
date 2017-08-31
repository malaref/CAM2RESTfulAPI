"""Database manager

This module provides a database class
for all class interactions

Based on the Flask SQLite3 pattern from
http://flask.pocoo.org/docs/0.12/patterns/sqlite3/

"""

import sqlite3, threading

class DatabaseClient(object):
	'''A thread-safe class to provide all database-related functionalities'''
	
	def __init__(self, database_path):
		'''Create a database connection and bind it a dict factory'''
		self._db = sqlite3.connect(database_path, check_same_thread=False)
		self._db.row_factory = DatabaseClient._dict_factory
		self.lock = threading.Lock()
		self.closed = False

	def update_db(self, query, args=()):
		'''Update the database with a new query and commit the changes'''
		assert not self.closed
		with self.lock:
			self._db.execute(query, args)
			self._db.commit()

	def query_db(self, query, args=(), one=False):
		'''Query the database for information and returns the results'''
		assert not self.closed
		with self.lock:
			cursor = self._db.execute(query, args)
			if one:
				return cursor.fetchone()
			else:
				return cursor.fetchall()
	
	def close_connection(self):
		'''Closes the database connection and ensures no other calls are allowed'''
		self.closed = True
		self._db.close()
		
	@staticmethod
	def _dict_factory(cursor, row):
		'''Helper factory method to transform the results to dicts'''
		d = {}
		for idx, col in enumerate(cursor.description):
			d[col[0]] = row[idx]
		return d
