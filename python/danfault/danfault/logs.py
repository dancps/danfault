import logging
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

def calls(type_call):
    if(type_call=='error'): return '['+colored('x','red')+']'
    elif(type_call=='warning'): return '['+colored('!','yellow')+']'
    elif(type_call=='message'): return '['+colored('~','cyan')+']'


class Formatter(logging.Formatter):
    def __init__(self,verbose,debug) -> None:
        super(Formatter, self).__init__() # About super https://stackoverflow.com/questions/8853966/the-inheritance-of-attributes-using-init
        self.infocolors = {
            "DEBUG":    'green',
            "INFO":     'white',
            "WARNING":  'yellow' ,
            "ERROR":    'red' ,
            "CRITICAL": 'red'
        }
        self.infoattrs = {
            "DEBUG": [] ,
            "INFO":  [] ,
            "WARNING":[] ,
            "ERROR":  [] ,
            "CRITICAL": ['bold']
        }
        header = "{asctime} - {levelname:<8}" if verbose else "{levelname:<8}" 
        prefix = colored("{filename}:{name}:{lineno:<4} ",attrs=['dark']) if debug else (colored("{filename} ",attrs=['dark']) if verbose else "")
        format = "{message}"

        self.FORMATS = {
            logging.DEBUG:    self.get_header(header,"DEBUG")  +prefix + format,
            logging.INFO:     self.get_header(header,"INFO")   +prefix+ format,
            logging.WARNING:  self.get_header(header,"WARNING")    +prefix+ format,
            logging.ERROR:    self.get_header(header,"ERROR")  +prefix + format,
            logging.CRITICAL: self.get_header(header,"CRITICAL")   +prefix+ format
        }


    def get_header(self, msg, type="INFO"): 
        return f"[{colored(msg,self.infocolors[type],attrs=self.infoattrs[type])}] "
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt,style='{',datefmt='%H:%M:%S')

        return formatter.format(record)


class Loggir(logging.Logger):
    def __init__(self,level=logging.DEBUG,verbose=False,debug=False) -> None:
        super(Loggir, self).__init__(__name__)
        self.setLevel(level)
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        ch.setFormatter(Formatter(verbose,debug))
        self.addHandler(ch)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', required=False, type=str, help='input')
    parser.add_argument('-o', '--output', default='.', type=str, help='output')
    parser.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')
    parser.add_argument('--multichoice', choices=['a', 'b', 'c'], nargs='+', type=str, help='multiple types of arguments. May be called all at the same time.')
    args = parser.parse_args()
    
    log = Loggir()

    log.debug("DEBUG")
    log.info("INFO")
    log.warning("WARNING")
    log.error("ERROR")
    log.critical("CRITICAL")


if(__name__=='__main__'):
    init=dt.now()
    main()
    end=dt.now()
    print(calls('message'),'Elapsed time: {}'.format(end-init))
    