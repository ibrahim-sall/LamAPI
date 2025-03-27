import docker, os 

def start_docker():
    client = docker.from_env()
    try:
        container = client.containers.run("ubuntu:latest", "echo Docker running")
        return client, container
    except docker.errors.DockerException as e:
        return str(e)
    
    
def create_docker_volume(volume_name: str, client : bytes):
    try:
        #a améliorer
        client.volumes.create(name = 'OUT')
        print(f"Volume Docker {volume_name} créé.")
    except docker.errors.DockerException as e:
        print(e)
        return False
    return True

def set_environment_variables(data_dir: str):
    os.environ["DATA_DIR"] = data_dir
    os.environ["DOCKER_RUN"] = (
        f"docker run --runtime=nvidia --shm-size=26G --gpus all "
        f"-v {data_dir}:{data_dir} "
        f"-v output_volume:/output "
    )
    print(f"DATA_DIR={data_dir}")