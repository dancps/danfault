# Finds pyproject

# Checks the matches between pyproject and the current folder

# Folder of `pyproject.toml` probably is the root of the project

import os
from termcolor import colored

def get_scripts(scripts) -> list:
    # Add a try except block here
    #  Should be able to handle the case where:
    #    - the file doesn't exist
    #    - the method doesn't exist in the file
    

    errors = []
    loaded_scripts = []
    for script in scripts.keys():
        try:
            loaded_scripts.append(Script(name=script, path=scripts[script]))
        except FileNotFoundError as e:
            errors.append(colored("Error: ", "red")+f"{e}")
        except AttributeError as e:
            errors.append(colored("Error: ", "red")+f"{e}")
        except Exception as e:
            errors.append(f"An unexpected error occurred: {e}")
    
    if errors:
        raise Exception("Errors occurred while loading scripts:\n" + "\n".join(errors))
    
    return loaded_scripts
    # return [Script(name = script, path=scripts[script]) for script in scripts.keys()]

class Script:
    """
    A class to represent a script and its associated method.
    Attributes
    ----------
    name : str
        The name of the script.
    path : str
        The path to the script in the format 'file_path:method_name'.
    code_path : str
        The file path derived from the given path.
    exists : bool
        A flag indicating whether the script file exists.
    method : str
        The method name to be checked within the script file.
    Methods
    -------
    get_code():
        Returns the file path derived from the given path.
    get_method():
        Returns the method name from the given path.
    check_if_file_exists():
        Checks if the script file exists.
    check_if_method_exists_in_file():
        Checks if the specified method exists in the script file.
    __str__():
        Returns a string representation of the Script object.
    check():
        Validates the existence of the script file and the specified method.
    """

    def __init__(self, name:str, path:str) -> None:
        self.name = name
        self.path = path
        self.code_path = self.get_code()
        self.exists = self.check_if_file_exists()
        self.method = self.get_method()

        self.check()

    def get_code(self):
        return self.path.split(':')[0].replace('.','/')+".py"
    
    def get_method(self):
        return self.path.split(':')[1]
    
    def check_if_file_exists(self):
        return os.path.exists(self.get_code())
    
    def check_if_method_exists_in_file(self):
        with open(self.get_code(), 'r') as f:
            lines = f.readlines()
            for line in lines:
                if "def "+self.method in line:
                    return True
        return False
    
    def __str__(self):
        return f"Script(\n  name      = {self.name}\n  path      = {self.path}\n  code_path = {self.code_path}\n  exists    = {self.exists})"
    
    def check(self):
        if not self.exists:
            raise FileNotFoundError(f"File {self.get_code()} doesn't exist.")
        
        if not self.check_if_method_exists_in_file():
            raise AttributeError(f"Method {self.method} not found in file {self.get_code()}")
        
        return True