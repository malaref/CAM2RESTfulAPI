# CAM2RESTfulAPI
A RESTful API for the [CAM2DistributedBackend](https://github.com/muhammad-alaref/CAM2DistributedBackend) project using Flask.

## Requirements

### [CAM2DistributedBackend](https://github.com/muhammad-alaref/CAM2DistributedBackend)
  
**>> The RESTful API should be installed and run on one node. Preferably, the same node as the Spark master daemon and the HDFS namenode daemon (the _manager_ node).**

## Installation

Using [pip](https://pypi.python.org/pypi/pip):
```shell
pip install git+https://github.com/muhammad-alaref/CAM2RESTfulAPI
```

## Start the server

One simple command:
```shell
CAM2RESTfulAPI
```

Note that this command runs the Flask [built-in server](http://flask.pocoo.org/docs/latest/server/) which is fine for small loads (small number of users and requests) but probably not suitable for high production loads. For better deployment options, check [this link](http://flask.pocoo.org/docs/latest/deploying/).

The first time the server starts it will prompt for:
* **Spark master URL** and **HDFS namenode URL:** In case of the preferable setup of running on the _manager_ node:
  ```
  Spark master URL: spark://localhost:7077
  HDFS namenode URL: http://localhost:50070
  ```
* **Admin password:** The password for the admin account. For now, this is just the first user of the system (no special permissions granted).

## Usage

The recommended way is to use the [Requests CLI](https://github.com/muhammad-alaref/CAM2RequestsCLI) project or the built-in HTML+CSS+JS browser-based interface.  
Alternatively, as a RESTful API, it will respond to direct `GET`s and `POST`s by any custom application written in any language or even tools like [cURL](https://curl.haxx.se/) and [Postman](https://www.getpostman.com/).
