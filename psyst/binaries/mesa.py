"""Module with a class and methods to analyze the database of a MESA grid of detailed
stellar evolution models
"""

from pathlib import Path
import sqlite3
from typing import Union

import pandas as pd

from psyst.io import logger


class MESAdb(object):
    """Class to access MESA database

    This database is stored as a SQLite file. To access it, commands should be sent using the
    sqlite3 module as follows:

    sqlite> .header on
    sqlite> .mode column
    sqlite> ATTACH DATABASE "fake.db" as 'db';
    sqlite> SELECT m1i, m2i, porbi, ei FROM MESArun;
    m1i               m2i               porbi             ei
    ----------------  ----------------  ----------------  ------------------
    100.652751037365  75.3792117601077  612.41538335228   0.347874034205441
    56.5083481563887  6.46905597851916  647.08550055285   0.18264349285481

    In python, we access the database with:
    > conn = sqlite3.connect(database-name)
    > c = conn.cursor()

    And to use the table, we pass strings to the execute() method:
    > c.execute("SELECT m1i, m2i, porbi, ei FROM MESArun")

    If there are changes, we commit them before closing the connection
    conn.commit()
    conn.close()

    Parameters
    ----------
    database_name : `str / Path`
        Name of the database file
    """

    def __init__(
        self,
        database_name: str = "",
    ) -> None:

        logger.info("create MESA object for a database")

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
    ) -> sqlite3.Cursor:
        """Load MESA database into memory"""

        logger.info("load MESA database")

        conn = sqlite3.connect(self.database_name)
        c = conn.cursor()

        return c

    def show_database(self) -> None:
        """Print database to standard output"""

        self.database.execute("SELECT * FROM MESArun;")
        print(self.database.fetchall())
