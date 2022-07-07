"""Module with COMPAS class and methods to handle population of binaries obtained with the
COMPAS code
"""

from pathlib import Path
from typing import Union

import numpy as np

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
    ) -> None:

        logger.info("load COMPAS database with keyword mappings")

        header = dict()
        data = dict()

        # mapping keywords
        keywords_map = {
            "Mass@ZAMS(1)": "m1i",
            "Mass@ZAMS(2)": "m2i",
            "Eccentricity@ZAMS": "ei",
            "SemiMajorAxis@ZAMS": "ai",
            "Age(SN)": "age_pre_cc",
            "Mass_CO_Core@CO(SN)": "c_core_mass_pre_cc",
            "Eccentricity<SN": "e_pre_cc",
            "SemiMajorAxis<SN": "a_pre_cc",
            "Orb_Velocity<SN": "v_orb_pre_cc",
            "Drawn_Kick_Magnitude(SN)": "w_kick",
            "Applied_Kick_Magnitude(SN)": "w_kick_applied",
            "SN_Kick_Theta(SN)": "theta_kick",
            "SN_Kick_Phi(SN)": "phi_kick",
            "Fallback_Fraction(SN)": "f_fb",
            "Supernova_State": "sn_state",
            "Mass(SN)": "remnant_mass",
            "Mass(CP)": "companion_mass",
            "Stellar_Type(CP)": "companion_stellar_type",
            "SemiMajorAxis": "a_pm",
            "Eccentricity": "e_pm",
        }

        # open file
        f = open(self.database_name, "r")

        # first two rows are not used
        f.readline()
        f.readline()

        # column names
        tmp = f.readline().strip().split()
        column_names = [keywords_map[name] for name in tmp]

        # will re-open it later
        f.close()

        # now load it again with numpy and assign column_names to columns of fdata
        fdata = np.loadtxt(self.database_name, skiprows=3, unpack=True)

        for k, name in enumerate(column_names):
            data[name] = np.array(fdata[k])

        return data
