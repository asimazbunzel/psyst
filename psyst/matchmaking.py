"""Module responsible for the matchmaking process between the COMPAS and the MESA databases"""

import itertools
import pprint
import sqlite3
import sys
import yaml

import numpy as np

from psyst.io import logger


class MatchMaker(object):

    """Class which holds the methods to perform matchmaking algorithms between two database"""

    def __init__(
        self,
        compas_database: sqlite3.Cursor = None,
        mesa_database: sqlite3.Cursor = None,
        interpolation_method: str = "",
        interpolated_results_name: str = "",
    ):

        # set defaults
        self.compas_database = compas_database
        self.mesa_database = mesa_database

        if len(interpolation_method) == 0 or interpolation_method is None:
            logger.info(
                "no interpolation method given. Using default of `nearest_neighbour`"
            )
            interpolation_method = "nearest_neighbour"

        self.interpolation_method = interpolation_method

        self.interpolated_results_name = interpolated_results_name

    def do_test_single_matchmake(
        self,
        datum: tuple = (),
        keyword_index: dict = {},
        keyword_match: dict = {},
        names_on_mesa: list = [],
    ) -> None:
        """I will write the documentation of this method sometime in the future

        Parameters
        ----------
        """

        logger.debug(f"matchmake of binary {datum}")

        # store values to be matched in a dictionary
        values_to_match = dict()
        for k, value in enumerate(datum):
            for mkey, mvalue in keyword_index.items():
                if k == mvalue:
                    values_to_match[mkey] = value

        # string to send to sqlite3
        string = ""
        for name in names_on_mesa:
            string += f"ABS({name} - {values_to_match[keyword_match[name]]})*ABS({name} - {values_to_match[keyword_match[name]]}) + "
        string = string[:-3]

        # get closest point in the grid
        self.mesa_database.execute(
            f"SELECT run_name, {string} as dist FROM MESArun ORDER BY {string} DESC"
        )
        closest_value = self.mesa_database.fetchall()[-1]

        run_name = closest_value[0]
        distance = closest_value[-1]

        debug_string = (
            f"closest point to ({values_to_match['companion_mass']:.2f},"
            f" {values_to_match['remnant_mass']:.2f}, {values_to_match['porb_pm']:.2f},"
            f" {values_to_match['e_pm']:.2f}) is: `{run_name}` with a distance of: {distance:.2f}"
        )
        logger.debug(debug_string)

        return run_name

    def do_test_matchmake(
        self,
    ) -> None:
        """Actual matchmaking process"""

        logger.info("start matchmaking process")

        do_test = False

        self.mesa_database.execute("SELECT * FROM MESArun;")
        self.compas_database.execute("SELECT * FROM COMPASrun;")

        # COMPAS header
        compas_header = [i[0] for i in self.compas_database.description]

        # index needed from the header (remember that for mesa, m1i is the companion mass of COMPAS)
        names_to_match = ["companion_mass", "remnant_mass", "porb_pm", "e_pm"]
        names_on_mesa = ["m1i", "m2i", "porbi", "ei"]

        # one more keyword matching snippet
        keyword_match = {
            names_on_mesa[k]: name for k, name in enumerate(names_to_match)
        }

        # keyword index
        keyword_index = dict()

        # get indices for keywords
        for name in names_to_match:
            keyword_index[name] = -1

            for k, header in enumerate(compas_header):
                if header == name:
                    keyword_index[name] = k
                    break

        # get final values of the COMPAS database (remnant_mass, companion_mass, a_pm, e_pm) -> (m1i, m2i, ai, ei)
        data = self.compas_database.fetchall()

        # results holds the run_name of the MESA simulation and a counter that tells us how many times we reproduced
        # the binary in the COMPAS database
        results = dict()

        # test with this case: m1_150.0_m2_20.0_initial_period_in_days_1000.00_initial_eccentricity_0.7
        if do_test:
            values_to_match = {
                "remnant_mass": 19.0,
                "companion_mass": 150.0,
                "porb_pm": 1000e0,
                "e_pm": 0.7,
            }

        # loop over each element of the COMPAS database
        for datum in data:
            # find the name of the MESA run closest to the COMPAS binary system
            run_name = self.do_single_matchmake(
                datum=datum,
                keyword_index=keyword_index,
                keyword_match=keyword_match,
                names_on_mesa=names_on_mesa,
            )

            # for nearest_neighbour method, just make a new SQLite database in which there is a row
            # with the number of times each element has repeated
            if self.interpolation_method == "nearest_neighbour":
                self.mesa_database.execute(
                    f"select run_name, m1i, m2i, porbi, ei from mesarun where run_name = '{run_name}'"
                )
                mesa_run = self.mesa_database.fetchall()

                # store thm in the results dict
                if not run_name in results.keys():
                    results[run_name] = dict()
                    results[run_name]["m1i"] = mesa_run[0][1]
                    results[run_name]["m2i"] = mesa_run[0][2]
                    results[run_name]["porbi"] = mesa_run[0][3]
                    results[run_name]["ei"] = mesa_run[0][4]
                    results[run_name]["weight"] = 1
                else:
                    results[run_name]["weight"] += 1

            else:
                sys.exit("only nearest_neighbour is ready to use")

        k = 0
        for key, value in results.items():
            print(key, value)
            k += 1
            if k > 10:
                sys.exit()

    def do_matchmake(
        self,
    ) -> None:
        """Matchmaking algorithm between binaries"""


        def TOLOG(binary):
            for (key, val) in binary.items():
                if key in LOGKEYS:
                    binary[key] = np.log10(val)
            return binary

        def TOLIN(binary):
            for (key, val) in binary.items():
                if key in LOGKEYS:
                    binary[key] = float('{:.2f}'.format(10**val))
            return binary

        def nearest_neighbour(binary, grid):
            """btain nearest neighbour with weight = 1.0"""

            neigh = {}
            for par, val in binary.items():
                neigh[par] = grid[par][np.argmin(np.abs(grid[par]-val))]

            neigh['weight'] = 1.0

            return neigh

        def weighted_neighbours(binary, grid):
            """Find 2**N neighbours and their corresponding weights"""

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
            neighs, weights = [], []
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
                neighs.append(neigh)
                weights.append(1/weight)

            weights/=sum(weights)

            for i, neigh in enumerate(neighs):
                neigh['weight'] = weights[i]

            return neighs

        logger.info("start matchmaking process")

        SETLOG = True
        LOGKEYS = ['m1i', 'm2i', 'porbi']

        with open('/home/asimazbunzel/Projects/HMXB-NSBH/data/complete-grid.yaml', 'r') as f:
            grid = yaml.load(f, Loader=yaml.FullLoader)

        for key in grid.keys():
            grid[key] = np.array(grid[key])

            if SETLOG:
                if key in LOGKEYS:
                    grid[key] = np.log10(grid[key])

        self.mesa_database.execute("SELECT * FROM MESArun;")
        self.compas_database.execute("SELECT * FROM COMPASrun;")

        # COMPAS header
        compas_header = [i[0] for i in self.compas_database.description]

        # index needed from the header (remember that for mesa, m1i is the companion mass of COMPAS)
        names_to_match = ["companion_mass", "remnant_mass", "porb_pm", "e_pm"]
        names_on_mesa = ["m1i", "m2i", "porbi", "ei"]

        # one more keyword matching snippet
        headers_mapping = {
            name: names_on_mesa[k] for k, name in enumerate(names_to_match)
        }

        # keyword index
        keyword_index = dict()

        # get indices for keywords
        for name in names_to_match:
            keyword_index[name] = -1

            for k, header in enumerate(compas_header):
                if header == name:
                    keyword_index[name] = k
                    break

        # get final values of the COMPAS database (remnant_mass, companion_mass, a_pm, e_pm) -> (m1i, m2i, ai, ei)
        data = self.compas_database.fetchall()

        # results holds the run_name of the MESA simulation and a counter that tells us how many times we reproduced
        # the binary in the COMPAS database
        results = dict()
        results["run_name"] = []
        results["weight"] = []

        for datum in data:
            # store values to be matched in a dictionary
            binary_to_match = dict()

            for k, value in enumerate(datum):
                for mkey, mvalue in keyword_index.items():
                    if k == mvalue:
                        binary_to_match[headers_mapping[mkey]] = value

            # log into binary
            if SETLOG:
                binary_to_match = TOLOG(binary_to_match)

            # get nearest neighbour
            closest_neighbour = nearest_neighbour(binary_to_match, grid)
            if SETLOG:
                closest_neighbour = TOLIN(closest_neighbour)

            # get near neighbours
            weighted_close_neighbours = weighted_neighbours(binary_to_match, grid)
            if SETLOG:
                for k, neighbour in enumerate(weighted_close_neighbours):
                    weighted_close_neighbours[k] = TOLIN(neighbour)

            if SETLOG:
                binary_to_match = TOLIN(binary_to_match)


            # depending on the interpolation method, compute different tables
            if self.interpolation_method == "nearest_neighbour":
                # string to send to sqlite3
                string = ""
                for name in names_on_mesa:
                    string += f"ABS({name} - {closest_neighbour[name]})*ABS({name} - {closest_neighbour[name]}) + "
                string = string[:-3]

                # get closest point in the grid
                self.mesa_database.execute(
                    f"SELECT run_name, {string} as dist FROM MESArun ORDER BY {string} DESC"
                )
                closest_value = self.mesa_database.fetchall()[-1]
                run_name = closest_value[0]

                debug_string = (
                    f"closest point to ({binary_to_match['m1i']:.2f},"
                    f" {binary_to_match['m2i']:.2f}, {binary_to_match['porbi']:.2f},"
                    f" {binary_to_match['ei']:.2f}) is: `{run_name}`"
                )
                logger.debug(debug_string)

                # self.mesa_database.execute(
                #     f"select run_name, m1i, m2i, porbi, ei from mesarun where run_name = '{run_name}'"
                # )
                # mesa_run = self.mesa_database.fetchall()

                # store thm in the results dict
                if not run_name in results["run_name"]:
                    results["run_name"].append(run_name)
                    results["weight"].append(1)
                else:
                    for k, name in enumerate(results["run_name"]):
                        if run_name == "name":
                            break
                    results["weight"][k] += 1

            else:
                for neigh in weighted_close_neighbours:
                    # string to send to sqlite3
                    string = ""
                    for name in names_on_mesa:
                        string += f"ABS({name} - {neigh[name]})*ABS({name} - {neigh[name]}) + "
                    string = string[:-3]

                    # get closest point in the grid
                    self.mesa_database.execute(
                        f"SELECT run_name, {string} as dist FROM MESArun ORDER BY {string} DESC"
                    )
                    closest_value = self.mesa_database.fetchall()[-1]
                    run_name = closest_value[0]

                    debug_string = (
                        f"closest point to ({binary_to_match['m1i']:.2f},"
                        f" {binary_to_match['m2i']:.2f}, {binary_to_match['porbi']:.2f},"
                        f" {binary_to_match['ei']:.2f}) is: `{run_name}`"
                    )
                    logger.debug(debug_string)

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

