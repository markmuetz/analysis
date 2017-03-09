Installation
============

On ARCHER:

    cd $WORKDIR
    git clone https://github.com/markmuetz/analysis
    cd analysis
    ./initial_setup.sh
    
Running
=======

    cd $WORKDIR/analysis
    # Edit settings.sh
    qsub analyze_dump.pbs
    
Output
------

Goes in `output`. This is the output and error streams from the qsub command, and the executed script (with the job ID).

Results
-------

Goes into a directory under `results`, e.g. `results/u-aj703`.