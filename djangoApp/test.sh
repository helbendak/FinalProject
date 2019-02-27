#!/bin/bash
coverage run --source=. manage.py test -v 2 && coverage html && coverage report