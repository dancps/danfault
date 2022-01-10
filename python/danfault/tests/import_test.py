from danfault.logs import Loggir
import argparse
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbose', help='increase output verbosity', action='store_true')
    parser.add_argument('-d', '--debug', help='increase output verbosity', action='store_true')
    args = parser.parse_args()

    log = Loggir(verbose=args.verbose,debug=args.debug)


    log.debug("DEBUG")
    log.info("INFO")
    log.warning("WARNING")
    log.error("ERROR")
    log.critical("CRITICAL")


if(__name__=='__main__'):
    main()