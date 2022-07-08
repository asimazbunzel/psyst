SHELL=bash
CONDA_ROOT=${HOME}/.local/bin/conda

install:
	pip3 install .

test:
	matchmaking-manager -d -C example/config.yaml
