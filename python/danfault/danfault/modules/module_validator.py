"""





https://stackoverflow.com/questions/3229419/how-to-pretty-print-nested-dictionaries
https://stackoverflow.com/questions/25638905/coloring-json-output-in-python
https://rich.readthedocs.io/en/stable/reference/init.html?highlight=print_json#rich.print_json
https://stackoverflow.com/questions/75115582/how-to-load-toml-file-in-python
"""

import toml
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
from danfault.logs import Loggir
from datetime import datetime as dt

import pprint

try:
    from termcolor import colored
except ImportError:
    def colored(inp,*s):
        return inp
try:
    from tqdm import tqdm
except ImportError:
    def tqdm(inp,*s):
        return inp
    
from rich import print as rprint
from rich import print_json
from danfault.modules.modules import Script, get_scripts


selflogger = Loggir()

def print_dict(dictionary):
    pp = pprint.PrettyPrinter(depth=4)
    pp.pprint(dictionary)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=str, help='input')
    parser.add_argument('-o', '--output', default='.', type=str, help='output')
    parser.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')
    parser.add_argument('--multichoice', choices=['a', 'b', 'c'], nargs='+', type=str, help='multiple types of arguments. May be called all at the same time.')
    args = parser.parse_args()

    if not os.path.exists(args.input):
        selflogger.error(f"File {args.input} doesn't exist.")
        raise FileNotFoundError(f"File {args.input} doesn't exist.")

        
    data = toml.load(args.input)

    # print_dict(data)
    # print(toml.dumps(data))
    # rprint(data)
    # print("-----------------------------------------------------")
    print_json(data=data)
    package = data['tool']['setuptools']['package-dir']
    print(package) # Gets the package name

    if len(package.keys())>1:
        selflogger.error('More than one package found in the package-dir. Please check the configuration file.')
        # raise ValueError('More than one package found in the package-dir. Please check the configuration file.')
    
    package_name = list(package.keys())[0]
    package_dir = package[package_name]

    print(colored("Package name: ", attrs=['bold'])+f"{package_name}")
    print(colored("Package folder: ", attrs=['bold'])+f"{package_dir}/")

    
    scripts = data['project']['scripts']

    print(scripts)

    scripts_objects = get_scripts(scripts)

    for script in scripts_objects:
        print(colored("Script name: ", attrs=['bold'])+f"{script.name}")
        print(colored("Script path: ", attrs=['bold'])+f"{script.path}")
        print(colored("Script folder: ", attrs=['bold'])+f"{script.get_code()}")
        print(colored("Script: ", attrs=['bold'])+f"{script}")
        print("-----------------------------------------------------")

    # based on package name, checks the current scripts

    # For each script, find file and then check the file
    #   For this might be interesting to include a way of inspecting python files



    # get


if(__name__=='__main__'):
    init=dt.now()
    main()
    end=dt.now()
    print('Elapsed time: {}'.format(end-init))