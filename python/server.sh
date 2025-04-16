#!/bin/bash
set -e

pip install --no-cache-dir flask requests pillow tqdm numpy pyproj laspy flask_swagger_ui docker celery redis


celery -A server_func.celery_app.celery worker &

exec python3 /app/demo_server.py --output_path=/output