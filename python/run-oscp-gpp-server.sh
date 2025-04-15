#!/bin/bash
CUR_DIR=$(pwd)


# Set these variables:

IMAGE_NAME="ghcr.io/microsoft/lamar-benchmark/lamar"


DATA_DIR=/mnt/lamas/data


# Vérifier si l'image existe 
if ! sudo docker images | grep -q "$IMAGE_NAME"; then
  echo "L'image Docker n'existe pas. Téléchargement de l'image..."
  sudo docker pull "$IMAGE_NAME"
else
  echo "L'image Docker existe déjà."
fi


python3 demo_server.py -output_path /mnt/lamas/OUT
