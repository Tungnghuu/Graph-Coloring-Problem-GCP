if __package__:
    from .analysis_core import load_runs
    from .reports import part1
else:
    from analysis_core import load_runs
    from reports import part1
if __name__=='__main__': part1(load_runs()); print('Encoding reports written.')