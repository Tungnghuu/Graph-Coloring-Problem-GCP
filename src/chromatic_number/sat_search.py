from time import perf_counter
from src.chromatic_number.base import ChromaticNumberSolver as Base
from src.chromatic_number.results import ResultsWriter
from src.solver.baseline import SATSolver, Solver
from src.utils.graph_validation import is_valid_coloring


def run_sat_search(strategy, graph, encoding, bounds_method, results_path=None, *,
                   solver: Solver | None = None, solver_name='g3', time_limit=60,
                   encoding_time_limit=60, total_time_limit=None, bounds_time=0):
    if strategy not in ('binary','repeated'): raise ValueError('unknown strategy')
    bound_start = perf_counter()
    lb, ub = Base._find_bounds(graph,bounds_method)
    if hasattr(bounds_method,"find_bounds") or hasattr(bounds_method,"find_lower_bound"):
        bounds_time += perf_counter() - bound_start
    for limit in (time_limit,encoding_time_limit,total_time_limit): Base._validate_time_limit(limit)
    Base._validate_bounds_time(bounds_time)
    backend = solver or SATSolver(solver_name)
    method = 'BinarySearchSAT' if strategy=='binary' else 'RepeatedSolver'
    writer = ResultsWriter(results_path,dict(initial_lb=lb,initial_ub=ub,bounds_time=bounds_time,
        solver=getattr(backend,'solver_name',type(backend).__name__),time_limit=time_limit,
        encoding_time_limit=encoding_time_limit,total_time_limit=total_time_limit,
        symmetry_breaking=getattr(encoding,'symmetry_breaking',None),
        timing='SAT: separate setup/solve; native: backend call includes native overhead',
        parameters='one worker; other backend defaults')) if results_path else None
    deadline = perf_counter()+total_time_limit if total_time_limit else None
    graph.colors=[None]*graph.n
    best=None; status=None; first=True; timeout=False; reason='search_exhausted'
    low,high=lb,ub
    try:
        while low<=high:
            k=(low+high)//2 if strategy=='binary' else high
            bt=bounds_time if first else 0
            model,et,encoded=Base._encode(encoding,graph,k,encoding_time_limit,deadline)
            if not encoded:
                Base._record_encoding_timeout(writer,method,encoding,k,bt,et,
                    phase="total" if deadline is not None and perf_counter()>=deadline else "encoding")
                Base._release_encoding(encoding,backend)
                timeout=True; status='TIMEOUT'; reason='encoding_or_total_limit'; break
            try:
                remaining=deadline-perf_counter() if deadline else None
                if remaining is not None and remaining<=0:
                    if writer: writer.save(dict(method=method,encoding=type(encoding).__name__,k=k,status='TIMEOUT',
                        bounds_time=bt,encoding_time=et,total_time=bt+et,solver_called=False,
                        timeout_phase='total',timed_out=True,valid_coloring=False))
                    timeout=True; status='TIMEOUT'; reason='total_limit'; break
                limit=min(time_limit,remaining) if time_limit is not None and remaining is not None else (remaining if time_limit is None else time_limit)
                start=perf_counter(); result=backend.solve(model,limit); elapsed=perf_counter()-start
                nv,nc=backend.model_size(model)
                valid=False
                if result.satisfiable is True:
                    graph.colors=encoding.decode_model(result.solution)
                    valid=is_valid_coloring(graph)
                    if not valid: raise ValueError('backend returned invalid coloring')
                    best=min(best,k) if best is not None else k
                status=result.status
                timeout=timeout or result.timed_out
                st=result.solving_time if result.solving_time is not None else elapsed
                if writer: writer.save(dict(method=method,encoding=type(encoding).__name__,k=k,status=status,
                    num_variables=nv,num_clauses=nc,valid_coloring=valid,bounds_time=bt,encoding_time=et,
                    solving_time=st,setup_time=result.setup_time,total_time=bt+et+elapsed,solver_called=True,
                    timeout_phase='solving' if result.timed_out else '',timed_out=result.timed_out,
                    backend_status=result.backend_status,best_k=best))
                first=False
                if result.satisfiable is True: high=k-1
                elif result.satisfiable is False:
                    low=k+1; lb=max(lb,k+1)
                    if strategy=='repeated': break
                else:
                    reason='solver_timeout' if result.timed_out else 'solver_unknown'
                    if strategy=='binary': low=k+1
                    else: break
            finally:
                backend.close(model); encoding.release()
        if timeout: status='TIMEOUT'
        if writer: writer.finish(completion='Timeout' if timeout else ('Completed' if reason=='search_exhausted' else 'Partial'),
            lower_bound=lb,best_k=best,reason=reason)
        return best,status
    except Exception as error:
        Base._release_encoding(encoding,backend)
        if writer: writer.finish(completion='Error',lower_bound=lb,best_k=best,reason=type(error).__name__+': '+str(error))
        raise