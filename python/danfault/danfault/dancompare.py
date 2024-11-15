"""Compares the files from one folder to another using sha256sum.

Raises:
    ValueError: _description_
    TypeError: _description_

Returns:
    _type_: _description_
"""

import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import argparse
from datetime import datetime as dt
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
from danfault.logs import Loggir
from hashlib import sha256
selflogger = Loggir()
def calls(type_call):
    if(type_call=='error'): return '['+colored('x','red')+']'
    elif(type_call=='warning'): return '['+colored('!','yellow')+']'
    elif(type_call=='message'): return '['+colored('~','cyan')+']'


def generate_sha256sum(input_file, output_folder, debug: bool = False):

    """
    From https://stackoverflow.com/questions/12900538/fastest-way-to-tell-if-two-files-have-the-same-contents-in-unix-linux:
    sha256sum oldFile > oldFile.sha256

    echo "$(cat oldFile.sha256) newFile" | sha256sum --check

    newFile: OK
    """

    """
    https://stackoverflow.com/questions/48613002/sha-256-hashing-in-python
    """

    basename, ext = os.path.splitext(os.path.basename(input_file))
    outpath = os.path.join(output_folder,f"{basename}.sha256")
    if os.path.isfile(outpath):
       if debug: selflogger.warning(f"The file {outpath} already exist. Skipping it.")
    if debug: selflogger.debug(f"generate_sha256sum: {input_file} -> {outpath}")
    os.system(f"sha256sum {input_file} > {outpath}")
    return outpath

def compare_sha256sum(base_sha, compare_sha, debug: bool = False):
    with open(base_sha, 'r') as fl:
        base_sha256 = fl.read().split(" ")[0]
    
    with open(compare_sha, 'r') as fl:
        compare_sha256 = fl.read().split(" ")[0]
    
    if debug:
        selflogger.debug(f"Base sha256sum   : {base_sha256}")
        selflogger.debug(f"Compare sha256sum: {compare_sha256}")

    return base_sha256==compare_sha256

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-b', '--base-folder', required=True, type=str, help='input')
    parser.add_argument('-c', '--comparison-folder', required=True, type=str, help='input')
    parser.add_argument('-o', '--output', default='./runs/', type=str, help='output')
    parser.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')
    parser.add_argument('-d', '--debug', help='increase output verbosity', action='store_true')
    parser.add_argument('--multichoice', choices=['a', 'b', 'c'], nargs='+', type=str, help='multiple types of arguments. May be called all at the same time.')
    args = parser.parse_args()

    if not os.path.isdir(args.output):
        selflogger.error(f"The folder {args.output} doesn't exist. Please create it.")
        selflogger.info(f"The generated files and folders will be generated on the folder {args.output} when you create it.")
        raise ValueError()
    else:
        selflogger.info(f"Creating the folders base_sha256/ and comparison_sha256/ at {args.output}")
        

    output_base_folder = os.path.join(args.output, "base_sha256")
    output_comparison_folder = os.path.join(args.output, "comparison_sha256")
    if not os.path.isdir(output_base_folder): os.makedirs(output_base_folder)
    if not os.path.isdir(output_comparison_folder): os.makedirs(output_comparison_folder)

    if not os.path.isdir(args.base_folder):
        raise TypeError("Should be a folder")

    missing_files = []    
    different_files = []    
    for basefile in os.listdir(args.base_folder):
        base_filepath = os.path.join(args.base_folder, basefile)
        comparison_filepath = os.path.join(args.comparison_folder, basefile)
        if not os.path.isfile(comparison_filepath):
            selflogger.error(f"The file {comparison_filepath} doesn't exist.")
            missing_files.append(comparison_filepath)
            continue
        if args.debug: selflogger.debug("Generating sha for files")
        base_file_sha = generate_sha256sum(base_filepath, output_base_folder, debug = args.debug)
        comparison_file_sha = generate_sha256sum(comparison_filepath, output_comparison_folder, debug = args.debug)
        is_equal = compare_sha256sum(base_file_sha, comparison_file_sha, debug = args.debug)
        if not is_equal: different_files.append((base_filepath, comparison_filepath))
        # TODO: This logic doesn't check for files that are only at the comparsion folder.

    selflogger.warning("The following files were not found:\n  - "+"\n  - ".join(missing_files))
    if len(different_files)>0:
        for b,c in different_files:
            selflogger.info(f"File {b} and {c} doesn't match.")

if(__name__=='__main__'):
    init=dt.now()
    main()
    end=dt.now()
    print(calls('message'),'Elapsed time: {}'.format(end-init))