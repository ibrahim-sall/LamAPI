#!/bin/bash
CUR_DIR=$(pwd)


# Set these variables:

CONFIG_PATH=$CUR_DIR/../data/seattle_vps.json #a remplacer


OUT_PATH=/mnt/lamas

IMAGE_NAME="ghcr.io/microsoft/lamar-benchmark/lamar"
VOLUME_NAME="data"

DATA_DIR=/mnt/lamas

export DOCKER_RUN="docker run --runtime=nvidia --shm-size=26G --gpus all -v /mnt/lamas:/mnt/lamas -v $OUT_PATH:/output -e DATA_DIR=$DATA_DIR -e MPLCONFIGDIR=$DATA_DIR/matplotlib_config -e OUTPUT_DIR=/output $IMAGE_NAME"
export DOCKER_RUN

# Vérifier si l'image existe 
if ! sudo docker images | grep -q "$IMAGE_NAME"; then
  echo "L'image Docker n'existe pas. Téléchargement de l'image..."
  sudo docker pull "$IMAGE_NAME"
else
  echo "L'image Docker existe déjà."
fi


python3 demo_server.py --config $CONFIG_PATH -output_path $OUT_PATH
