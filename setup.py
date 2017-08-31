from setuptools import setup, find_packages

setup(
	name='CAM2RESTfulAPI',
	version='1.0-a0',
	packages=find_packages(),
	include_package_data=True,
	zip_safe=False,
	install_requires=[
		'flask',
		'hdfs',
		'CAM2DistributedBackend',
	],
	scripts=['bin/CAM2RESTfulAPI'],
) 
