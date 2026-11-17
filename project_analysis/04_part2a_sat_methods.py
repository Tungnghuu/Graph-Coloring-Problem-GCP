if __package__:
    from .analysis_core import load_runs
    from .reports import part2a
else:
    from analysis_core import load_runs
    from reports import part2a
if __name__=='__main__': part2a(load_runs()); print('Search method reports written.')