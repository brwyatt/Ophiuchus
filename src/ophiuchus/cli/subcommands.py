import logging
from argparse import ArgumentParser


# Parent class for subcommands.
class Subcommand:
    help = None
    description = None

    def __init__(self, parser: ArgumentParser):
        self.log = logging.getLogger(
            "{}.{}".format(self.__module__, self.__class__.__name__),
        )

        if self.help:
            parser.help = self.help

        if self.description:
            parser.description = self.description

    def __call__(self, *args, **kwargs) -> int:
        msg = "This subcommand has not been implemented"
        self.log.critical(msg)
        raise NotImplementedError(msg)
