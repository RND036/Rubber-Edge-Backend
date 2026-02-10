web: daphne -b 0.0.0.0 -p $PORT rubber_farm_api.asgi:application
worker: celery -A rubber_farm_api worker --loglevel=info
