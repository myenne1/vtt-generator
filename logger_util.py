import os

class LogWriter:
    def __init__(self, log_path: str):
        self.log_path = log_path

    def write(self, message: str):
        with open(self.log_path, "a") as log_file:
            log_file.write(message + "\n")
