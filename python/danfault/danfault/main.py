from danfault.logs import Loggir
import os
import typer
from danfault import csvutils
app = typer.Typer()

# Optionally, you can add commands to the app here or in other modules and import them.
app.add_typer(csvutils.app, name="csv")

@app.command()
def hello_world():
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