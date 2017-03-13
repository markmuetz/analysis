# N.B. user has no control over this.
export RESULTS_DIR=../results/$SUITE

# Make sure anaconda (and iris etc.) is loaded.
# N.B. module anaconda-compute is for use on the *compute* nodes,
# this is running in the serial queue.
module load anaconda
