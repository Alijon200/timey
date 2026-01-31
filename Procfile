web: gunicorn timey.wsgi
web: python manage.py migrate && ./.venv/bin/gunicorn timey.wsgi:application --bind 0.0.0.0:$PORT


