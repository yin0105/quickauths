web: gunicorn insurance:app
worker: celery -A insurance.routes.celery worker --loglevel=info