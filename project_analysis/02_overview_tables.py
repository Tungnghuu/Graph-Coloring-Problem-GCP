if __package__:
    from .analysis_core import ROOT, load_runs, read_csv
    from .reports import overview
else:
    from analysis_core import ROOT, load_runs, read_csv
    from reports import overview
if __name__=='__main__': overview(load_runs(),read_csv(ROOT/'processed'/'data_quality.csv')); print('Overview tables written.')
