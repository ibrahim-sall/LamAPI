# LamAPI
This repo contains our school's project aiming to build a Web service that compute GeoPose from user's infos
## lamar-benchmark

We provide a docker subdirectory with the dockerfile from lamar-benchmark and a [benchmark.md](docker/README.md) to set-up the server from distant image (that's the better solution for installation stability).

## API-geopose
In the first place you nedd to create a python environment:
```sh
conda create -n oscp_test
conda activate oscp_test
conda install -c anaconda requests
conda install -c anaconda flask
conda install -c anaconda pillow
```

You can now start the server: ``run-oscp-gpp-server.sh``. You can test whether the server is running by typing in your browser: http://localhost:8080/geopose.

And then start the client and execute a request ``run-oscp-gpp-client.sh``