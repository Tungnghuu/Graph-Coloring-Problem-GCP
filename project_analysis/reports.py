from collections import defaultdict
from itertools import combinations
from pathlib import Path
import csv
import statistics
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
if __package__:
    from .analysis_core import ROOT, clean_runs, grouped, median, table, read_csv, write_csv, number
else:
    from analysis_core import ROOT, clean_runs, grouped, median, table, read_csv, write_csv, number

FIG=ROOT/'outputs'/'figures'
TABLES=ROOT/'outputs'/'tables'
SAT=('SAT','POP','POHP')
P2B_ENCODINGS=SAT
P2B_METHODS=('Incremental','Repeated','Binary')
BACKENDS=(*SAT,'Gurobi_ILP','CPLEX_MIP','CPLEX_CP')

FIGURE_STATUS = []

def has_plotted_data(fig):
    """Empty scatter/line artists still set Axes.has_data(), so inspect their data."""
    return any(
        any(len(line.get_xdata()) and len(line.get_ydata()) for line in ax.lines)
        or any(len(collection.get_offsets()) for collection in ax.collections)
        or bool(ax.patches)
        or any(image.get_array().size for image in ax.images)
        for ax in fig.axes
    )

def figure_presentation(name):
    """Keep machine comparison IDs separate from reader-facing titles and files."""
    clean = name.replace('_exploratory', '')
    metrics = {
        'encoding_time': ('thoi_gian_ma_hoa', 'Encoding time comparison'),
        'solving_time': ('thoi_gian_giai', 'Solving time comparison'),
        'total_time': ('tong_thoi_gian', 'Total runtime comparison'),
        'timeout': ('ty_le_timeout', 'Timeout rate'),
        'num_variables': ('so_bien', 'Formula variable count'),
        'num_clauses': ('so_menh_de', 'Formula clause count'),
        'paired_time': ('thoi_gian_tung_do_thi', 'Runtime by graph'),
        'best_colors': ('so_mau_tot_nhat', 'Best color count by graph'),
        'attempts_time': ('so_lan_thu_va_thoi_gian', 'Attempts versus runtime'),
        'solver_calls_time': ('so_lan_goi_solver_va_thoi_gian', 'Solver calls versus runtime'),
        'outcomes': ('chat_luong_nghiem', 'Solution outcome breakdown'),
        'profile': ('hieu_nang_tuong_doi', 'Relative performance profile'),
        'gap': ('khoang_cach_toi_uu', 'Optimality gap'),
    }
    if clean.startswith(('p1_', 'p2a_', 'p2b_')):
        part, config, metric = clean.split('_', 2)
        slug, title = metrics[metric]
        label = config + ' SAT' if part == 'p1' else config
        filename = f'{part}_{slug}_{config.lower()}'
        if '_exploratory' not in name:
            filename += '_da_xac_minh'
        notes = ['Historical data; configuration is unverified.' if '_exploratory' in name
                 else 'Runs use verified configurations.']
        if part in ('p1','p2a','p2b') and metric in ('encoding_time','solving_time','total_time','paired_time'):
            notes.append('Includes proven-optimal and best-observed runs; k may differ across encodings or methods.')
        elif metric in ('encoding_time', 'solving_time', 'total_time', 'paired_time'):
            notes.append('Compares common proven-optimal runs only; n is the sample count.')
        if metric in ('paired_time', 'best_colors'):
            notes.append('Shows at most 12 graph IDs; circle = proven optimal, x = not proven optimal.')
        if metric in ('num_variables', 'num_clauses'):
            notes.append('First attempt, matched by graph and k; median at each vertex count.')
        if metric in ('attempts_time', 'solver_calls_time'):
            notes.append('x = timeout; observed runtime is not time-to-solution for timed-out runs.')
        if metric == 'attempts_time':
            notes.append('Runtime uses a symlog scale to retain very long runs.')
        if part == 'p2b' and metric == 'outcomes':
            notes.append('Best observed = lowest valid best_k for the same graph and method; it does not prove optimality.')
        if metric == 'profile':
            if part == 'p2b':
                notes.append('Includes proven-optimal and best-observed runs; k may differ across encodings.')
            else:
                notes.append('Success means proven optimal; the denominator includes all matched cases, including failures.')
        if metric == 'gap':
            notes.append('Feasible solutions may not be optimal; gap = (UB - LB) / UB.')
        return filename, f'{title} — {label}', ' '.join(notes)
    if clean.startswith('p3_'):
        graph = clean[3:]
        return ('p3_thoi_gian_theo_so_mau_k' + ('' if graph == 'runtime_k' else '_'+graph),
                'Runtime by color count k' + ('' if graph == 'runtime_k' else ' — '+graph),
                'Each k is an independent solve. One graph per group; historical configuration may be unverified.')
    return name, None, ''

AXIS_LABELS = {
    'encoding_time': 'Encoding time (s)', 'solving_time': 'Solving time (s)',
    'total_time': 'Total runtime (s)', 'best_k': 'Best color count',
    'num_variables': 'Variables', 'num_clauses': 'Clauses', 'Vertices': 'Vertices',
    'gap': 'Relative gap (UB - LB) / UB', 'attempts': 'Number of k attempts',
    'solver_calls': 'Solver calls', 'Observed timeout (%)': 'Timeout rate (%)',
    'Observed runtime (s), not time to solution for timeout': 'Observed runtime (s)',
    'Runs (%)': 'Runs (%)', 'Runtime / fastest proven runtime': 'Runtime / fastest runtime',
    'Fraction of all matched cases': 'Fraction of all matched cases', 'k': 'Color count k',
    'Runtime per k (s)': 'Runtime per k (s)',
}

def save(name):
    fig = plt.gcf()
    reason = getattr(fig, '_skip_reason', '')
    if not reason and not has_plotted_data(fig):
        reason = 'No matched observations with the required metric; see membership tables.'
    original_name = name
    original_title = ' / '.join(ax.get_title() for ax in fig.axes if ax.get_title())
    name, title, caption = figure_presentation(name)
    name = name.replace('/', '_').replace('\\', '_')
    title = title or original_title
    if fig.axes:
        fig.axes[0].set_title(title)
    for ax in fig.axes:
        ax.set_xlabel(AXIS_LABELS.get(ax.get_xlabel(), ax.get_xlabel()))
        ax.set_ylabel(AXIS_LABELS.get(ax.get_ylabel(), ax.get_ylabel()))
        legend = ax.get_legend()
        if legend:
            for text in legend.get_texts():
                value = text.get_text()
                text.set_text({
                    'optimal':'Proven optimal',
                    'best_observed':'Best observed (not proven optimal)',
                    'feasible':'Feasible, not best observed',
                    'unknown':'Unknown',
                }.get(value,value.replace(' timeout',' (timeout)')))
    FIGURE_STATUS.append(dict(figure=name, comparison_id=original_name, status='skipped' if reason else 'created',
                              title=title, caption=caption, comparison_notes=original_title, reason=reason))
    if not reason:
        FIG.mkdir(parents=True, exist_ok=True)
        import textwrap
        if caption:
            fig.text(.5, .015, textwrap.fill(caption, width=110), ha="center", va="bottom", fontsize=8)
        fig.tight_layout(rect=(0, .12 if caption else 0, 1, 1))
        fig.savefig(FIG/(name+'.png'), dpi=160)
    plt.close(fig)

def no_data(title):
    fig = plt.figure()
    fig._skip_reason = 'Insufficient matched evidence; see coverage and membership tables.'
    plt.title(title)

def write_figure_status():
    write_csv(FIG.parent/'figure_status.csv', FIGURE_STATUS,
              ['figure', 'comparison_id', 'status', 'title', 'caption', 'comparison_notes', 'reason'])
    skipped = [r for r in FIGURE_STATUS if r['status'] == 'skipped']
    with (FIG.parent/'findings.md').open('a') as f:
        f.write('\n\n## Skipped figures\n\n')
        f.write('No placeholder images are exported. See figure_status.csv for every figure.\n')
        for row in skipped:
            f.write(f'- {row["figure"]}: {row["reason"]}\n')

def emit(name,headers,rows,caption): table(name,headers,rows,caption,output=TABLES)

def iqr(values):
    vals=sorted(v for v in values if v is not None)
    if not vals: return None
    if len(vals)==1: return 0
    qs=statistics.quantiles(vals,n=4,method='inclusive'); return qs[2]-qs[0]

def boxes(rows,category,value,title,name):
    cells=grouped(rows,category); labels=[]; data=[]
    for label,rs in sorted(cells.items()):
        vals=[r[value] for r in rs if r.get(value) is not None and r[value]>=0]
        if vals: labels.append(f'{label}\n(n={len(vals)})'); data.append(vals)
    if not data: no_data(title)
    else:
        plt.figure(figsize=(max(8,len(labels)*.8),5)); plt.boxplot(data,showfliers=True)
        if all(v>0 for vs in data for v in vs): plt.yscale('log')
        else: plt.yscale('symlog',linthresh=.001)
        plt.xticks(range(1,len(labels)+1),labels,rotation=40,ha='right'); plt.ylabel(value); plt.xlabel('Graph group / Method'); plt.title(title)
    save(name)

def heat(rows,col,title,name):
    groups=sorted({r['group'] for r in rows}); cats=sorted({r[col] for r in rows})
    if not groups or not cats: no_data(title); save(name); return
    plt.figure(figsize=(max(7,len(groups)*1.5),max(3,len(cats))))
    matrix=[]; labs=[]
    for cat in cats:
        line=[]; labels=[]
        for group in groups:
            rs=[r for r in rows if r[col]==cat and r['group']==group]
            pct=100*sum(r['timeout'] for r in rs)/len(rs) if rs else float('nan')
            line.append(pct); labels.append(f'{pct:.0f}%\n(n={len(rs)})' if rs else 'NA')
        matrix.append(line); labs.append(labels)
    plt.imshow(matrix,vmin=0,vmax=100,cmap='YlOrRd',aspect='auto'); plt.colorbar(label='Observed timeout (%)')
    plt.xticks(range(len(groups)),groups,rotation=30); plt.yticks(range(len(cats)),cats)
    for i,line in enumerate(labs):
        for j,label in enumerate(line): plt.text(j,i,label,ha='center',va='center',fontsize=8)
    plt.title(title); save(name)

def common(rows,key,categories,stratum):
    output=[]
    for rs in grouped(rows,stratum).values():
        by=grouped(rs,lambda r:r[key])
        if all(len(by.get(c,[]))==1 for c in categories): output.extend(by[c][0] for c in categories)
    return output

def stratum(r,part):
    keys=[r['graph_id'],r['comparison_config']]
    if part in ('p1','p2a'): keys.append(r['backend'])
    keys.append(r['encoding'] if part=='p2a' else r['method'])
    return tuple(keys)

def select(runs,key,cats,part,name,predicate=lambda r:True,metric=None,exploratory=False,extra=None,require_common=True):
    eligible=[]; reasons={}; clean={r['source'] for r in clean_runs(runs)}
    for r in runs:
        reason=''
        if r[key] not in cats or not predicate(r): reason='outside comparison scope'
        elif r['source'] not in clean: reason='invalid, incomplete identity or ambiguous repeats'
        elif not exploratory and not r['metadata_verified']: reason='configuration not verified'
        elif metric and r.get(metric) is None: reason='metric missing'
        if reason: reasons[r['source']]=reason
        else: eligible.append(r)
    grouping=lambda r:(stratum(r,part),r.get(extra)) if extra else stratum(r,part)
    selected=common(eligible,key,cats,grouping) if require_common else eligible
    included={r['source'] for r in selected}
    emit(name+'_membership',['Source','Graph','Included','Reason'],[[r['source'],r['graph_id'],r['source'] in included,'' if r['source'] in included else reasons.get(r['source'],'unmatched or repeated stratum')] for r in runs],
         'Membership for '+name+'; unknown historical configurations are exploratory only.')
    return selected

def paired(rows,key,cats,value,name,title,part):
    cases=grouped(rows,lambda r:stratum(r,part)); drawn=0; plt.figure(figsize=(9,5))
    for case,rs in sorted(cases.items(),key=lambda x:str(x[0])):
        d={r[key]:r for r in rs}
        if not all(c in d and d[c].get(value) is not None for c in cats): continue
        ys=[d[c][value] for c in cats]
        plt.plot(range(len(cats)),ys,alpha=.4,label=rs[0]['graph']); drawn+=1
        for i,c in enumerate(cats): plt.scatter(i,ys[i],marker='o' if d[c]['proof']=='optimal' else 'x',s=20)
        if drawn==12: break
    if not drawn: plt.close(); no_data(title)
    else:
        plt.xticks(range(len(cats)),cats); plt.ylabel(value); plt.title(title+'\nFirst 12 graph IDs; circle=optimal, x=unproven')
        plt.legend(fontsize=6,ncol=2)
    save(name)

def overview(runs,issues):
    coverage=read_csv(ROOT/'processed'/'coverage.csv')
    headers=['method','encoding','group','Completed','Partial','Timeout','Missing','Error']
    emit('coverage',headers,[[r[k] for k in headers] for r in coverage],
         'File/run inventory; Missing includes explicit expected manifest only. Timeout is independent of feasible/optimal.')
    emit('data_quality',['Issue','Occurrences','Files'],[[key,len(rs),len({r['source'] for r in rs})] for key,rs in sorted(grouped(issues,lambda r:r['issue']).items())], 'Quality notices; categories may overlap.')
    configs=read_csv(ROOT/'processed'/'configurations.csv')
    emit('configuration_coverage',['Verified','Files'],[[value,sum(r['verified']==value for r in configs)] for value in ('True','False')], 'Full environment and parameters are in processed/configurations.csv; never inferred from this machine for old runs.')
    graphs={r['graph_id']:r for r in runs if r['vertices'] is not None}
    emit('dataset_overview',['Bucket','Graphs','Vertices min','Vertices max','Edges min','Edges max'],[[key,len(rs),min(r['vertices'] for r in rs),max(r['vertices'] for r in rs),min(r['edges'] for r in rs),max(r['edges'] for r in rs)] for key,rs in sorted(grouped(list(graphs.values()),lambda r:r['group']).items())], 'Distinct graph identities represented by input files; includes missing/error runs.')
    # Keep an explicit, readable metadata table, not just machine-readable JSON.
    import json
    details=[]
    for r in configs:
        m=json.loads(r['metadata']); e=m.get('environment',{})
        details.append([r['source'],m.get('solver'),m.get('started_at'),e.get('cpu'),e.get('ram_bytes'),e.get('os'),e.get('python'),str(e.get('versions',{})),m.get('parameters'),m.get('time_limit'),m.get('encoding_time_limit'),m.get('total_time_limit')])
    emit('configurations',['Source','Solver','Date UTC','CPU','RAM bytes','OS','Python','Versions','Parameters','Solve limit','Encoding limit','Run limit'],details,'Blank means not recorded. Run limit excludes externally precomputed bounds; wall time includes their measured cost.')

def part1(runs,method='Repeated',exploratory=False):
    tag='p1_'+method+('_exploratory' if exploratory else '')
    rows=select(runs,'encoding',SAT,'p1',tag,lambda r:r['method']==method,exploratory=exploratory)
    best_sources=best_observed_sources(rows,'p1')
    title='EXPLORATORY historical logs' if exploratory else 'Verified matched runs'
    for metric in ('encoding_time','solving_time'):
        matched=select(runs,'encoding',SAT,'p1',tag+'_'+metric,lambda r:r['method']==method and (r['proof']=='optimal' or r['source'] in best_sources),metric,exploratory)
        boxes(matched,lambda r:r['group']+' / '+r['encoding'],metric,title+'; optimal or best-observed runs; '+method,tag+'_'+metric)
    heat(rows,'encoding',title+'; '+method,tag+'_timeout')
    emit(tag+'_timeout_phases',['Encoding','Phase','Runs'],[[enc,phase,sum(phase in (r.get('timeout_phase') or '').split(',') for r in rows if r['encoding']==enc)] for enc in SAT for phase in ('encoding','solving','total')], 'Recorded timeout phase only; historical unknown phases are not inferred.')
    sizes=select(runs,'encoding',SAT,'p1',tag+'_sizes',lambda r:r['method']==method,exploratory=exploratory,extra='first_k')
    for metric in ('num_variables','num_clauses'):
        metric_sizes=common([r for r in sizes if r.get(metric) is not None],'encoding',SAT,lambda r:(stratum(r,'p1'),r['first_k']))
        plt.figure(figsize=(9,5))
        for enc in SAT:
            rs=[r for r in metric_sizes if r['encoding']==enc and r.get(metric) is not None]
            by=grouped(rs,lambda r:r['vertices']); xs=sorted(by)
            plt.plot(xs,[median([r[metric] for r in by[x]]) for x in xs],marker='o',label=enc)
        plt.xlabel('Vertices'); plt.ylabel(metric); plt.title(title+'; first attempt, matched graph and k; median at each n'); plt.legend(); save(tag+'_'+metric)
    speed=select(runs,'encoding',SAT,'p1',tag+'_runtime',lambda r:r['method']==method and (r['proof']=='optimal' or r['source'] in best_sources),metric='total_time',exploratory=exploratory)
    paired(speed,'encoding',SAT,'total_time',tag+'_paired_time',title+'; optimal or best-observed runs; k may differ','p1')
    headers=['Encoding','Graphs','Runs','Optimal/best-observed timed n','Encoding timed n','Solve timed n','Encoding median','Encoding IQR','Solve median','Solve IQR','Total median','Total IQR','Timeout','Feasible']
    data=[]
    for enc,rs in sorted(grouped(rows,lambda r:r['encoding']).items()):
        done=[r for r in speed if r['encoding']==enc]
        samples={k:[r for r in common([r for r in speed if r.get(k) is not None],'encoding',SAT,lambda r:stratum(r,'p1')) if r['encoding']==enc] for k in ('encoding_time','solving_time','total_time')}
        data.append([enc,len({r['graph_id'] for r in rs}),len(rs),len(done),len(samples['encoding_time']),len(samples['solving_time']),*[f([r[k] for r in samples[k]]) for k in ('encoding_time','solving_time','total_time') for f in (median,iqr)],sum(r['timeout'] for r in rs),sum(r['best_k'] is not None for r in rs)])
    emit(tag+'_summary',headers,data,title+'; runtime statistics use common proven or best-observed runs; k may differ; historical solve includes setup.')
    emit(tag+'_results',['Graph','Encoding','UB','LB','Proof','Timeout','Time basis'],[[r['graph_id'],r['encoding'],r['best_k'],r['lower_bound'],r['proof'],r['timeout'],r['time_basis']] for r in rows],title)
    data=[]
    for enc,rs in sorted(grouped(sizes,lambda r:r['encoding']).items()):
        for metric in ('num_variables','num_clauses'):
            comparable=common([r for r in sizes if r.get(metric) is not None],'encoding',SAT,lambda r:(stratum(r,'p1'),r['first_k']))
            vals=[r[metric] for r in comparable if r['encoding']==enc]
            if vals: data.append([enc,metric,len(vals),median(vals),min(vals),max(vals)])
    emit(tag+'_formula_sizes',['Encoding','Metric','N','Median','Min','Max'],data,'Matched graph/method/first k. Formula size depends on both graph and k.')

def part2a(runs,exploratory=False):
    cats=('Incremental','Repeated','Binary')
    for enc in SAT:
        tag='p2a_'+enc+('_exploratory' if exploratory else '')
        rows=select(runs,'method',cats,'p2a',tag,lambda r:r['encoding']==enc,exploratory=exploratory)
        best_sources=best_observed_sources(rows,'p2a')
        speed=select(runs,'method',cats,'p2a',tag+'_runtime',lambda r:r['encoding']==enc and (r['proof']=='optimal' or r['source'] in best_sources),metric='total_time',exploratory=exploratory)
        title=('EXPLORATORY; ' if exploratory else 'Verified; ')+enc
        boxes(speed,lambda r:r['group']+' / '+r['method'],'total_time',title+'; common proven-optimal or best-observed runs; k may differ',tag+'_total_time')
        heat(rows,'method',title,tag+'_timeout')
        paired(rows,'method',cats,'best_k',tag+'_best_colors',title,'p2a')
        for metric in ('attempts','solver_calls'):
            plt.figure(figsize=(8,5))
            for method in cats:
                rs=[r for r in rows if r['method']==method and r.get(metric) is not None and r['total_time'] is not None]
                for timed,marker in ((False,'o'),(True,'x')):
                    subset=[r for r in rs if r['timeout']==timed]
                    plt.scatter([r[metric] for r in subset],[r['total_time'] for r in subset],marker=marker,label=method+(' timeout' if timed else ''),alpha=.6)
            plt.yscale('symlog',linthresh=1)
            plt.xlabel(metric); plt.ylabel('Observed runtime (s), not time to solution for timeout'); plt.title(title); plt.legend(fontsize=7); save(tag+'_'+metric+'_time')
        data=[]
        for method,rs in sorted(grouped(rows,lambda r:r['method']).items()):
            done=[r for r in speed if r['method']==method]
            data.append([method,len(rs),len(done),median([r['total_time'] for r in done]),iqr([r['total_time'] for r in done]),sum(r['timeout'] for r in rs),median([r['attempts'] for r in rs]),median([r['solver_calls'] for r in rs]),median([r['best_k'] for r in rs]),100*sum(r['proof']=='optimal' for r in rs)/len(rs)])
        emit(tag+'_methods',['Method','Runs','Optimal/best-observed timed n','Median time','IQR time','Timeout','Median attempts','Median calls','Median best colors','Optimal %'],data,title+'; runtime includes common proven or best-observed runs, where k may differ; median colors describes this dataset, not paired quality advantage.')
        emit(tag+'_results',['Graph','Method','UB','LB','Proof','Timeout'],[[r['graph_id'],r['method'],r['best_k'],r['lower_bound'],r['proof'],r['timeout']] for r in rows],title)

def performance_profile(rows,categories=BACKENDS,best_sources=None):
    cases=grouped(rows,lambda r:stratum(r,'p2b')); ratios=defaultdict(list)
    for rs in cases.values():
        good=[
            r for r in rs
            if (r['proof']=='optimal' or (best_sources and r['source'] in best_sources))
            and r['total_time'] is not None
            and r['total_time']>0
        ]
        if not good: continue
        best=min(r['total_time'] for r in good)
        for r in good: ratios[r['encoding']].append(r['total_time']/best)
    if not cases or not ratios: return {}
    xmax=max(2,max(max(v) for v in ratios.values())*1.05)
    return {c:[(x,sum(v<=x for v in ratios[c])/len(cases)) for x in sorted(set([1,xmax]+ratios[c]))] for c in categories}

def best_observed_sources(rows,part='p2b'):
    """Find categories with the lowest recorded feasible color count per comparison."""
    best_by_group={}
    categories_by_group=defaultdict(set)
    for row in rows:
        if row['proof'] not in ('optimal','feasible') or row.get('best_k') is None:
            continue
        group=stratum(row,part)
        category='method' if part=='p2a' else 'encoding'
        categories_by_group[group].add(row[category])
        best_by_group[group]=min(best_by_group.get(group,float('inf')),row['best_k'])
    return {
        row['source']
        for row in rows
        if row['proof']=='feasible'
        and row.get('best_k') is not None
        and len(categories_by_group[stratum(row,part)]) > 1
        and row['best_k']==best_by_group.get(stratum(row,part))
    }

def comparative_outcome(row,best_sources):
    if row['proof']=='optimal':
        return 'optimal'
    if row['source'] in best_sources:
        return 'best_observed'
    if row['proof']=='feasible':
        return 'feasible'
    return 'unknown'

def part2b(runs,exploratory=False):
    for method in P2B_METHODS:
        cats=P2B_ENCODINGS if method=='Incremental' else BACKENDS
        keep_unmatched=method=='Incremental'
        tag='p2b_'+method+('_exploratory' if exploratory else '')
        rows=select(runs,'encoding',cats,'p2b',tag,lambda r:r['method']==method,exploratory=exploratory,require_common=not keep_unmatched)
        best_sources=best_observed_sources(rows)
        speed=select(runs,'encoding',cats,'p2b',tag+'_runtime',lambda r:r['method']==method and (r['proof']=='optimal' or r['source'] in best_sources),metric='total_time',exploratory=exploratory,require_common=not keep_unmatched)
        title=('EXPLORATORY; ' if exploratory else 'Verified; ')+method+'; SAT, POP and POHP encodings'
        boxes(speed,lambda r:r['encoding'],'total_time',title+'; common proven-optimal or best-observed runs; k may differ',tag+'_total_time')
        heat(rows,'encoding',title,tag+'_timeout')
        cells=grouped(rows,lambda r:r['encoding'])
        if not rows: no_data(title)
        else:
            plt.figure(figsize=(9,5)); bottom=[0]*len(cats)
            outcome_colors={
                'optimal':'tab:blue',
                'best_observed':'tab:green',
                'feasible':'tab:orange',
                'unknown':'tab:red',
            }
            for outcome in ('optimal','best_observed','feasible','unknown'):
                vals=[100*sum(comparative_outcome(r,best_sources)==outcome for r in cells[c])/len(cells[c]) for c in cats]
                plt.bar(cats,vals,bottom=bottom,label=outcome,color=outcome_colors[outcome]); bottom=[a+b for a,b in zip(bottom,vals)]
            plt.ylabel('Runs (%)'); plt.legend(); plt.title(title)
        save(tag+'_outcomes')
        profile=performance_profile(speed,cats,best_sources)
        if not profile: no_data(title+'; no proven timed runs')
        else:
            plt.figure(figsize=(8,5))
            for c,points in profile.items(): plt.step([p[0] for p in points],[p[1] for p in points],where='post',label=c)
            plt.xscale('log'); plt.ylim(0,1.02); plt.xlabel('Runtime / fastest proven runtime'); plt.ylabel('Fraction of all matched cases'); plt.legend(); plt.title(title)
        save(tag+'_profile')
        boxes([r for r in rows if r['proof']=='feasible'],lambda r:r['encoding'],'gap',title+'; unproven feasible runs',tag+'_gap')
        data=[]
        for c in cats:
            rs=cells.get(c,[]); done=[r for r in speed if r['encoding']==c]
            data.append([c,len({r['graph_id'] for r in rs}),len(rs),sum(r['best_k'] is not None for r in rs),sum(r['proof']=='optimal' for r in rs),sum(r['source'] in best_sources for r in rs),sum(r['timeout'] for r in rs),len(done),median([r['total_time'] for r in done]),iqr([r['total_time'] for r in done]),median([r['gap'] for r in rs if r['proof']=='feasible'])])
        if keep_unmatched:
            scope='Incremental includes SAT, POP and POHP only and retains available graph records.'
        else:
            scope='Includes all six encodings and only common matched graphs.'
        emit(tag+'_backends',['Encoding/backend','Graphs','Runs','Feasible','Optimal','Best observed','Timeout','Optimal timed n','Median time','IQR time','Median unproven gap'],data,title+'; '+scope+' Best observed is comparative, not an optimality proof.')
        emit(tag+'_results',['Graph','Encoding','UB','LB','Proof','Comparative result','Timeout'],[[r['graph_id'],r['encoding'],r['best_k'],r['lower_bound'],r['proof'],comparative_outcome(r,best_sources),r['timeout']] for r in rows],title)
        pair_data=[]
        for a,b in combinations(cats,2):
            pair=select(runs,'encoding',(a,b),'p2b',tag+'_pair_'+a+'_'+b,lambda r:r['method']==method,exploratory=exploratory)
            timed=common([r for r in pair if r['proof']=='optimal' and r['total_time'] is not None],'encoding',(a,b),lambda r:stratum(r,'p2b'))
            pair_data.append([a,b,len(pair)//2,len(timed)//2,median([r['total_time'] for r in timed if r['encoding']==a]),median([r['total_time'] for r in timed if r['encoding']==b])])
        emit(tag+'_pairs',['A','B','Common cases','Both optimal timed','A median','B median'],pair_data,title+'; pairwise intersections are independent of other backends.')

def part3():
    rows=read_csv(ROOT/'processed'/'k_sweep.csv')
    for r in rows:
        for k in ('k','total_time','solving_time','encoding_time'): r[k]=number(r[k])
    inventory=read_csv(ROOT/'processed'/'inventory.csv')
    emit('p3_coverage',['Source','Graph','Rows','Status'],[[r['source'],r['graph_id'],r['rows'],'Missing' if int(r['rows'])==0 else 'Recorded attempts; completion may be unknown'] for r in inventory if r['schema']=='k_sweep'], 'Header-only sweep is Missing, not Timeout.')
    cells=grouped(rows,lambda r:r['graph_id']); summary=[]
    for gid,rs in sorted(cells.items()):
        plt.figure(figsize=(9,5)); valid=[r for r in rs if r['total_time'] is not None]
        ordered=sorted(valid,key=lambda r:r['k'])
        plt.plot([r['k'] for r in ordered],[r['total_time'] for r in ordered],alpha=.5)
        for status,marker in (('SAT','o'),('UNSAT','s'),('TIMEOUT','x'),('UNKNOWN','^')):
            subset=[r for r in ordered if r['status']==status]
            plt.scatter([r['k'] for r in subset],[r['total_time'] for r in subset],marker=marker,label=status)
        plt.yscale('symlog',linthresh=.001); plt.xlabel('k'); plt.ylabel('Runtime per k (s)'); plt.title(gid+'; independent solves, historical configuration may be unknown'); plt.legend(); save('p3_'+gid.replace('/','_').replace('.col',''))
        for status in ('SAT','UNSAT','TIMEOUT','UNKNOWN'):
            subset=[r for r in valid if r['status']==status]
            if subset:
                peak=max(subset,key=lambda r:r['total_time'])
                summary.append([gid,status,len(subset),min(r['k'] for r in subset),max(r['k'] for r in subset),median([r['total_time'] for r in subset]),peak['k'],peak['total_time']])
    if not cells: no_data('Runtime by k')
    else:
        plt.figure(figsize=(10,6))
        for gid,rs in sorted(cells.items()):
            rs=sorted([r for r in rs if r['total_time'] is not None],key=lambda r:r['k'])
            plt.plot([r['k'] for r in rs],[r['total_time'] for r in rs],label=gid)
        plt.xlabel('k'); plt.ylabel('Runtime per k (s)'); plt.yscale('symlog',linthresh=.001); plt.legend(fontsize=7); plt.title('Exploratory k sweep; one graph per bucket is not a population conclusion')
    save('p3_runtime_k')
    emit('p3_summary',['Graph','Status','Attempts','Min k','Max k','Median runtime','Peak k','Peak runtime'],summary,'Per-k observed runtime, not total Repeated search time. Timeout values are censored.')

def conclusions(runs):
    verified=sum(r['metadata_verified'] for r in runs)
    text=['# Analysis findings',f'Input run records: {len(runs)}. Verified metadata: {verified}.',
          'Primary comparisons require verified metadata. Historical outputs have exploratory labels; they cannot establish a controlled ranking.',
          'Legacy POP logs are not evidence for the new partial-order implementation. See rerun_needed.csv.',
          'Pairwise runtime tables use common proven-optimal runs. Runtime plots may also include the best-observed feasible result; k can differ across methods or encodings. Timeout and missing outcomes remain in coverage; timeout duration is not solution time.',
          'Best observed means the lowest recorded valid best_k among methods or encodings in the same graph comparison; it is comparative only and does not prove optimality. A timeout alone is not evidence that its current k is feasible.',
          'Historical lower bounds can omit the original bound calculation. Historical solve times may include setup. No historical wall-clock values are reconstructed.',
          'Gap uses (UB-LB)/UB and only recorded certified bounds; missing values are not zero. SAT/ILP/CP quality is assessed separately from speed.',
          'Each membership table identifies included/excluded source files. No fastest-repeat selection is performed.',
          'For k sweeps, inspect status-specific peaks and intervals in p3_summary.csv. Runtime need not be monotonic in k; each bucket has only one representative.',
          'Expected coverage requires --expected; without it completely absent runs cannot be counted.']
    (FIG.parent/'findings.md').write_text('\n\n'.join(text)+'\n')

def empirical_findings():
    lines=['## Observations from generated tables']
    for path in sorted(TABLES.glob('*_summary.csv')):
        if path.stem.startswith('p1_'):
            rows=read_csv(path)
            if not rows: continue
            label='Exploratory, not a controlled conclusion' if 'exploratory' in path.stem else 'Verified cohort'
            lines.append(f'{label} ({path.stem}):')
            for metric in ('Encoding median','Solve median','Total median'):
                valid=[r for r in rows if number(r.get(metric)) is not None]
                if valid:
                    best=min(valid,key=lambda r:number(r[metric]))
                    lines.append(f'- Lowest {metric}: {best["Encoding"]}, {float(best[metric]):.6g} s; common optimal/best-observed timed n={best["Optimal/best-observed timed n"]}.')
            lines.append('These medians apply only to the matched proven or best-observed subset. k may differ; use timeout/feasible counts and IQR alongside speed; no overall winner follows from speed alone.')
    for path in sorted(TABLES.glob('p2a_*_methods.csv')):
        rows=read_csv(path)
        if not rows: continue
        lines.append(f'{path.stem}: '+ '; '.join(f'{r["Method"]}: optimal={r["Optimal %"]}%, timeout={r["Timeout"]}/{r["Runs"]}, median attempts={r["Median attempts"]}' for r in rows)+'.')
    for path in sorted(TABLES.glob('p2b_*_pairs.csv')):
        for r in read_csv(path):
            if number(r['Both optimal timed']):
                lines.append(f'{path.stem}: {r["A"]} vs {r["B"]}, common cases={r["Common cases"]}, both proven timed={r["Both optimal timed"]}; medians={r["A median"]} / {r["B median"]} s. Pairwise samples can differ; do not combine these into a universal ordering.')
    sweeps=read_csv(ROOT/'processed'/'k_sweep.csv')
    for gid,rs in sorted(grouped(sweeps,lambda r:r['graph_id']).items()):
        valid=sorted([r for r in rs if number(r['total_time']) is not None],key=lambda r:float(r['k']))
        if not valid: continue
        peak=max(valid,key=lambda r:float(r['total_time']))
        reversals=sum(float(a['total_time'])>float(b['total_time']) for a,b in zip(valid,valid[1:]))
        timeouts=[int(float(r['k'])) for r in valid if r['status']=='TIMEOUT']
        lines.append(f'{gid}: largest observed runtime at k={peak["k"]}, status={peak["status"]}, t={float(peak["total_time"]):.6g}s. Smaller k was slower in {reversals}/{max(0,len(valid)-1)} adjacent observed pairs. Timeout k range: {str((min(timeouts),max(timeouts))) if timeouts else "none recorded"}; range does not imply every interior k timed out.')
        for status in ('SAT','UNSAT'):
            vals=[float(r['solving_time']) for r in valid if r['status']==status and number(r['solving_time']) is not None]
            if vals: lines.append(f'- {status}: n={len(vals)}, median recorded solve={median(vals):.6g}s. This is descriptive; different k and censoring preclude a significance claim.')
    lines.append('Size, density, k and structure can all affect difficulty. Single-graph bucket samples and historical metadata gaps prevent claims about all large graphs or native solver families.')
    path=FIG.parent/'findings.md'
    with path.open('a') as f: f.write('\n\n'+'\n\n'.join(lines)+'\n')