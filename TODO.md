TODO
---

- [x] create classes to load databases of stellar evolutions from COMPAS and MESA

- [x] classes should be printed to standard output

- [x] also, these classes must be in the same format (SQLite object, pandas dataframe,
      dictionary, ...) ➡  ~~dataframe is used (for now)~~ SQLite objects

- [x] ~~think of a way to include a VIRTUAL GENERATED ALWAYS column in the MESA SQLite database.
      it has to compute the Euclidean distance between points in 4 different columns of the
      database and 4 others coming from outside it~~

- [x] ~~using the previously created column, select those with the smallest distance value (nearest
      neighbour method, for now). the most important column to get is the `run_name` which is the
      `id` to match in the other tables of the MESA database~~

- [x] not just nearest neighbour but also all 16 close neighbours are now computed thanks to Fede's
      algorithm. Also, the weight of each of them is known 🔥

- [x] with the nearest method solved for each binary of the COMPAS database, create a new table in
      which we count the number of repetitions of each row of the MESA database, like weighting the
      population

- [x] clean up code, in particular the matchmaking module

- [ ] change logic of matchmaking to implement multiprocessing to work a little bit more
      inteligently

- [ ] think of the proper way to write information to file while multiprocessing is working on the
      grid

- [ ] document most of the code, some methods seem a little bit obscure
