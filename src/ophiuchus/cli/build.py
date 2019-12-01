import os
import subprocess
import sys
from argparse import ArgumentParser
from os.path import abspath
from shutil import rmtree
from typing import List

from ophiuchus.cli.subcommands import EntryPointBuilderSubcommand
from ophiuchus.framework import GlobalConfig
from ophiuchus.framework import Handler
from ophiuchus.utils import load_entry_points
from pip import main as pip


def python_version():
    return f"{sys.version_info.major}.{sys.version_info.minor}"


class Build(EntryPointBuilderSubcommand):
    description = "Build website lambdas"

    def __init__(self, parser: ArgumentParser):
        super().__init__(parser)

        parser.add_argument(
            "--artifacts-base-dir",
            default="./build",
            type=abspath,
            help="Build/install directory for artifacts",
        )

        parser.add_argument(
            "--python-version",
            default=python_version(),
            type=str,
            help="Python version to build/package for. (Default is the current "
            "version: %(default)s)",
        )

        parser.add_argument(
            "--requirements-file",
            default="./requirements.txt",
            type=abspath,
            help="Path to application requirements.txt file",
        )

    def __call__(
        self,
        site_groups: List[str],
        artifacts_base_dir: str,
        additional_endpoints: List[List[str]] = [],
        python_version: str = python_version(),
        requirements_file: str = "./requirements.txt",
        *args,
        **kwargs,
    ):
        config = GlobalConfig(  # noqa: F841
            endpoints=dict(additional_endpoints),
        )

        self.log.info(f"Cleaning old artifacts dir: {artifacts_base_dir}")
        rmtree(artifacts_base_dir)
        os.makedirs(artifacts_base_dir, exist_ok=True)

        for site_group in site_groups:
            self.build_site_group(
                site_group=site_group,
                artifacts_base_dir=artifacts_base_dir,
                python_version=python_version,
                requirements_file=requirements_file,
            )

    def build_site_group(
        self,
        site_group: str,
        artifacts_base_dir: str,
        python_version: str = python_version(),
        requirements_file: str = "./requirements.txt",
    ):
        self.log.info(f"Building {site_group}")

        site_group_artifact_dir = os.path.join(artifacts_base_dir, site_group,)
        self.log.debug(f"Using artifact path: {site_group_artifact_dir}")
        site_group_lambda_dir = os.path.join(
            site_group_artifact_dir, "lambdas",
        )
        self.log.debug(f"Using lambda path: {site_group_lambda_dir}")
        site_group_packages_dir = os.path.join(
            site_group_artifact_dir,
            "python",
            "lib",
            f"python{python_version}",
            "site-packages",
        )
        self.log.debug(
            f"Using package install path: {site_group_packages_dir}",
        )

        self.log.debug("Creating site group artifact directory")
        os.makedirs(site_group_artifact_dir, exist_ok=True)

        self.install_package(
            site_group_packages_dir=site_group_packages_dir,
            requirements_file=requirements_file,
        )

    def install_package(
        self,
        site_group_packages_dir: str,
        requirements_file: str = "./requirements.txt",
    ):
        self.log.debug("Creating site group packages directory")
        os.makedirs(site_group_packages_dir, exist_ok=True)
        self.log.info(
            f"Installing package from requirements file {requirements_file} "
            f"into {site_group_packages_dir}",
        )
        subprocess.run(
            [
                "pip",
                "install",
                "--target",
                site_group_packages_dir,
                "-r",
                requirements_file,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
