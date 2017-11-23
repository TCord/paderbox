#!/usr/bin/env bash

renice -n 20 $$

# paths
TOOLBOX=./toolbox

CUDA_PATH=/usr/local/cuda
LD_LIBRARY_PATH=$CUDA_PATH/lib64:${LD_LIBRARY_PATH}
PATH=$CUDA_PATH/bin:$PATH
export PATH
export LD_LIBRARY_PATH

source /net/ssd/software/conda/bin/activate

# set a prefix for each cmd
green='\033[0;32m'
NC='\033[0m' # No Color
trap 'echo -e "${green}$ $BASH_COMMAND ${NC}"' DEBUG

# Force Exit 0
trap 'exit 0' EXIT SIGINT SIGTERM

# Use a pseudo virtualenv, http://stackoverflow.com/questions/2915471/install-a-python-package-into-a-different-directory-using-pip
mkdir -p venv
export PYTHONUSERBASE=$(readlink -m venv)

# Refresh files...
ls /net/ssd/software/conda/lib/python3.6/lib-dynload/../../ > /dev/null

# Refresh toolbox
# TODO: install all dependencies and add --no-deps option
pip uninstall --quiet --yes nt
pip show nt
pip install  --quiet --user -e ${TOOLBOX}
pip show nt

# Tear down everything (uninstall packages), to be called at the end of the jenkins script
function tear_down {
    # Store pip packages
    pip freeze > pip.txt

    # Uninstall packages
    pip uninstall --quiet --yes nt
}