#!/bin/sh

export FLASK_APP=webserver.py
export FLASK_ENV=development

flask run --host=0.0.0.0 # make the server publically visible