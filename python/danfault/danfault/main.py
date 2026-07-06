from danfault.logs import Loggir
import os
import typer
from danfault import csvutils
from danfault import arc
from danfault import spotify
from danfault import vault
app = typer.Typer()

# Optionally, you can add commands to the app here or in other modules and import them.
app.add_typer(csvutils.app, name="csv")
app.add_typer(arc.arc_app, name="arc")
app.add_typer(spotify.app, name="spotify")
app.add_typer(vault.app, name="vault")

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