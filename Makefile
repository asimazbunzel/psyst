SHELL=bash
CONDA_ROOT=${HOME}/.local/bin/conda

install:
	source ${CONDA_ROOT}/bin/activate && pip3 install .
