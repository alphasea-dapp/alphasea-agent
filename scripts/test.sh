#!/bin/bash

coverage run -m unittest discover -v
coverage html -d /tmp/alphasea-agent/htmlcov
