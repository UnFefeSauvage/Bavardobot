# -*- coding: UTF-8 -*-
import os.path
import threading


class ResourcesManager:
    def __init__(self, path):
        self.path = os.path.normpath(path)
        self.locks = {}
    
    def write(self, path, data):
        if os.path.isdir(path):
            raise ValueError(f"Cannot write to {path} for it is a directory!")
        
        path = self.path + "/" + os.path.normpath(path)

        if ".." in path or path[0] == "/":
            raise ValueError("Only relative paths to childs are allowed!")

        if not (path in self.locks.keys()):
            self.locks[path] = threading.Lock()

        
        with self.locks[path]:
            with open(path, 'w') as file:
                file.write(data)

        
    def read(self, path):
        if os.path.isdir(path):
            raise IsADirectoryError(f"Cannot write to {path} for it is a directory!")
        
        path = self.path + "/" + os.path.normpath(path)

        if ".." in path or path[0] == "/":
            raise ValueError("Only relative paths to childs are allowed!")
        
        if os.path.isdir(path):
            raise ValueError(f"{path} is a directory")

        if not os.path.isfile(path):
            raise FileNotFoundError(f"{path} does not exist!")

        data = None

        if not (path in self.locks.keys()):
            self.locks[path] = threading.Lock()

        with self.locks[path]:
            with open(path, 'r') as file:
                data = file.read()
        
        return data

