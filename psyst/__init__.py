"""Base module for the population synthesis to stellar evolution wrapper"""

import os
import platform
from pathlib import Path
import signal
import sys

from psyst.base import Loader
from psyst.io import logger, LOG_FILENAME
from psyst.matchmaking import MatchMaker

__version__ = "0.0.1"


def __signal_handler(signal, frame):
    """Callback for CTRL-C"""
    end()


def end():
    """Stop matchmaking manager"""

    # logger.info("manager stopped")

    sys.exit(0)


def start():
    """Start manager"""

    logger.info("start matchmaking manager")

    # if only want to print database name and exit
    if core.args.show_log_fname:
        print(f"LOG FILENAME is: `{LOG_FILENAME}`")
        sys.exit(0)

    # load database of COMPAS
    core.load_compas_database()

    # try to save COMPAS database into an SQLite file
    if core.config.get("save_pop_synth_database_as_sql"):
        core.compasdb.save_to_sql(name=core.config.get("pop_synth_database_sql_name"))

    # load database of MESA
    core.load_mesa_database()

    # check if database of MESA and COMPAS will be printed out
    if core.args.show_mesa_database:
        core.mesadb.show_database()

    if core.args.show_compas_database:
        core.compasdb.show_database()

    if core.args.show_mesa_database or core.args.show_compas_database:
        sys.exit(0)

    # matchmaking process
    matchmaker = MatchMaker(
        compas_database=core.compasdb.database,
        mesa_database=core.mesadb.database,
        interpolation_method=core.config.get("interpolation_method"),
        interpolated_results_name=core.config.get("interpolated_results_name"),
    )

    matchmaker.do_matchmake()

    return


def main():
    """Main driver for stellar evolution matchmaking"""

    logger.info("initialize manager for the matchmaking of stellar evolution models")

    # catch CTRL-C signal
    signal.signal(signal.SIGINT, __signal_handler)

    # current working directory
    curr_dir = os.getcwd()

    logger.info(f"current working directory is `{curr_dir}`")
    logger.info(
        f"{platform.python_implementation()} {platform.python_version()} detected"
    )

    # load main driver
    global core
    core = Loader()

    # start manager
    start()

    # shutdown
    end()
