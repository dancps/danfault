from danfault.logs import Loggir
import os

def main():

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