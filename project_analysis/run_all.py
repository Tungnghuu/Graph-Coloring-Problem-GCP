from pathlib import Path
import argparse
from datetime import datetime, timezone
if __package__:
    from . import reports
    from . import analysis_core as core
else:
    import reports
    import analysis_core as core

def archive_outputs(output):
    """Keep prior generated reports out of the current gallery and table scans."""
    names=('figures', 'tables', 'findings.md', 'figure_status.csv')
    existing=[output/name for name in names if (output/name).exists()]
    if existing:
        archive=output/'archive'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
        archive.mkdir(parents=True)
        for path in existing:
            path.rename(archive/path.name)

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--source',type=Path,action='append')
    p.add_argument('--data',type=Path,default=core.PROJECT/'data')
    p.add_argument('--output',type=Path,default=core.ROOT)
    p.add_argument('--expected',type=Path)
    p.add_argument('--part1-method',choices=('Repeated','Binary','Incremental'),default='Repeated')
    mode=p.add_mutually_exclusive_group()
    mode.add_argument('--verified-only',action='store_true',help='Require verified metadata; skip unavailable figures')
    mode.add_argument('--exploratory',action='store_true',help='Use historical data with explicit caveats (default)')
    args=p.parse_args()
    reports.ROOT=args.output; reports.FIG=args.output/'outputs'/'figures'; reports.TABLES=args.output/'outputs'/'tables'
    runs,attempts,issues=core.preprocess(args.source or [core.PROJECT/'results',core.ROOT/'raw_results'],args.data,args.output/'processed',args.expected)
    archive_outputs(args.output/'outputs')
    reports.FIGURE_STATUS.clear()
    reports.overview(runs,issues)
    exploratory=not args.verified_only
    reports.part1(runs,args.part1_method,exploratory)
    reports.part2a(runs,exploratory)
    reports.part2b(runs,exploratory=exploratory)
    reports.part3(); reports.conclusions(runs); reports.empirical_findings(); reports.write_figure_status()
    members=[]
    for path in sorted(reports.TABLES.glob('*_membership.csv')):
        for row in core.read_csv(path): members.append(dict(comparison=path.stem,**row))
    core.write_csv(args.output/'processed'/'comparison_membership.csv',members,['comparison','Source','Graph','Included','Reason'])
    print(f'{len(runs)} runs, {len(attempts)} attempts, {len(issues)} notices. Output: {args.output}')

if __name__=='__main__': main()