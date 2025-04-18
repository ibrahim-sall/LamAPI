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

### 5. Monter le volume de sortie pour le docker

```sh
docker volume create output_volume 
```

### 6. Récupérer l'ID de l'image LaMAR

Remplacer dans le docker-compose la valeur de la variable d'environnement _DOCKER_IMAGE_ID_

```sh
docker images --quiet ghcr.io/microsoft/lamar-benchmark/lamar:latest 
```

### 7. Lancer le serveur 
C'est bon tout est maintenant en place pour faire tourner le serveur flask et ces dépendances. Placez vous à la racine du dépôt cloné et executez:
```sh
docker compose up --build
```
