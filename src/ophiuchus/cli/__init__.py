import logging
import sys
from argparse import ArgumentParser
from typing import Dict
from typing import List

import pkg_resources
from ophiuchus.cli.subcommands import Subcommand


log = logging.getLogger(__name__)


def load_subcommands() -> Dict[str, Subcommand]:
    subcommands = {}
    for entry_point in pkg_resources.iter_entry_points(
        "ophiuchus_subcommands",
    ):
        subcommands[entry_point.name] = entry_point.load()

    return subcommands


def get_arg_parser() -> ArgumentParser:
    parser = ArgumentParser()

    # Display help by default
    parser.set_defaults(func=lambda **x: parser.print_help())
    parser.set_defaults(subcommand="help")

    # Common, global arguments
    parser.add_argument(
        "--logformat",
        type=str,
        help='Set log format (Default: "%(default)s")',
        default="%(asctime)s [%(levelname)7s] %(name)s: " "%(message)s",
    )
    parser.add_argument(
        "--loglevel",
        action="store",
        choices=list(logging._nameToLevel.keys()),
        default="INFO",
        type=lambda x: str(x).upper(),
        help='Set loglevel (Default: "%(default)s")',
    )

    # Setup the subparser argument
    subparsers = parser.add_subparsers(
        title="subcommand",
        description="Ophiuchus subcommands",
        dest="subcommand",
    )

    # Convenience subcommand for help
    subparsers.add_parser(
        "help", description="Display application help",
    ).set_defaults(func=lambda **x: parser.print_help())

    # Setup all discoverable subcommands
    for name, setup_func in load_subcommands().items():
        subparser = subparsers.add_parser(name)
        subparser.set_defaults(func=setup_func(subparser))

    return parser


def main(args: List[str] = None) -> int:
    parser = get_arg_parser()
    args = parser.parse_args(args)

    logging.basicConfig(
        level=args.loglevel, format=args.logformat,
    )

    log.debug(f"Args: {args}")

    try:
        log.debug(f'Running subcommand "{args.subcommand}"')
        return args.func(**vars(args))
    except Exception as e:
        log.critical(f'Subcommand "{args.subcommand}" failed: {e}')


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
