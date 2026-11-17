if __package__:
    from .analysis_core import load_runs
    from .reports import part2b
else:
    from analysis_core import load_runs
    from reports import part2b
if __name__=='__main__': part2b(load_runs()); print('Backend reports written.')