"""Module with COMPAS class and methods to handle population of binaries obtained with the
COMPAS code
"""

from pathlib import Path
import sqlite3
from typing import Union

import numpy as np
import pandas as pd

from psyst.io import logger


class COMPASdb(object):
    """Class to access COMPAS database

    The database will be stored in a variable called `database`, which is of type `dict`. Each
    key of it will be a numpy array with the corresponding column in the database.

    For instance,

    m1i     m2i     ai      porbi    ei     ...
    -------------------------------------------
    10.00   8.00    120.00  45.00    0.1    ...
    12.10   5.43     34.12   4.12    0.8    ...

    Thus, printing database['m1i'] will return the array [10.00, 12.10], such that the dimension
    of the array is the number of binaries in the population

    Parameters
    ----------
    database_name : `str / Path`
        Name of the database file
    """

    def __init__(
        self,
        database_name: Union[str, Path] = "",
    ) -> None:

        logger.info("create COMPAS object for a database")

        # always use pathlib
        if isinstance(database_name, str):
            if len(database_name) == 0:
                logger.critical("`database_name` cannot be empty")
                sys.exit(1)

            else:
                database_name = Path(database_name)

        # sanity check
        if not database_name.exists():
            logger.critical(f"no such file found: `{database_name}`")
            sys.exit(1)

        self.database_name = database_name

        self.database = self._load_database_()

    def _load_database_(
        self,
    ) -> dict:
        """Load COMPAS database into memory"""

        logger.info("load COMPAS database with keyword mappings")

        conn = sqlite3.connect(self.database_name)
        c = conn.cursor()

        return c

    def save_to_sql(self, name: str = "") -> None:
        """Save COMPAS database as an SQLite file"""

        conn = sqlite3.connect(name)

        try:
            self.database.to_sql("COMPASrun", conn)

        except ValueError:
            logger.error(
                "SQLite table `COMPASrun` already exists. will not create a new one"
            )

    def show_database(self) -> None:
        """Print database to standard output"""

        self.database.execute("SELECT * FROM COMPASrun;")
        print(self.database.fetchall())
