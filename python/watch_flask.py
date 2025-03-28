import os
import subprocess
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import signal
import socket

class RestartOnChangeHandler(FileSystemEventHandler):
    def __init__(self, command, exclude_dirs, port):
        self.command = command
        self.exclude_dirs = exclude_dirs
        self.port = port
        self.process = None
        self.start_process()

    def is_port_in_use(self, port):
        """Vérifie si le port est déjà utilisé."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            return s.connect_ex(('localhost', port)) == 0

    def start_process(self):
        # Vérifie si le port est déjà utilisé
        if self.is_port_in_use(self.port):
            print(f"Le port {self.port} est déjà utilisé. Arrêtez le programme en cours avant de continuer.")
            return

        # Terminer le processus existant s'il est en cours d'exécution
        if self.process and self.process.poll() is None:
            print("Arrêt du serveur Flask existant...")
            self.process.terminate()
            self.process.wait()

        print("Démarrage du serveur Flask...")
        self.process = subprocess.Popen(self.command, shell=True, preexec_fn=os.setsid)

    def on_any_event(self, event):
        # Ignore les événements dans les répertoires exclus
        if any(excluded in event.src_path for excluded in self.exclude_dirs):
            return
        if event.src_path.endswith(".py"):
            print(f"Changement détecté : {event.src_path}")
            self.start_process()

    def stop_process(self):
        if self.process and self.process.poll() is None:
            print("Arrêt du serveur Flask...")
            os.killpg(os.getpgid(self.process.pid), signal.SIGTERM)

if __name__ == "__main__":
    command = "python demo_server.py --config ../data/seattle_vps.json --output_path ./OUT"
    path = os.path.dirname(os.path.abspath(__file__))
    exclude_dirs = ["./OUT"] 
    port = 8080 

    event_handler = RestartOnChangeHandler(command, exclude_dirs, port)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)

    print(f"Surveillance des modifications dans : {path}")
    observer.start()
    try:
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
        event_handler.stop_process()
    observer.join()
