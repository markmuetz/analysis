Running Interactively
=====================

To do this on ARCHER:

    cd <archer_analysis-install-dir>
    module load anaconda
    ipython
    
```python
from archer_analysis.restart_dump_analysis import RestartDumpAnalyzer

rda = RestartDumpAnalyzer(user, suite, expt, dump_file, results_dir)
rda.load()
rda.run()
rda.save()
```
