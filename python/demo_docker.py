import os 
import docker


def command(data_dir, output_dir, scene, ref_id="map", query_id="query_phone", 
                       retrieval="fusion", feature="superpoint", matcher="superglue"):
    docker_run = os.getenv("DOCKER_RUN")
    if not docker_run:
        raise ValueError("DOCKER_RUN environment variable is not set.")
    
    command = [
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
    return docker_run, command

def run(docker_run: str, command: list):
    try:
        client = docker.from_env()
        full_command = " ".join(command)
        print(f"Running Docker container with command: {docker_run} {full_command}")
        container = client.containers.run(
            docker_run.split(" ")[2],
            full_command,
            runtime="nvidia",
            detach=True,
            remove=True,
            environment={
                "DATA_DIR": os.getenv("DATA_DIR"),
                "MPLCONFIGDIR": f"{os.getenv('DATA_DIR')}/matplotlib_config",
                "OUTPUT_DIR": "/output"
            },
            volumes={
                "/mnt/lamas": {"bind": "/mnt/lamas", "mode": "rw"},
                os.getenv("DATA_DIR"): {"bind": "/output", "mode": "rw"}
            },
            shm_size="26G",
            gpus="all"
        )
        logs = container.logs(stream=True)
        for log in logs:
            print(log.decode("utf-8").strip())
    except docker.errors.ContainerError as e:
        print(f"Container error: {e}")
    except docker.errors.ImageNotFound as e:
        print(f"Image not found: {e}")
    except docker.errors.APIError as e:
        print(f"Docker API error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")