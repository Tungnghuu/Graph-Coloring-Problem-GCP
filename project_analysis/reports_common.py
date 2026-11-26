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

FIG = ROOT / 'outputs' / 'figures'
TABLES = ROOT / 'outputs' / 'tables'
SAT = ('SAT','POP','POHP')
P2B_ENCODINGS=SAT
P2B_METHODS=('Incremental','Repeated','Binary')
BACKENDS=(*SAT,'Gurobi_ILP','CPLEX_MIP','CPLEX_CP')
GRAPH_GROUP_ORDER=('100_or_less','250','500','750','1000','dense')

FIGURE_STATUS = []

def graph_group_sort_key(group):
    try:
        return GRAPH_GROUP_ORDER.index(group), group
    except ValueError:
        return len(GRAPH_GROUP_ORDER), group

def graph_id_sort_key(graph_id):
    normalized_graph_id = graph_id.replace('/', '\\')
    group = normalized_graph_id.split('\\', 1)[0]
    return graph_group_sort_key(group), graph_id

def graph_category_sort_key(label):
    group = label.split(' / ', 1)[0]
    return graph_group_sort_key(group), label

def has_plotted_data(fig):
    return any(
        any(len(line.get_xdata()) and len(line.get_ydata()) for line in ax.lines)
        or any(len(collection.get_offsets()) for collection in ax.collections)
        or bool(ax.patches)
        or any(image.get_array().size for image in ax.images)
        for ax in fig.axes
    )

def figure_presentation(name):
    clean = name.replace('_exploratory', '')
    metrics = {
        'encoding_time': ('encoding_time', 'Encoding time comparison'),
        'solving_time': ('solving_time', 'Solving time comparison'),
        'total_time': ('total_time', 'Total runtime comparison'),
        'timeout': ('timeout_rate', 'Timeout rate'),
        'num_variables': ('variables', 'Formula variable count'),
        'num_clauses': ('clauses', 'Formula clause count'),
        'paired_time': ('runtime_by_graph', 'Runtime by graph'),
        'best_colors': ('best_colors', 'Best color count by graph'),
        'attempts_time': ('attempts_vs_runtime', 'Attempts versus runtime'),
        'solver_calls_time': ('solver_calls_vs_runtime', 'Solver calls versus runtime'),
        'outcomes': ('solution_outcomes', 'Solution outcome breakdown'),
        'profile': ('performance_profile', 'Relative performance profile'),
        'gap': ('optimality_gap', 'Optimality gap'),
    }
    if clean.startswith(('p1_', 'p2a_', 'p2b_')):
        part, config, metric = clean.split('_', 2)
        slug, title = metrics[metric]
        label = config + ' SAT' if part == 'p1' else config
        filename = f'{part}_{slug}_{config.lower()}'
        if '_exploratory' not in name:
            filename += '_verified'
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
        if graph == 'runtime_k':
            return (
                'p3_runtime_by_k',
                'Total runtime by color count k',
                'Multi-graph comparison; total runtime only. Each k is an independent solve.',
            )
        return (
            'p3_runtime_by_k_' + graph,
            'Runtime components by color count k — ' + graph,
            'Single graph; lines show encoding, solving, and total runtime for independent solves.',
        )
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
    figure_status = {
        'figure': name,
        'comparison_id': original_name,
        'status': 'skipped' if reason else 'created',
        'title': title,
        'caption': caption,
        'comparison_notes': original_title,
        'reason': reason,
    }
    FIGURE_STATUS.append(figure_status)
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

def emit(name, headers, rows, caption):
    table(name, headers, rows, caption, output=TABLES)

def iqr(values):
    measured_values = sorted(
        value for value in values
        if value is not None
    )
    if not measured_values:
        return None
    if len(measured_values) == 1:
        return 0

    quartiles = statistics.quantiles(
        measured_values,
        n=4,
        method='inclusive',
    )
    return quartiles[2] - quartiles[0]

def boxes(rows, category, value, title, name):
    cells = grouped(rows, category)
    labels = []
    plot_data = []

    for label, matching_rows in sorted(
        cells.items(),
        key=lambda item: graph_category_sort_key(item[0]),
    ):
        measured_values = [
            row[value]
            for row in matching_rows
            if row.get(value) is not None and row[value] >= 0
        ]
        if measured_values:
            labels.append(f'{label}\n(n={len(measured_values)})')
            plot_data.append(measured_values)

    if not plot_data:
        no_data(title)
    else:
        figure_width = max(8, len(labels) * 0.8)
        plt.figure(figsize=(figure_width, 5))
        plt.boxplot(plot_data, showfliers=True)

        every_value_is_positive = all(
            value > 0
            for group_values in plot_data
            for value in group_values
        )
        if every_value_is_positive:
            plt.yscale('log')
        else:
            plt.yscale('symlog', linthresh=0.001)

        positions = range(1, len(labels) + 1)
        plt.xticks(positions, labels, rotation=40, ha='right')
        plt.ylabel(value)
        plt.xlabel('Graph group / Method')
        plt.title(title)

    save(name)

def heat(rows, column, title, name):
    groups = sorted(
        {row['group'] for row in rows},
        key=graph_group_sort_key,
    )
    categories = sorted({row[column] for row in rows})

    if not groups or not categories:
        no_data(title)
        save(name)
        return

    figure_width = max(7, len(groups) * 1.5)
    figure_height = max(3, len(categories))
    plt.figure(figsize=(figure_width, figure_height))

    heatmap_values = []
    heatmap_labels = []
    for category in categories:
        category_values = []
        category_labels = []

        for group in groups:
            matching_rows = [
                row for row in rows
                if row[column] == category and row['group'] == group
            ]
            if matching_rows:
                timeout_percentage = (
                    100 * sum(row['timeout'] for row in matching_rows)
                    / len(matching_rows)
                )
                cell_label = (
                    f'{timeout_percentage:.0f}%\n'
                    f'(n={len(matching_rows)})'
                )
            else:
                timeout_percentage = float('nan')
                cell_label = 'NA'

            category_values.append(timeout_percentage)
            category_labels.append(cell_label)

        heatmap_values.append(category_values)
        heatmap_labels.append(category_labels)

    plt.imshow(
        heatmap_values,
        vmin=0,
        vmax=100,
        cmap='YlOrRd',
        aspect='auto',
    )
    plt.colorbar(label='Observed timeout (%)')
    plt.xticks(range(len(groups)), groups, rotation=30)
    plt.yticks(range(len(categories)), categories)

    for row_index, label_row in enumerate(heatmap_labels):
        for column_index, label in enumerate(label_row):
            plt.text(
                column_index,
                row_index,
                label,
                ha='center',
                va='center',
                fontsize=8,
            )

    plt.title(title)
    save(name)

def common(rows, key, categories, stratum):
    matching_rows = []
    rows_by_stratum = grouped(rows, stratum)

    for stratum_rows in rows_by_stratum.values():
        rows_by_category = grouped(
            stratum_rows,
            lambda row: row[key],
        )
        every_category_has_one_row = all(
            len(rows_by_category.get(category, [])) == 1
            for category in categories
        )

        if every_category_has_one_row:
            for category in categories:
                matching_rows.append(rows_by_category[category][0])

    return matching_rows

def stratum(row, part):
    keys = [
        row['graph_id'],
        row['comparison_config'],
    ]

    if part in ('p1', 'p2a'):
        keys.append(row['backend'])

    if part == 'p2a':
        keys.append(row['encoding'])
    else:
        keys.append(row['method'])

    return tuple(keys)

def select(
    runs,
    key,
    cats,
    part,
    name,
    predicate=lambda row: True,
    metric=None,
    exploratory=False,
    extra=None,
    require_common=True,
):
    eligible_rows = []
    exclusion_reasons = {}
    clean_sources = {
        row['source']
        for row in clean_runs(runs)
    }

    for row in runs:
        reason = ''

        if row[key] not in cats or not predicate(row):
            reason = 'outside comparison scope'
        elif row['source'] not in clean_sources:
            reason = 'invalid, incomplete identity or ambiguous repeats'
        elif not exploratory and not row['metadata_verified']:
            reason = 'configuration not verified'
        elif metric and row.get(metric) is None:
            reason = 'metric missing'

        if reason:
            exclusion_reasons[row['source']] = reason
        else:
            eligible_rows.append(row)

    if extra:
        def grouping_key(row):
            return stratum(row, part), row.get(extra)
    else:
        def grouping_key(row):
            return stratum(row, part)

    if require_common:
        selected_rows = common(
            eligible_rows,
            key,
            cats,
            grouping_key,
        )
    else:
        selected_rows = eligible_rows

    included_sources = {
        row['source']
        for row in selected_rows
    }
    membership_rows = []

    for row in runs:
        if row['source'] in included_sources:
            reason = ''
        else:
            reason = exclusion_reasons.get(
                row['source'],
                'unmatched or repeated stratum',
            )

        membership_rows.append([
            row['source'],
            row['graph_id'],
            row['source'] in included_sources,
            reason,
        ])

    emit(
        name + '_membership',
        ['Source', 'Graph', 'Included', 'Reason'],
        membership_rows,
        'Membership for ' + name
        + '; unknown historical configurations are exploratory only.',
    )
    return selected_rows

def paired(rows, key, cats, value, name, title, part):
    cases = grouped(
        rows,
        lambda row: stratum(row, part),
    )
    drawn_graphs = 0
    plt.figure(figsize=(9, 5))

    for case, case_rows in sorted(
        cases.items(),
        key=lambda item: str(item[0]),
    ):
        rows_by_category = {
            row[key]: row
            for row in case_rows
        }
        all_categories_have_value = all(
            category in rows_by_category
            and rows_by_category[category].get(value) is not None
            for category in cats
        )
        if not all_categories_have_value:
            continue

        y_values = [
            rows_by_category[category][value]
            for category in cats
        ]
        plt.plot(
            range(len(cats)),
            y_values,
            alpha=0.4,
            label=case_rows[0]['graph'],
        )
        drawn_graphs += 1

        for position, category in enumerate(cats):
            if rows_by_category[category]['proof'] == 'optimal':
                marker = 'o'
            else:
                marker = 'x'
            plt.scatter(position, y_values[position], marker=marker, s=20)

        if drawn_graphs == 12:
            break

    if not drawn_graphs:
        plt.close()
        no_data(title)
    else:
        plt.xticks(range(len(cats)), cats)
        plt.ylabel(value)
        plt.title(
            title
            + '\nFirst 12 graph IDs; circle=optimal, x=unproven'
        )
        plt.legend(fontsize=6, ncol=2)

    save(name)

def performance_profile(
    rows,
    categories=BACKENDS,
    best_sources=None,
):
    cases = grouped(
        rows,
        lambda row: stratum(row, 'p2b'),
    )
    runtime_ratios = defaultdict(list)

    for case_rows in cases.values():
        usable_rows = []
        for row in case_rows:
            is_proven = row['proof'] == 'optimal'
            is_best_observed = (
                best_sources is not None
                and row['source'] in best_sources
            )
            has_positive_runtime = (
                row['total_time'] is not None
                and row['total_time'] > 0
            )

            if (
                (is_proven or is_best_observed)
                and has_positive_runtime
            ):
                usable_rows.append(row)

        if not usable_rows:
            continue

        fastest_runtime = min(
            row['total_time']
            for row in usable_rows
        )
        for row in usable_rows:
            ratio = row['total_time'] / fastest_runtime
            runtime_ratios[row['encoding']].append(ratio)

    if not cases or not runtime_ratios:
        return {}

    largest_ratio = max(
        max(ratios)
        for ratios in runtime_ratios.values()
    )
    maximum_x_value = max(2, largest_ratio * 1.05)

    profile_points = {}
    for category in categories:
        category_ratios = runtime_ratios[category]
        x_values = sorted(
            set([1, maximum_x_value] + category_ratios)
        )
        category_points = []

        for x_value in x_values:
            successful_cases = sum(
                ratio <= x_value
                for ratio in category_ratios
            )
            fraction = successful_cases / len(cases)
            category_points.append((x_value, fraction))

        profile_points[category] = category_points

    return profile_points

def best_observed_sources(rows, part='p2b'):
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

def comparative_outcome(row, best_sources):
    if row['proof'] == 'optimal':
        return 'optimal'
    if row['source'] in best_sources:
        return 'best_observed'
    if row['proof'] == 'feasible':
        return 'feasible'
    return 'unknown'