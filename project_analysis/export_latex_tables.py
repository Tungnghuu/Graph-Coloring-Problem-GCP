from pathlib import Path
from .analysis_core import clean_runs, load_runs, median, pool_exploratory
from .reports import SAT, best_observed_sources, common, stratum

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'tables'
METHOD = 'Repeated'
GROUP_ORDER = ('100_or_less', '250', '500', '750', '1000', 'dense')

LATEX_SPECIAL = {
    '\\': r'\textbackslash{}',
    '&': r'\&',
    '%': r'\%',
    '$': r'\$',
    '#': r'\#',
    '_': r'\_',
    '{': r'\{',
    '}': r'\}',
    '~': r'\textasciitilde{}',
    '^': r'\textasciicircum{}',
}

def tex_escape(value):
    return ''.join(LATEX_SPECIAL.get(char, char) for char in str(value))

def fmt(value):
    if value is None or value == '':
        return '--'
    number = float(value)
    if number.is_integer():
        return str(int(number))
    return f'{number:.3g}'

def matched_rows(runs):
    eligible = [
        row for row in clean_runs(runs)
        if row['method'] == METHOD and row['encoding'] in SAT
    ]
    return common(eligible, 'encoding', SAT, lambda row: stratum(row, 'p1'))

def runtime_table(rows):
    best_sources = best_observed_sources(rows, 'p1')
    timed = [
        row for row in rows
        if (row['proof'] == 'optimal' or row['source'] in best_sources)
        and row['total_time'] is not None
    ]
    medians = {}
    sample_counts = {}
    for metric in ('encoding_time', 'solving_time', 'total_time'):
        measured = common(
            [row for row in timed if row.get(metric) is not None],
            'encoding',
            SAT,
            lambda row: stratum(row, 'p1'),
        )
        medians[metric] = {
            encoding: median([
                row[metric] for row in measured if row['encoding'] == encoding
            ])
            for encoding in SAT
        }
        sample_counts[metric] = {
            encoding: sum(row['encoding'] == encoding for row in measured)
            for encoding in SAT
        }

    data = []
    for encoding in SAT:
        group = [row for row in rows if row['encoding'] == encoding]
        data.append([
            encoding,
            len({row['graph_id'] for row in group}),
            fmt(medians['encoding_time'][encoding]),
            fmt(medians['solving_time'][encoding]),
            fmt(medians['total_time'][encoding]),
            '/'.join(str(sample_counts[key][encoding]) for key in
                     ('encoding_time', 'solving_time', 'total_time')),
            sum(row['timeout'] for row in group),
            sum(row['best_k'] is not None for row in group),
        ])
    return data

def formula_size_table(runs):
    eligible = [
        row for row in clean_runs(runs)
        if row['method'] == METHOD and row['encoding'] in SAT
    ]
    matched = common(
        eligible,
        'encoding',
        SAT,
        lambda row: (stratum(row, 'p1'), row.get('first_k')),
    )
    data = []
    for encoding in SAT:
        variables = [
            row['num_variables'] for row in matched
            if row['encoding'] == encoding
            and row.get('num_variables') is not None
            and row['num_variables'] > 0
        ]
        clauses = [
            row['num_clauses'] for row in matched
            if row['encoding'] == encoding
            and row.get('num_clauses') is not None
            and row['num_clauses'] > 0
        ]
        data.append([
            encoding,
            len(variables),
            f'{fmt(median(variables))} [{fmt(min(variables))}--{fmt(max(variables))}]'
            if variables else '--',
            len(clauses),
            f'{fmt(median(clauses))} [{fmt(min(clauses))}--{fmt(max(clauses))}]'
            if clauses else '--',
        ])
    return data

def bounds_table(rows):
    order = {encoding: position for position, encoding in enumerate(SAT)}
    groups = {name: position for position, name in enumerate(GROUP_ORDER)}
    data = []
    for row in sorted(rows, key=lambda item: (
        groups.get(item['group'], len(groups)), item['graph'].lower(), order[item['encoding']],
    )):
        status = {
            'optimal': 'Proven optimal',
            'feasible': 'Feasible, not proven optimal',
            'unknown': 'Unknown',
        }.get(row['proof'], row['proof'])
        data.append([
            row['graph'],
            row['encoding'],
            fmt(row['best_k']),
            fmt(row['lower_bound']),
            status,
        ])
    return data

def tabular_file(filename, caption, label, alignment, headers, rows, size=r'\small'):
    lines = [
        r'\begin{table}[htbp]',
        r'\centering',
        size,
        rf'\caption{{{tex_escape(caption)}}}',
        rf'\label{{tab:{label}}}',
        rf'\begin{{tabular}}{{{alignment}}}',
        r'\hline',
        ' & '.join(headers) + r' \\',
        r'\hline',
    ]
    lines.extend(
        ' & '.join(tex_escape(value) for value in row) + r' \\'
        for row in rows
    )
    lines.extend([r'\hline', r'\end{tabular}', r'\end{table}'])
    (OUTPUT / filename).write_text('\n'.join(lines) + '\n', encoding='utf-8')

def longtable_file(filename, caption, label, headers, rows):
    lines = [
        r'% Requires \usepackage{longtable}',
        r'\small',
        r'\begin{longtable}{llrrl}',
        rf'\caption{{{tex_escape(caption)}}}\label{{tab:{label}}}\\',
        r'\hline',
        ' & '.join(headers) + r' \\',
        r'\hline',
        r'\endfirsthead',
        rf'\multicolumn{{5}}{{c}}{{\tablename\ \thetable\ (continued)}}\\',
        r'\hline',
        ' & '.join(headers) + r' \\',
        r'\hline',
        r'\endhead',
        r'\hline',
        r'\multicolumn{5}{r}{Continued on next page}\\',
        r'\endfoot',
        r'\hline',
        r'\endlastfoot',
    ]
    lines.extend(
        ' & '.join(tex_escape(value) for value in row) + r' \\'
        for row in rows
    )
    lines.append(r'\end{longtable}')
    (OUTPUT / filename).write_text('\n'.join(lines) + '\n', encoding='utf-8')

def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    runs = pool_exploratory(load_runs())
    rows = matched_rows(runs)
    table1 = runtime_table(rows)
    table2 = formula_size_table(runs)
    table3 = bounds_table(rows)

    table1_note = (
        'P1, Repeated method. Timing medians use matched proven-optimal or '
        'best-observed runs; k may differ. Historical configurations are unverified.'
    )
    tabular_file(
        'table1_runtime.tex',
        table1_note,
        'encoding-runtime',
        'lrrrrrrr',
        [
            'Encoding', 'Graphs', 'Median encode (s)', 'Median solve (s)',
            'Median total (s)', 'Timed n (E/S/T)', 'Timeouts', 'Valid solutions',
        ],
        table1,
    )
    tabular_file(
        'table2_formula_size.tex',
        'Formula sizes at the first recorded k; zero-size records are excluded.',
        'formula-size',
        'lrlrl',
        [
            'Encoding', 'Variables n', 'Variables median [min--max]',
            'Clauses n', 'Clauses median [min--max]',
        ],
        table2,
    )
    longtable_file(
        'table3_bounds_proof.tex',
        'Best valid upper bound, lower bound, and proof status per graph and encoding. Lower bound = clique bound used by the benchmark (recomputed for runs without a manifest), raised by any UNSAT result.',
        'bounds-proof',
        ['Graph', 'Encoding', 'Best UB', 'Recorded LB', 'Proof status'],
        table3,
    )
    print(f'Wrote 3 LaTeX tables ({len(table1)} encodings, {len(table3)} graph-encoding rows) to {OUTPUT}.')

if __name__ == '__main__':
    main()