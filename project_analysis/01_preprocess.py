from pathlib import Path
import argparse
if __package__:
    from .analysis_core import PROJECT, ROOT, preprocess
else:
    from analysis_core import PROJECT, ROOT, preprocess

def main():
    p=argparse.ArgumentParser(description='Normalize experiment CSV files.')
    p.add_argument('--source',type=Path,action='append',help='Input directory; repeat for multiple sources')
    p.add_argument('--data',type=Path,default=PROJECT/'data')
    p.add_argument('--output',type=Path,default=ROOT/'processed')
    p.add_argument("--expected",type=Path,help="Explicit expected-run CSV manifest")
    args=p.parse_args()
    runs,attempts,issues=preprocess(args.source or [PROJECT/'results', ROOT/'raw_results'],args.data,args.output,args.expected)
    print(f'Preprocessed {len(runs)} runs, {len(attempts)} attempts; {len(issues)} quality notices.')
if __name__=='__main__': main()