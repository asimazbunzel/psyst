"""Base module that handles the input of arguments as well as the classes for each part of the
matchmaking process
"""

import argparse
import os
from pathlib import Path
import pprint
import sys

from psyst.io import load_yaml, logger


class Loader(object):
    """Load configuration values into this class"""

    def __init__(
        self,
    ) -> None:

        logger.info("create Loader object")

        # get command-line arguments
        self.args = self.parse_args()

        # sanity check, without a config file, we can't work
        if self.args.config_fname is None:
            logger.critical(
                "configuration file flag `-C` or `--config-file` cannot be empty"
            )
            sys.exit(1)

        # use pathlib
        if isinstance(self.args.config_fname, str):
            if len(self.args.config_fname) == 0:
                logger.critical("empty name of configuration file")
                sys.exit(1)

            else:
                self.args.config_fname = Path(self.args.config_fname)

        # load configuration file as a dictionary
        self.config = self.load_config_file()

    def init_args(
        self,
    ) -> argparse.ArgumentParser:
        """Initialize parser of command-line arguments"""

        logger.info("initialize parser of command-line arguments")

        parser = argparse.ArgumentParser(
            prog="matchmaking-manager",
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            description="matchmake a population of stars from a population synthesis code to a detailed stellar evolution grid of models",
        )

        parser.add_argument(
            "-d",
            "--debug",
            action="store_true",
            default=False,
            dest="debug",
            help="enable debug omde",
        )

        parser.add_argument(
            "-C",
            "--config-file",
            dest="config_fname",
            help="name of configuration file",
        )

        parser.add_argument(
            "--show-log-name",
            action="store_true",
            default=False,
            dest="show_log_fname",
            help="display log filename in standard output and exit",
        )

        return parser

    def parse_args(self) -> argparse.Namespace:
        """Parse command-line arguments"""

        logger.info("parse of command-line arguments to Loader")

        args = self.init_args().parse_args()

        if args.debug:
            from logging import DEBUG

            logger.setLevel(DEBUG)

        msg = "command-line arguments are: "
        for k, v in sorted(vars(args).items()):
            msg += f"{k}: {v} "
        logger.debug(msg[:-1])

        return args

    def load_config_file(self) -> dict:
        """Load configuration file with options for the matchmaking process"""

        logger.info("load configuration file")

        if not self.args.config_fname.exists():
            logger.critical(f"no such file found: `{self.args.config_fname}`")
            sys.exit(1)

        return load_yaml(self.args.config_fname)
