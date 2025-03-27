import docker 

def start_docker():
    client = docker.from_env()
    try:
        container = client.containers.run("ubuntu:latest", "echo Docker running")
        return container
    except docker.errors.DockerException as e:
        return str(e)
    
