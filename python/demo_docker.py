import docker, os 
import subprocess

def start_docker():
    client = docker.from_env()
    try:
        container = client.containers.run("ghcr.io/microsoft/lamar-benchmark/lamar:latest", "echo Docker running")
        return container
    except docker.errors.DockerException as e:
        return str(e)


def set_environment_variables(data_dir: str, docker_image_id: str):
    # Définir les variables d'environnement
    os.environ["DATA_DIR"] = data_dir
    os.environ["DOCKER_IMAGE_ID"] = docker_image_id
    os.environ["DOCKER_RUN"] = (
        f"docker run --runtime=nvidia --shm-size=26G --gpus all "
        f"-v {data_dir}:{data_dir} "
        f"-v output_volume:/output "
        f"-e DATA_DIR=$DATA_DIR "
        f"-e MPLCONFIGDIR=$DATA_DIR/matplotlib_config "
        f"-e OUTPUT_DIR=/output "
        f"$DOCKER_IMAGE_ID"
    )
    
    # Affichage pour vérifier les variables
    print(f"DATA_DIR={data_dir}")
    print(f"DOCKER_IMAGE_ID={docker_image_id}")
    print(f"DOCKER_RUN={os.environ['DOCKER_RUN']}")

def create_docker_command_lamar(data_dir, output_dir, scene, ref_id="map", query_id="query_phone", 
                       retrieval="fusion", feature="superpoint", matcher="superglue"):
    
    command = [
        "$DOCKER_RUN", 
        "python3", "-m", "lamar.run",
        "--scene", scene,
        "--ref_id", ref_id,
        "--query_id", query_id,
        "--retrieval", retrieval,
        "--feature", feature,
        "--matcher", matcher,
        "--capture", data_dir,
        "--outputs", output_dir
    ]
    return command

def run_docker_command(command:list):
    try:
        # Exécuter la commande Docker
        print(f"Exécution de la commande: {' '.join(command)}")
        subprocess.run(command, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Erreur lors de l'exécution de la commande Docker: {e}")
    except Exception as e:
        print(f"Erreur inattendue: {e}")