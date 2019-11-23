from argparse import ArgumentParser

from ophiuchus.cli.subcommands import Subcommand


class Build(Subcommand):
    description = "Build website"

    def __init__(self, parser: ArgumentParser):
        super().__init__(parser)
