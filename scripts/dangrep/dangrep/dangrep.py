import os
from pdf2image import convert_from_path
import argparse
import traceback
import pytesseract as tess
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

global TYPE_COLORS
TYPE_COLORS = {
    "approx": "yellow",
    "approximate": "yellow",
    "approximates": "yellow",
    "exact": "green",
    "exacts": "green"
}

def calls(type_call):
    if(type_call=='error'): return '['+colored('x','red')+']'
    elif(type_call=='warning'): return '['+colored('!','yellow')+']'
    elif(type_call=='message'): return '['+colored('~','cyan')+']'

def find_pos(line):
    # Finds the position to be highlited
    # Returns the position and aprox type
    pass

def substitute(line, pattern, color):
    
    pass

def get_type_color(type):
    return TYPE_COLORS[type]

def highlight(lines,appoximates,exacts,verbose):
    # TODO: Optimize it

    # Aproximate scan

    # Exact scan
    for line_n, line in enumerate(lines):
        new_line = line
        for type_list,pat_type in [(appoximates,"approximates"),(exacts,"exacts")]:
            for pattern in type_list:
                new_line = new_line.replace(pattern,colored(pattern,get_type_color(pat_type)))
        if verbose: print(f"[l {line_n}] {new_line}".strip())
        else: print(f"{new_line}".strip())

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('file', type=str, help='input')
    parser.add_argument('pattern',nargs='+', type=str, help='output')
    parser.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')
    parser.add_argument('-d', '--debug', help='increase output verbosity', action='store_true')
    parser.add_argument('-a', '--approximate', help='tries to convert the image to text format', action='store_true')
    parser.add_argument('--case_sensitive', help='tries to convert the image to text format', action='store_true')
    args = parser.parse_args()

    with open(args.file,'r') as fl:
        lines = fl.readlines()
    
    if args.case_sensitive:
        # diferencia lower de nao lower
        pattern_list = args.pattern
    else:
        #processa tudo como lower
        pattern_list = [p.lower() for p in args.pattern]+[p.upper() for p in args.pattern]+[" ".join([p.capitalize() for p in pat.split(" ")]) for pat in args.pattern]

    exact_pats = pattern_list#[word for pattern in args.pattern for word in pattern.split(" ")]
    approx_pats = [word for pattern in pattern_list for word in pattern.split(" ")] if args.approximate else []

    print("Searching for:",", ".join([colored(pat,'green') for pat in exact_pats]+[colored(pat,'yellow') for pat in approx_pats]))

    highlight(lines,appoximates=approx_pats,exacts=exact_pats,verbose=args.verbose)
   
if(__name__=='__main__'):
    init=dt.now()
    try:
        main()
    except Exception as e:    
        print(e)
        print("Traceback do erro:")
        traceback.print_tb(e.__traceback__)
    end=dt.now()
    print(calls('message'),'Elapsed time: {}'.format(end-init))
