from argparse import ArgumentParser

from ophiuchus.cli.subcommands import Subcommand
from ophiuchus.utils import load_entry_points


class Run(Subcommand):
    description = "Run website locally"

    def __init__(self, parser: ArgumentParser):
        super().__init__(parser)

        parser.add_argument(
            "site_name",
            type=str,
            help="Entrypoint group name for website Lambda handlers",
        )

    def __call__(self, site_name, *args, **kwargs) -> int:
        handlers = load_entry_points(site_name)
        self.log.debug(handlers)
