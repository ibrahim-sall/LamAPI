#!/bin/bash
CUR_DIR=$(pwd)


# Set these variables:

CONFIG_PATH=$CUR_DIR/../data/seattle_vps.json #a remplacer


OUT_PATH=$CUR_DIR/../data/lamar/OUT

IMAGE_NAME="ghcr.io/microsoft/lamar-benchmark/lamar"
CONTAINER_NAME="lamar_container"


DOCKER_RUN="docker run --name=$CONTAINER_NAME --runtime=nvidia --shm-size=26G --gpus all -v $OUT_PATH:/output $OUT_PATH:/data"


# Vérifier si l'image existe déjà
if ! sudo docker images | grep -q "$IMAGE_NAME"; then
  echo "L'image Docker n'existe pas. Téléchargement de l'image..."
  sudo docker pull "$IMAGE_NAME"
else
  echo "L'image Docker existe déjà."
fi

python demo_server.py --config $CONFIG_PATH -output_path $OUT_PATH
