import os 
import subprocess


def create_docker_command_lamar(data_dir, output_dir, scene, ref_id="map", query_id="query_phone", 
                       retrieval="fusion", feature="superpoint", matcher="superglue"):
    docker_run = os.getenv("DOCKER_RUN")
    
    command = [
        docker_run, 
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