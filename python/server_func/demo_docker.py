import os
import docker
import subprocess


def command(data_dir, output_dir, scene, ref_id="map", query_id="query_phone", 
                       retrieval="fusion", feature="superpoint", matcher="superglue"):
    docker_run = os.getenv("DOCKER_RUN")
    if not docker_run:
        raise ValueError("DOCKER_RUN environment variable is not set.")
    
    command = [
        "python3", "-m", "lamar.run",
        "--scene", scene,
        "--ref_id", ref_id,
        "--query_id", "query_phone",
        "--retrieval", retrieval,
        "--feature", feature,
        "--matcher", matcher,
        "--capture", data_dir,
        "--outputs", output_dir
    ]
    return docker_run, command

def run(docker_run: str, command: list):
    try:
        client = docker.from_env()
        full_command = " ".join(command)
        print(f"Running Docker container with command: {full_command}")

        image_id = os.getenv("DOCKER_IMAGE_ID")
        if not image_id:
            raise ValueError("DOCKER_IMAGE_ID environment variable is not set.")

        container = client.containers.run(
            image=image_id,
            command=full_command,
            detach=True,
            volumes={
                "/mnt/lamas": {"bind": "/mnt/lamas", "mode": "z"},
                "output_volume": {"bind": "/output", "mode": "rw"}
            },
            runtime="nvidia",
            shm_size="26G",
            environment={
                "DATA_DIR": os.getenv("DATA_DIR"),
                "MPLCONFIGDIR": f"{os.getenv('DATA_DIR')}/matplotlib_config",
                "OUTPUT_DIR": "/output"
            }
        )
        for log in container.logs(stream=True):
            print(log.decode("utf-8").strip())

        exit_status = container.wait()
        print(f"Container exited with status: {exit_status['StatusCode']}")

        container.remove()
        return exit_status['StatusCode']
    except docker.errors.ContainerError as e:
        print(f"Container error: {e}")
        raise
    except docker.errors.ImageNotFound as e:
        print(f"Image not found: {e}")
        raise
    except docker.errors.APIError as e:
        print(f"Docker API error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise
