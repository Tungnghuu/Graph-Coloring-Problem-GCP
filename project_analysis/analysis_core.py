from collections import Counter, defaultdict
from pathlib import Path
import csv
import hashlib
import json
import math
import statistics

ROOT = Path(__file__).resolve().parent
PROJECT = ROOT.parent
ENCODINGS = ('SAT','POP','POHP','Gurobi_ILP','CPLEX_MIP','CPLEX_CP')
METHODS = {'RepeatedSolver':'Repeated','RepeatedSAT':'Repeated','IncrementalSAT':'Incremental','BinarySearchSAT':'Binary'}
FIELDS = ['source','run_id','graph','graph_id','group','vertices','edges','method','encoding','backend',
 'config_id','comparison_config','metadata_verified','completion','termination_reason','attempts','solver_calls',
 'best_k','lower_bound','gap','proof','timeout','timeout_phase','encoding_time','setup_time','solving_time',
 'bounds_time','recorded_time','total_time','time_basis','num_variables','num_clauses','first_k','quality']
ATTEMPT_FIELDS = ['source','graph','graph_id','group','vertices','edges','method','encoding','backend',
 'k','status','num_variables','num_clauses','valid_coloring','bounds_time','encoding_time','setup_time',
 'solving_time','total_time','solver_called','timed_out','timeout_phase','best_k','backend_status']

def write_csv(path, rows, fields):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=csv.DictWriter(f,fieldnames=fields,extrasaction='ignore'); writer.writeheader(); writer.writerows(rows)

def read_csv(path):
    with path.open(newline='',encoding='utf-8-sig') as f: return list(csv.DictReader(f))

def number(value):
    try:
        x=float(value)
        return x if math.isfinite(x) else None
    except (ValueError,TypeError): return None

def integer(value):
    x=number(value)
    return int(x) if x is not None and x.is_integer() else None

def flag(value):
    if isinstance(value,bool): return value
    return {'true':True,'false':False}.get(str(value).lower())

def dataset_index(data):
    index=defaultdict(list)
    for path in sorted(data.rglob('*.col')):
        try:
            for line in path.read_text().splitlines():
                p=line.split()
                if p and p[0]=='p' and len(p)>=4:
                    index[path.stem].append((path.parent.name,int(p[2]),int(p[3]),str(path.relative_to(data))))
                    break
        except (OSError,ValueError,UnicodeError): continue
    return index

def identity(path,rows):
    name=path.stem.removesuffix('_res')
    encoding=next((e for e in sorted(ENCODINGS,key=len,reverse=True) if name.endswith('_'+e)),'')
    graph=name[:-(len(encoding)+1)] if encoding else name
    method=METHODS.get(rows[0].get('method',''),'') if rows else ''
    method=method or next((m for m in ('Binary','Repeated','Incremental') if m in path.parts),'')
    return graph,method,encoding,'PySAT-unspecified' if encoding in ('SAT','POP','POHP') else encoding

def measured_sum(rows,key):
    values=[r.get(key) for r in rows]
    return sum(values) if values and all(v is not None for v in values) else None

def summarize(attempts, meta=None):
    meta=meta or {}; first=attempts[0] if attempts else {}
    sat=[r['k'] for r in attempts if r['status']=='SAT' and r.get('valid_coloring') is True]
    # An incumbent at a timeout must have its own explicit color count.
    sat += [r['best_k'] for r in attempts if r.get('valid_coloring') is True and r.get('best_k') is not None]
    best=min(sat) if sat else None
    n=first.get('vertices')
    candidates=[k for k in [integer(meta.get('initial_lb')),integer(meta.get('final_lb'))] if k is not None]
    candidates += [r['k']+1 for r in attempts if r['status']=='UNSAT']
    if n is not None: candidates.append(1 if n>0 else 0)
    lower=max(candidates) if candidates else None
    inconsistent=best is not None and lower is not None and lower>best
    proof='unknown' if best is None or inconsistent else ('optimal' if lower==best else 'feasible')
    timeout=any(r['status']=='TIMEOUT' or r.get('timed_out') is True for r in attempts) or meta.get('completion')=='Timeout'
    completion=meta.get('completion')
    if completion not in ('Completed','Partial','Timeout','Missing','Error'):
        completion='Error' if any(r['status']=='ERROR' for r in attempts) else ('Timeout' if timeout else ('Completed' if proof=='optimal' else 'Partial'))
    bt=[r.get('bounds_time') for r in attempts]
    quality=[]
    if inconsistent: quality.append('contradictory_bounds')
    if any(x is not None and x>0 for x in bt[1:]): quality.append('repeated_bounds_time')
    recorded=measured_sum(attempts,'total_time')
    wall=number(meta.get('total_wall_time'))
    return dict(attempts=len(attempts),solver_calls=sum(r['solver_called'] for r in attempts) if attempts and all(r.get('solver_called') is not None for r in attempts) else None,
        best_k=best,lower_bound=lower,gap=(best-lower)/best if best and lower is not None and not inconsistent else (0 if best==lower==0 else None),
        proof=proof,timeout=timeout,completion=completion,termination_reason=meta.get('termination_reason','not recorded'),
        timeout_phase=','.join(sorted({r.get('timeout_phase','') for r in attempts if r.get('timeout_phase')})),
        encoding_time=measured_sum(attempts,'encoding_time'),setup_time=measured_sum(attempts,'setup_time'),
        solving_time=measured_sum(attempts,'solving_time'),bounds_time=bt[0] if bt else None,
        recorded_time=recorded,total_time=wall if wall is not None else recorded,time_basis='wall+precomputed_bounds' if wall is not None else 'recorded_components',
        num_variables=first.get('num_variables'),num_clauses=first.get('num_clauses'),first_k=first.get('k'),quality=';'.join(quality))

def preprocess(sources,data,out,expected=None):
    index=dataset_index(data); runs=[]; attempts=[]; issues=[]; sweeps=[]; configurations=[]; inventory=[]
    paths=sorted({p.resolve() for source in sources if source.exists() for p in source.rglob('*.csv')})
    for path in paths:
        source=str(path)
        try: rows=read_csv(path)
        except (OSError,UnicodeError,csv.Error) as error:
            issues.append(dict(source=source,issue='unreadable',detail=str(error))); rows=[]
        is_sweep=path.stem.endswith('_k_sweep')
        graph,method,enc,backend=identity(path,rows)
        if is_sweep:
            graph=Path(rows[0].get('graph') or path.stem.removesuffix('_POHP_k_sweep')).stem if rows else path.stem.removesuffix('_POHP_k_sweep')
            method,enc,backend='K-sweep','POHP','PySAT-unspecified'
        matches=index.get(graph,[])
        local=[m for m in matches if m[0]==path.parent.name]
        if len(local)==1: matches=local
        group,n,m,gid=matches[0] if len(matches)==1 else ('',None,None,graph)
        meta={}
        if path.with_suffix('.meta.json').exists():
            try: meta=json.loads(path.with_suffix('.meta.json').read_text())
            except (ValueError,OSError) as error: issues.append(dict(source=source,issue='invalid_manifest',detail=str(error)))
        backend=meta.get('solver',backend)
        verified=meta.get('schema_version')==2 and all(k in meta for k in ('config_id','environment','implementation','time_limit','encoding_time_limit','total_time_limit'))
        comp={k:meta.get(k) for k in ('environment','implementation','time_limit','encoding_time_limit','total_time_limit','symmetry_breaking','parameters','initial_lb','initial_ub')}
        comparison=hashlib.sha256(json.dumps(comp,sort_keys=True).encode()).hexdigest()[:16] if verified else 'unverified'
        base=dict(source=source,run_id=meta.get('run_id',source),graph=graph,graph_id=gid,group=group,vertices=n,edges=m,
            method=method,encoding=enc,backend=backend,config_id=meta.get('config_id','unverified'),comparison_config=comparison,metadata_verified=verified)
        inventory.append(dict(source=source,schema='k_sweep' if is_sweep else ('v2' if meta else 'legacy'),rows=len(rows),graph_id=gid))
        configurations.append(dict(source=source,verified=verified,metadata=json.dumps(meta,sort_keys=True)))
        if len(matches)!=1: issues.append(dict(source=source,issue='graph_unresolved',detail=graph))
        parsed=[]
        for pos,row in enumerate(rows,2):
            k=integer(row.get('k')); status=str(row.get('status','')).upper()
            if k is None or k<0 or status not in ('SAT','UNSAT','TIMEOUT','UNKNOWN','ERROR'):
                issues.append(dict(source=source,issue='invalid_row',detail=f'line {pos}: k/status')); continue
            a=dict(base,k=k,status=status,valid_coloring=flag(row.get('valid_coloring')),solver_called=flag(row.get('solver_called')),
                timed_out=flag(row.get('timed_out')),timeout_phase=row.get('timeout_phase',''),backend_status=row.get('backend_status',''))
            if not is_sweep:
                row_method=METHODS.get(row.get('method',''),'')
                row_enc={'GurobiILP':'Gurobi_ILP','CPLEXMIP':'CPLEX_MIP','CPLEXCP':'CPLEX_CP'}.get(row.get('encoding','').removesuffix('Encoding'),row.get('encoding','').removesuffix('Encoding'))
                if (row_method and row_method!=method) or (row_enc and row_enc!=enc):
                    issues.append(dict(source=source,issue='identity_mismatch',detail=f'line {pos}')); continue
            for key in ('num_variables','num_clauses','bounds_time','encoding_time','setup_time','solving_time','total_time','best_k'):
                a[key]=number(row.get(key))
                if a[key] is not None and a[key]<0:
                    a[key]=None; issues.append(dict(source=source,issue='negative_value',detail=f'line {pos}: {key}'))
            if status=='SAT' and a['valid_coloring'] is False:
                issues.append(dict(source=source,issue='invalid_coloring',detail=f'line {pos}: SAT with invalid coloring'))
            parsed.append(a)
        if is_sweep:
            sweeps.extend(parsed)
            if not parsed: issues.append(dict(source=source,issue='missing_sweep',detail='No completed result'))
            continue
        summary=summarize(parsed,meta)
        if not rows:
            summary['completion']='Error' if meta.get('completion')=='Error' or any(i['source']==source and i['issue']=='unreadable' for i in issues) else 'Missing'
            issues.append(dict(source=source,issue='empty',detail='No completed attempt; see manifest for errors'))
        elif not parsed: summary['completion']='Error'
        if len(parsed)!=len(rows): summary['quality']+=';invalid_rows'
        if len(matches)!=1: summary['quality']+=';graph_unresolved'
        if any(i['source']==source and i['issue']=='identity_mismatch' for i in issues): summary['quality']+=';identity_mismatch'
        if any(i['source']==source and i['issue']=='invalid_coloring' for i in issues): summary['quality']+=';invalid_coloring'
        runs.append(dict(base,**summary)); attempts.extend(parsed)
    # Repeats remain visible; ambiguous repeated configurations are not ranked.
    keys=grouped(runs,lambda r:(r['graph_id'],r['method'],r['encoding'],r['backend'],r['config_id']))
    for key,rs in keys.items():
        if len(rs)>1:
            for r in rs:
                r['quality']+=';repeated_configuration'
                issues.append(dict(source=r['source'],issue='repeated_configuration',detail=str(key)))
    # Explicit manifest only: do not invent an expected Cartesian product.
    if expected:
        for e in read_csv(expected):
            if not any(all(str(r.get(k,''))==str(v) for k,v in e.items() if v and k in FIELDS) for r in runs):
                r={k:None for k in FIELDS}; r.update(e,source='',completion='Missing',proof='unknown',timeout=False,metadata_verified=False,quality='',attempts=0)
                runs.append(r)
    write_csv(out/'summary_runs.csv',runs,FIELDS); write_csv(out/'attempts.csv',attempts,ATTEMPT_FIELDS)
    write_csv(out/'k_sweep.csv',sweeps,ATTEMPT_FIELDS)
    write_csv(out/'data_quality.csv',issues,['source','issue','detail'])
    write_csv(out/'inventory.csv',inventory,['source','schema','rows','graph_id'])
    write_csv(out/'configurations.csv',configurations,['source','verified','metadata'])
    coverage=[]
    for key,rs in sorted(grouped(runs,lambda r:(r.get('method') or '',r.get('encoding') or '',r.get('group') or '')).items()):
        coverage.append(dict(zip(('method','encoding','group'),key),**{c:sum(r['completion']==c for r in rs) for c in ('Completed','Partial','Timeout','Missing','Error')}))
    write_csv(out/'coverage.csv',coverage,['method','encoding','group','Completed','Partial','Timeout','Missing','Error'])
    reruns=[]
    for r in runs:
        reasons=[]
        if not r['metadata_verified']: reasons.append('unverified historical configuration/timing/bounds')
        if r['encoding']=='POP' and not r['metadata_verified']: reasons.append('legacy POP implementation not certified as partial order')
        if r['completion'] in ('Missing','Error','Partial'): reasons.append(r['completion'])
        if r['quality']: reasons.append(r['quality'])
        if reasons: reruns.append(dict(source=r['source'],graph_id=r['graph_id'],method=r['method'],encoding=r['encoding'],reason='; '.join(reasons)))
    write_csv(out/'rerun_needed.csv',reruns,['source','graph_id','method','encoding','reason'])
    return runs,attempts,issues

def load_runs(out=ROOT/'processed'):
    rows=read_csv(out/'summary_runs.csv')
    numeric=('vertices','edges','attempts','solver_calls','best_k','lower_bound','gap','encoding_time','setup_time','solving_time','bounds_time','recorded_time','total_time','num_variables','num_clauses','first_k')
    for r in rows:
        for k in numeric: r[k]=number(r.get(k))
        for k in ('timeout','metadata_verified'): r[k]=flag(r.get(k)) is True
    return rows

def clean_runs(rows):
    fatal=('contradictory_bounds','identity_mismatch','invalid_rows','graph_unresolved','repeated_configuration','repeated_bounds_time','invalid_coloring')
    return [r for r in rows if r['graph'] and r['group'] and r['method'] and r['encoding'] in ENCODINGS
            and r['completion'] not in ('Missing','Error') and not any(q in (r['quality'] or '') for q in fatal)]

def median(values):
    values=[x for x in values if x is not None]
    return statistics.median(values) if values else None

def fmt(value):
    if value is None or value=='': return '--'
    if isinstance(value,float): return f'{value:.3g}'
    return str(value)

def table(name, headers, rows, caption, output=ROOT/'outputs'/'tables'):
    output.mkdir(parents=True,exist_ok=True)
    write_csv(output/(name+'.csv'), [dict(zip(headers,row)) for row in rows], headers)

def grouped(rows,key):
    d=defaultdict(list)
    for row in rows: d[key(row)].append(row)
    return d