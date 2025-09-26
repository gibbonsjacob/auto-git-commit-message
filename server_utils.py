import subprocess
import time
import requests

class OllamaServer:
    """
    Summary:
        A class to manage the lifecycle of an Ollama server instance, including
        starting, checking, and stopping the server.
    """

    def __init__(self, model_name: str):
        """
        Summary:
            Initialize the OllamaServer with the given model name.
        Args:
            model_name (str): The name of the Ollama model to serve.
        """
        self.model_name = model_name
        self.proc = None
        

    def get_pid(self) -> bool:
        """
        Summary:
            Check if the Ollama server process is running.
        Returns:
            bool: True if running, False otherwise.
        """
        try:
            output = subprocess.check_output(["pgrep", "-f", "ollama serve"])
            return output.strip()
        except subprocess.CalledProcessError:
            return False
        
        
    def is_running(self) -> bool:
        try:
            resp = requests.get("http://localhost:11434/api/tags", timeout=5)
            return resp.status_code == 200
        except Exception:
            return False
        
        
    def start(self) -> None:
        """
        Summary:
            Start the Ollama server if it's not already running.
        Raises:
            RuntimeError: If the server fails to start.
        """
        if self.is_running():
            return

        print(f"Starting Ollama server for model: {self.model_name}")
        self.proc = subprocess.Popen(
            ["ollama", "serve"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True
        )

        timeout = 5
        start_time = time.time()
        while not self.is_running():
            if time.time() - start_time > timeout:
                raise RuntimeError("Failed to start Ollama server in time.")
            time.sleep(0.5)

    def stop(self) -> None:
        """
        Summary:
            Stop the Ollama server if it was started by this instance.
        """
        if self.proc:
            self.proc.terminate()
            self.proc.wait()
            self.proc = None
