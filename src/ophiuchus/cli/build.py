from argparse import ArgumentParser

from ophiuchus.cli.subcommands import EntryPointBuilderSubcommand


class Build(EntryPointBuilderSubcommand):
    description = "Build website"

    def __init__(self, parser: ArgumentParser):
        super().__init__(parser)
