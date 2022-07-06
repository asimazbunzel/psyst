TODO
---

- [ ] create classes to load databases of stellar evolutions from COMPAS and MESA

- [x] think of a way to include a VIRTUAL GENERATED ALWAYS column in the MESA SQLite database.
      it has to compute the Euclidean distance between points in 4 different columns of the
      database and 4 others coming from outside it

- [ ] using the previously created column, select those with the smallest distance value (nearest
      neighbour method, for now). the most important column to get is the `run_name` which is the
      `id` to match in the other tables of the MESA database
