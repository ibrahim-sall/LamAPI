# Instructions pour utiliser Docker avec le volume SMB
## Prérequis

- Docker installé sur votre système
- Accès au partage SMB
- `cifs-utils` installé pour monter le partage SMB

## Étapes

### 1. Télécharger l'image Docker

Téléchargez l'image Docker en utilisant l'ID ou le nom de l'image.

```sh
docker pull ghcr.io/microsoft/lamar-benchmark/lamar:latest
```

Remplacez `<docker_image_id>` par l'ID ou le nom de votre image Docker.

### 2. Créer le point de montage local

Créez un répertoire local pour monter le partage SMB.

```sh
sudo mkdir -p /mnt/lamas
```

### 3. Monter le partage SMB

Montez le partage SMB en utilisant `mount.cifs`.

```sh
sudo mount.cifs //store-echange/formationtemp/tsi/Lamas /mnt/lamas -o username=,password=,workgroup=ENSG1
```

### 4. Vérifier le montage

Assurez-vous que le partage est monté correctement.

```sh
ls /mnt/lamas
```

### 5. Définir les variables d'environnement

Définissez les variables d'environnement nécessaires. Si possible dans ~/.bashrc (puis source pour le relancer).

```sh
export DATA_DIR=/mnt/lamas
export DOCKER_IMAGE_ID=
export DOCKER_RUN="docker run --runtime=nvidia --shm-size=26G --gpus all -v /mnt/lamas:/mnt/lamas -v output_volume:/output -e DATA_DIR=$DATA_DIR -e MPLCONFIGDIR=$DATA_DIR/matplotlib_config -e OUTPUT_DIR=/output $DOCKER_IMAGE_ID"
```

### 6. Monter le volume de sortie pour le docker

```sh
docker volume create output_volume 
```

### 7. Exécuter la commande Docker

```sh
$DOCKER_RUN python3 -m lamar.run --scene HGE --ref_id map --query_id query_phone --retrieval fusion --feature superpoint --matcher superglue --capture $DATA_DIR --outputs /output
```

# Adresse du serveur

```sh
ssh formation@172.31.58.183
```