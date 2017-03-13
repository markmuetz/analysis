Running Interactively
=====================

To do this on ARCHER:

    cd $WORKDIR/archer_analysis
    module load anaconda
    ipython
    
```python
import archer_analysis

da = archer_analysis.analyze_dump.DumpAnalyzer(user, suite, expt, dump_file, results_dir)
da.load()
da.run()
da.save()
```