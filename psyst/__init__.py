"""Base module for the population synthesis to stellar evolution wrapper"""

import os
import platform
from pathlib import Path
import signal
import sys

from psyst.base import Loader
from psyst.io import logger, LOG_FILENAME

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
    if True:
        print(f"LOG FILENAME is: `{LOG_FILENAME}`")

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
