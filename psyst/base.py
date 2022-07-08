"""Base module that handles the input of arguments as well as the classes for each part of the
matchmaking process


SQLite to make comparison should be something like this:

    SELECT *,ABS(m1i-20)*ABS(m1i-20) + ABS(m2i-10)*ABS(m2i-10) + ABS(porbi - 3)*ABS(porbi -3) + ABS(ei - 0.45)*ABS(ei - 0.45) FROM MESArun ORDER BY ABS(m1i-20)*ABS(m1i-20) + ABS(m2i-10)*ABS(m2i-10) + ABS(porbi - 3)*ABS(porbi -3) + ABS(ei - 0.45)*ABS(ei - 0.45) DESC;

"""

import argparse
import os
from pathlib import Path
import pprint
import sys

from psyst.binaries import COMPASdb, MESAdb
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

        parser.add_argument(
            "--show-compas-database",
            action="store_true",
            default=False,
            dest="show_compas_database",
            help="display COMPAS database in standard output and exit",
        )

        parser.add_argument(
            "--show-mesa-database",
            action="store_true",
            default=False,
            dest="show_mesa_database",
            help="display MESA database in standard output and exit",
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

    def load_compas_database(self) -> None:
        """Load COMPAS database of a stellar population"""

        logger.info("load COMPAS database from file")

        # short name for COMPAS db
        db_name = self.config.get("pop_synth_database")

        if isinstance(db_name, str):
            if len(db_name) == 0:
                logger.critical(
                    "empty name of `pop_synth_database` option in configuration file"
                )
                sys.exit(1)

            else:
                db_name = Path(db_name)

        # sanity check
        if not db_name.exists():
            logger.critical(f"no such file found: `{db_name}`")
            sys.exit(1)

        # now we can load COMPAS database
        self.compasdb = COMPASdb(database_name=db_name)

    def load_mesa_database(self) -> None:
        """Load MESA database of a stellar population"""

        logger.info("load MESA database from file")

        # short name for MESA db
        db_name = self.config.get("mesa_database")

        if isinstance(db_name, str):
            if len(db_name) == 0:
                logger.critical(
                    "empty name of `mesa_database` option in configuration file"
                )
                sys.exit(1)

            else:
                db_name = Path(db_name)

        # sanity check
        if not db_name.exists():
            logger.critical(f"no such file found: `{db_name}`")
            sys.exit(1)

        # now we can load COMPAS database
        self.mesadb = MESAdb(database_name=db_name)
