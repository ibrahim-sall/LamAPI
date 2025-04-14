set -e

pip install --no-cache-dir flask requests pillow tqdm numpy pyproj laspy flask_swagger_ui docker

exec python3 demo_server.py