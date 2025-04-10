#!/bin/bash
CUR_DIR=$(pwd)


# Set these variables:

IMAGE_NAME="ghcr.io/microsoft/lamar-benchmark/lamar"


DATA_DIR=/mnt/lamas/data

export DOCKER_RUN="docker run --runtime=nvidia --shm-size=26G --gpus all -v /mnt/lamas:/mnt/lamas -v $DATA_DIR:/output -e DATA_DIR=$DATA_DIR -e MPLCONFIGDIR=$DATA_DIR/matplotlib_config -e OUTPUT_DIR=/output $IMAGE_NAME"


# Vérifier si l'image existe 
if ! sudo docker images | grep -q "$IMAGE_NAME"; then
  echo "L'image Docker n'existe pas. Téléchargement de l'image..."
  sudo docker pull "$IMAGE_NAME"
else
  echo "L'image Docker existe déjà."
fi


python3 demo_server.py -output_path volume_output
