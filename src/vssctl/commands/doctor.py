import platform

import typer

from rich import print

app = typer.Typer()


def run():

    print()

    print("[green]vssctl[/green]")

    print(platform.platform())

    print("OK")