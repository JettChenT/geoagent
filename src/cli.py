import typer
from .subscriber import default_subscriber
from .sock import start_srv

app = typer.Typer()

@app.command()
def server():
    typer.echo("Starting server")
    sio, srv_thread = start_srv()
    input("server started")
    srv_thread.join()
