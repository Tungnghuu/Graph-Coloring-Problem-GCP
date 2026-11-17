import argparse
import csv
import json
from pathlib import Path
import sys
from time import perf_counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.benchmark.experiment_runner import get_search_method, ALL_ENCODINGS
from src.chromatic_number.bound_methods.combined import CombinedBounds
from src.chromatic_number.results import ResultsWriter
from src.chromatic_number.base import ChromaticNumberSolver as Base
from src.solver.baseline import SATSolver
from src.encoding import POHPEncoding
from src.utils.graph_io import read_col
from src.utils.graph_validation import is_valid_coloring

def sweep(graph_path,out,ks,solve_limit,encoding_limit):
    graph=read_col(graph_path); backend=SATSolver('g3')
    path=out/graph_path.parent.name/(graph_path.stem+'_POHP_k_sweep.csv')
    if path.exists(): raise FileExistsError(path)
    writer=ResultsWriter(path,dict(solver='g3',time_limit=solve_limit,encoding_time_limit=encoding_limit,
        total_time_limit=None,symmetry_breaking=True,parameters='one worker; other backend defaults',
        graph=str(graph_path),experiment='independent Repeated POHP k sweep'))
    timed=False
    try:
        for k in ks:
            enc=POHPEncoding(); start=perf_counter()
            model,et,ok=Base._encode(enc,graph,k,encoding_limit,None)
            if not ok:
                Base._record_encoding_timeout(writer,'RepeatedSolver',enc,k,0,et); timed=True; enc.release(); continue
            try:
                result=backend.solve(model,solve_limit); graph.colors=[None]*graph.n
                if result.satisfiable is True: graph.colors=enc.decode_model(result.solution)
                valid=is_valid_coloring(graph) if result.satisfiable is True else False
                if result.satisfiable is True and not valid: raise ValueError('invalid coloring')
                nv,nc=backend.model_size(model)
                writer.save(dict(method='RepeatedSolver',encoding='POHPEncoding',k=k,status=result.status,
                    num_variables=nv,num_clauses=nc,valid_coloring=valid,bounds_time=0,encoding_time=et,
                    setup_time=result.setup_time,solving_time=result.solving_time,total_time=perf_counter()-start,
                    solver_called=True,timed_out=result.timed_out,timeout_phase='solving' if result.timed_out else '',backend_status=result.backend_status))
                timed=timed or result.timed_out
            finally: backend.close(model); enc.release()
        writer.finish(completion='Timeout' if timed else 'Completed',lower_bound=None,best_k=None,reason='requested_k_range_finished')
    except Exception as error:
        writer.finish(completion='Error',lower_bound=None,best_k=None,reason=str(error)); raise
    return path

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--graph',type=Path,action='append',default=[])
    p.add_argument('--representatives',type=Path,help='CSV with path,k_min,k_max; one graph per bucket')
    p.add_argument('--sweep-only',action='store_true')
    p.add_argument('--output',type=Path,required=True,help='New directory, separate from historical results')
    p.add_argument('--native',action='store_true')
    p.add_argument('--solve-limit',type=float,default=30)
    p.add_argument('--encoding-limit',type=float,default=30)
    p.add_argument('--run-limit',type=float,default=120)
    p.add_argument('--sweep',action='store_true')
    p.add_argument('--k-min',type=int); p.add_argument('--k-max',type=int)
    args=p.parse_args()
    ranges={}
    if args.representatives:
        with args.representatives.open() as f:
            for row in csv.DictReader(f):
                graph_path=Path(row["path"]); args.graph.append(graph_path)
                ranges[str(graph_path)]=(int(row["k_min"]),int(row["k_max"]))
    if not args.graph: p.error("provide --graph or --representatives")
    if args.output.exists(): p.error('output must be a new directory; existing results are preserved')
    args.output.mkdir(parents=True)
    expected=[]; errors=[]
    for path in args.graph:
        graph=read_col(path); start=perf_counter(); bounds=CombinedBounds().find_bounds(graph); bt=perf_counter()-start
        if args.sweep or args.sweep_only:
            lo=args.k_min if args.k_min is not None else max(1,bounds[0]-2)
            hi=args.k_max if args.k_max is not None else min(graph.n,bounds[1]+2)
            lo,hi=ranges.get(str(path),(lo,hi))
            if lo>hi: p.error('k-min must be <= k-max')
            sweep(path,args.output/'exp',range(lo,hi+1),args.solve_limit,args.encoding_limit)
        if args.sweep_only: continue
        for method in ('Repeated','Binary','Incremental'):
            for name,enc_cls,solver_cls in ALL_ENCODINGS:
                if name not in ('SAT','POP','POHP') and (not args.native or method=='Incremental'): continue
                output=args.output/method/path.parent.name/(path.stem+'_'+name+'_res.csv')
                expected.append(dict(graph_id=path.parent.name+'/'+path.name,graph=path.stem,group=path.parent.name,method=method,encoding=name))
                try:
                    options=dict(time_limit=args.solve_limit,encoding_time_limit=args.encoding_limit,total_time_limit=args.run_limit,bounds_time=bt)
                    if method!='Incremental': options['solver']=solver_cls()
                    get_search_method(method.lower()).find_chromatic_number(graph,enc_cls(),bounds,output,**options)
                except Exception as error: errors.append(dict(graph=str(path),method=method,encoding=name,error=repr(error)))
    # Keep manifest outside the raw CSV tree to avoid treating it as results.
    manifest=args.output.with_suffix('.expected.csv')
    with manifest.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['graph_id','graph','group','method','encoding']); writer.writeheader(); writer.writerows(expected)
    args.output.with_suffix('.errors.json').write_text(json.dumps(errors,indent=2))
    print(f'Expected runs: {len(expected)}; errors: {len(errors)}; manifest: {manifest}')
    if errors: print(json.dumps(errors,indent=2))

if __name__=='__main__': main()