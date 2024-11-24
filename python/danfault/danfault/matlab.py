import argparse
from danfault.logs import Loggir
from datetime import datetime as dt
from termcolor import colored
import os

selflogger = Loggir()
def bold(txt: str) -> str:
    return colored(txt, attrs=['bold'])

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input',  type=str, help='input')
    parser.add_argument('-o', '--output', default='.', type=str, help='output')
    parser.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')
    parser.add_argument('--multichoice', choices=['a', 'b', 'c'], nargs='+', type=str, help='multiple types of arguments. May be called all at the same time.')
    args = parser.parse_args()
    
    pwd = os.getcwd()
    base = os.path.abspath(os.path.dirname(args.input))

    print(f'You are currently at: {bold(pwd)}')
    print(f'Changing to: {bold(base)}')
    os.chdir(base)

    matlab_script = os.path.basename(args.input).replace(".m",'')

    matlab_cmd = f"matlab -nodesktop -nosplash -r '{matlab_script}'" 
    print(f"Running {bold(matlab_cmd)}")

    os.system(matlab_cmd)

if(__name__=='__main__'):
    init=dt.now()
    main()
    end=dt.now()
    selflogger.info('Elapsed time: {}'.format(end-init))