Installation
============

On ARCHER:

    cd $WORKDIR
    git clone https://github.com/markmuetz/archer_analysis
    cd archer_analysis
    ./initial_setup.sh
    
Running
=======

    cd $WORKDIR/archer_analysis/run_control/
    # Edit settings.sh
    qsub analyze_dump.pbs

Monitor progress:

    watch qstat -au $USER
    <ctrl-C>
    # After it has finished:
    qsub plot_dump_analysis.pbs
    
Output
------

Goes in `output`. This is the output and error streams from the qsub command, and the executed script (with the job ID).

Results
-------

Goes into a directory under `results`, e.g. `results/u-aj703`. Any results files will go here.

Updating
========

    cd $WORKDIR/archer_analysis
    git pull
    

TODO
====

[TODOs](docs/todo.md)
