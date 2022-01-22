#!/bin/bash

coverage run -m unittest discover -v -s tests -t .
exit_code=$?
coverage html -d /tmp/alphasea-agent/htmlcov

exit $exit_code
