"""Module responsible for the matchmaking process between the COMPAS and the MESA databases"""

import itertools
import multiprocessing as mp
from pathlib import Path
import pprint
import sqlite3
from typing import Union
import sys
import yaml

import numpy as np

from psyst.io import logger


class MatchMaker(object):

    """Class which holds the methods to perform matchmaking algorithms between two database"""

    SET_LOG = True
    LOG_KEYS = ["m1i", "m2i", "porbi"]

    # index needed from the header (remember that for mesa, m1i is the companion mass of COMPAS)
    NAMES_TO_MATCH = ["companion_mass", "remnant_mass", "porb_pm", "e_pm"]
    NAMES_ON_MESA = ["m1i", "m2i", "porbi", "ei"]

    def __init__(
        self,
        compas_database: sqlite3.Cursor = None,
        mesa_database: sqlite3.Cursor = None,
        mesa_grid_name: Union[str, Path] = "",
        interpolation_method: str = "",
        interpolated_results_name: str = "",
    ):

        # set defaults
        self.compas_database = compas_database
        self.mesa_database = mesa_database

        if mesa_grid_name is None:
            logger.critical("`mesa_grid_name` cannot be empty")
            sys.exit(1)

        if isinstance(mesa_grid_name, str):
            if len(mesa_grid_name) == 0:
                logger.critical("empty name griven for the mesa grid file")
                sys.exit(1)

            else:
                self.mesa_grid_name = Path(mesa_grid_name)

        if len(interpolation_method) == 0 or interpolation_method is None:
            logger.info(
                "no interpolation method given. Using default of `nearest_neighbour`"
            )
            interpolation_method = "nearest_neighbour"

        self.interpolation_method = interpolation_method
        self.interpolated_results_name = interpolated_results_name

    def __header_mapping__(
        self,
    ) -> dict:
        """Simple mapper between strings"""

        # one more keyword matching snippet
        HEADER_MAPPINGS = {
            name: self.NAMES_ON_MESA[k] for k, name in enumerate(self.NAMES_TO_MATCH)
        }

        return HEADER_MAPPINGS

    def __to_log__(
        self,
        binary: dict = {}
    ) -> dict:
        """Convert each element (arrays) in a dictionary to log10

        Parameters
        ----------
        binary : `dict`
            Dictionary with the arrays as elements

        Returns
        -------
        binary : `dict`
            Dictionary with the log10 of its elements
        """

        for key, val in binary.items():
            if key in self.LOG_KEYS:
                binary[key] = np.log10(val)

        return binary

    def __to_linear__(
        self,
        binary: dict = {}
    ) -> dict:
        """Convert each element (arrays) in a dictionary to linear space

        Parameters
        ----------
        binary : `dict`
            Dictionary with the arrays as elements

        Returns
        -------
        binary : `dict`
            Dictionary with the linspace of its elements
        """

        for key, val in binary.items():
            if key in self.LOG_KEYS:
                binary[key] = float("{:.2f}".format(10**val))

        return binary

    def _find_nearest_neighbour_(
        self,
        binary: dict = {},
        grid: dict = {}
    ) -> dict:
        """Find nearest neighbour with weight = 1.0

        Parameters
        ----------
        binary : `dict`
            Dictionary with the binary information to match with a grid

        grid : `dict`
            Dictionary with the complete grid of regular points where the closest neighbour
            will be located

        Returns
        -------
        neighbour : `list`
            Element from grid which is closest to the binary dict. It also contains an element
            called `weight` equal to 1
        """

        neighbour= {}
        for par, val in binary.items():
            neighbour[par] = grid[par][np.argmin(np.abs(grid[par]-val))]

        neighbour["weight"] = 1.0

        return [neighbour]

    def _find_weighted_neighbours_(
        self,
        binary: dict = {},
        grid: dict = {}
    ) -> dict:
        """Find the 2**N neighbours and their corresponding weights, in an N-dimensional space

        Parameters
        ----------
        binary : `dict`
            Dictionary with the binary information to match with a grid

        grid : `dict`
            Dictionary with the complete grid of regular points where the 2**N closest neighbours
            will be located

        Returns
        -------
        neighbours : `list`
            Element from grid which are closest to the binary dict. It also contains an element
            called `weights` that measures the distance to each point of the grid
        """

        # for numerical reasons
        NZERO = 1e-15

        # Find lowest neighbour
        idx_neigh = {}
        for par, val in binary.items():
            idx_neigh[par] = np.argmin(np.abs(grid[par]-val))

            if val < grid[par][idx_neigh[par]]:
                idx_neigh[par] -= 1

        # Define the mesh of neighbours
        DIM = len(grid.keys())
        mesh = np.array([x for x in itertools.product(*(np.arange(2) for i in range(DIM)))])

        # Obtain the weights of each neighbour
        neighbours, weights = [], []
        for i, idx in enumerate(mesh):
            neigh = {}
            weight = 1.0
            for j, (par, val) in enumerate(binary.items()):
                neigh[par] = grid[par][idx_neigh[par] + idx[j]]

                num_par = np.abs(val-grid[par][idx_neigh[par] + idx[j]])
                den_par = grid[par][idx_neigh[par] + 1]-grid[par][idx_neigh[par]]

                if np.abs(num_par/den_par - 1.0) < NZERO:
                    weight *= 1

                elif np.abs(num_par) < NZERO:
                    weight *= NZERO

                else:
                    weight *= num_par/den_par

            neighbours.append(neigh)
            weights.append(1/weight)

        weights/=sum(weights)

        for i, neigh in enumerate(neighbours):
            neigh["weight"] = weights[i]

        return neighbours

    def do_single_matchmake(
        self,
        datum,
        grid: dict = {},
    ):
        """Actual matchmaking process is done here for a single binary of the COMPAS database
        """

        # query COMPAS database
        self.compas_database.execute("SELECT * FROM COMPASrun;")

        # COMPAS header
        compas_header = [i[0] for i in self.compas_database.description]

        # keyword index
        keyword_index = dict()

        # get indices for keywords
        for name in self.NAMES_TO_MATCH:
            keyword_index[name] = -1

            for k, header in enumerate(compas_header):
                if header == name:
                    keyword_index[name] = k
                    break

        # header mapping misc
        headers_mapping = self.__header_mapping__()

        # store values to be matched in a dictionary
        binary_to_match = dict()

        for k, value in enumerate(datum):
            for mkey, mvalue in keyword_index.items():
                if k == mvalue:
                    binary_to_match[headers_mapping[mkey]] = value

        # log into binary
        if self.SET_LOG:
            binary_to_match = self.__to_log__(binary=binary_to_match)

        # depending on the interpolation method, comput
        if self.interpolation_method == "nearest_neighbour":
            # get nearest neighbour
            neighbours = self._find_nearest_neighbour_(binary=binary_to_match, grid=grid)

        else:
            # get near neighbours
            neighbours = self._find_weighted_neighbours_(binary=binary_to_match, grid=grid)

        # return to original values of binary system for the COMPAS and MESA cases
        if self.SET_LOG:
            binary_to_match = self.__to_linear__(binary=binary_to_match)

            for k, neighbour in enumerate(neighbours):
                neighbours[k] = self.__to_linear__(binary=neighbour)

                debug_string = (
                    f"closest point to ({binary_to_match['m1i']:.2f},"
                    f" {binary_to_match['m2i']:.2f}, {binary_to_match['porbi']:.2f},"
                    f" {binary_to_match['ei']:.2f}) is: `({neighbour['m1i']:.2f},"
                    f" {neighbour['m2i']:.2f}, {neighbour['porbi']:.2f},"
                    f" {neighbour['ei']:.2f})"
                )
                logger.debug(debug_string)

        return neighbours

    def do_matchmake(
        self,
    ) -> None:
        """Matchmaking algorithm between binaries"""

        logger.info("start matchmaking process")

        # open mesa grid file
        with open(self.mesa_grid_name, "r") as f:
            grid = yaml.load(f, Loader=yaml.FullLoader)

        # convert everything to numpy and apply log if needed
        for key in grid.keys():
            grid[key] = np.array(grid[key])

            if self.SET_LOG:
                if key in self.LOG_KEYS:
                    grid[key] = np.log10(grid[key])

        # query databases of MESA and COMPAS
        self.mesa_database.execute("SELECT * FROM MESArun;")
        self.compas_database.execute("SELECT * FROM COMPASrun;")

        # get final values of the COMPAS database (remnant_mass, companion_mass, a_pm, e_pm) -> (m1i, m2i, ai, ei)
        data = self.compas_database.fetchall()

        # results holds the run_name of the MESA simulation and a counter that tells us how many times we reproduced
        # the binary in the COMPAS database
        results = dict()
        results["run_name"] = []
        results["weight"] = []

        # loop over COMPAS database elements (# TODO: use multiprocessing for this)
        for datum in data:
            neighbours = self.do_single_matchmake(datum, grid=grid)

            # loop over neighbours list to find match in MESA database
            for neigh in neighbours:
                # string with the query to send to sqlite3
                string = ""
                for name in self.NAMES_ON_MESA:
                    string += f"ABS({name} - {neigh[name]})*ABS({name} - {neigh[name]}) + "
                string = string[:-3]

                # get closest point in the grid
                self.mesa_database.execute(
                    f"SELECT run_name, {string} as dist FROM MESArun ORDER BY {string} DESC"
                )
                closest_value = self.mesa_database.fetchall()[-1]
                run_name = closest_value[0]


                # store thm in the results dict
                if not run_name in results["run_name"]:
                    results["run_name"].append(run_name)
                    results["weight"].append(neigh["weight"])
                else:
                    for k, name in enumerate(results["run_name"]):
                        if run_name == "name":
                            break
                    results["weight"][k] += neigh["weight"]

        # create database with results
        conn = sqlite3.connect(self.interpolated_results_name)

        # connect to it with a cursor
        c = conn.cursor()

        command = "CREATE TABLE IF NOT EXISTS MESAweighted (run_name TEXT, weight REAL);"
        c.execute(command)

        for j in range(len(results["run_name"])):
            name = results["run_name"][j]
            command = "INSERT INTO MESAweighted (run_name, weight) VALUES "
            command += f"('{name}', {results['weight'][j]});"
            c.execute(command)

        conn.commit()
        conn.close()

