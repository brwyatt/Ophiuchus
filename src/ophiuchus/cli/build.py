import os
from argparse import ArgumentParser
from os.path import abspath
from typing import List

from ophiuchus.cli.subcommands import EntryPointBuilderSubcommand
from ophiuchus.framework import GlobalConfig
from pip import main as pip


class Build(EntryPointBuilderSubcommand):
    description = "Build website lambdas"

    def __init__(self, parser: ArgumentParser):
        super().__init__(parser)

        parser.add_argument(
            "--artifact-dir",
            default="./build",
            type=abspath,
            help="Build/install directory for artifacts",
        )

    def __call__(
        self,
        site_groups: List[str],
        artifact_dir: str,
        additional_endpoints: List[List[str]] = [],
        *args,
        **kwargs,
    ):
        conf = GlobalConfig(endpoints=dict(additional_endpoints))  # noqa: F841

        os.makedirs(artifact_dir, exist_ok=True)
        pip(["install", "--target", artifact_dir, "-r", "./requirements.txt"])
