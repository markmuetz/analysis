Installation
============

On PUMA:

    cd roses/<suite-id>
    git clone https://github.com/markmuetz/archer_analysis
    cp -r archer_analysis/app/analysis/ app/

Edit rose-suite.conf to add in some variables to control the analysis.
Edit suite.rc to add in some cylc tasks to launch the analysis.
See u-al000 for some ideas as to how to do this.

DOCS
====

[docs](docs/index.md)
