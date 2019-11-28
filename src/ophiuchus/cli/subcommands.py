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


class EntryPointBuilderSubcommand(Subcommand):
    # Subcommand baseclass providing some default common arguments

    def __init__(self, parser: ArgumentParser):
        super().__init__(parser)

        parser.add_argument(
            "--additional-endpoints",
            action="append",
            default=[],
            nargs=2,
            metavar=("SITE_GROUP", "ENDPOINT"),
            type=str,
            help="Add additional named endpoints that aren't part of the local"
            " build/run but are required by the application.",
        )
        parser.add_argument(
            "site_groups",
            nargs="+",
            metavar="site_group",
            type=str,
            help="Entry point group name(s) for website Lambda handlers",
        )
