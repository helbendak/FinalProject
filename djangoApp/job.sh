#!/usr/bin/env
python manage.py migrate && python manage.py migrate --run-syncdb && python manage.py createsuperuser && python manage.py runserver