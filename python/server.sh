#!/bin/bash
set -e

pip install --no-cache-dir flask requests pillow tqdm numpy pyproj laspy flask_swagger_ui docker celery redis

# Start Celery worker with the updated module path
celery -A server_func.celery_app.celery worker &

# Start Flask app with argparse arguments
exec python3 /app/demo_server.py --output_path=/output