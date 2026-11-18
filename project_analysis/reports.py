import importlib

if __package__:
    from .reports_common import (
        AXIS_LABELS, BACKENDS, FIG, FIGURE_STATUS,
        GRAPH_GROUP_ORDER, P2B_ENCODINGS, P2B_METHODS,
        Path, ROOT, SAT, TABLES,
        best_observed_sources, boxes, clean_runs,
        combinations, common, comparative_outcome, csv,
        defaultdict, emit, figure_presentation,
        graph_category_sort_key, graph_group_sort_key, graph_id_sort_key, grouped,
        has_plotted_data, heat, iqr,
        matplotlib, median, no_data, number, paired,
        performance_profile, plt, read_csv,
        save, select, statistics, stratum, table, write_csv, write_figure_status,
    )
else:
    from reports_common import (
        AXIS_LABELS, BACKENDS, FIG, FIGURE_STATUS, GRAPH_GROUP_ORDER, P2B_ENCODINGS, P2B_METHODS,
        Path, ROOT, SAT, TABLES,
        best_observed_sources, boxes, clean_runs,
        combinations, common, comparative_outcome, csv,
        defaultdict, emit, figure_presentation, graph_category_sort_key,
        graph_group_sort_key, graph_id_sort_key, grouped,
        has_plotted_data, heat, iqr,
        matplotlib, median, no_data,
        number, paired, performance_profile, plt, read_csv, save, select, statistics, stratum,
        table, write_csv, write_figure_status,
    )

if __package__:
    _overview = importlib.import_module('.02_overview_tables', __package__)
    _part1 = importlib.import_module('.03_part1_encodings', __package__)
    _part2a = importlib.import_module('.04_part2a_sat_methods', __package__)
    _part2b = importlib.import_module('.05_part2b_solver_families', __package__)
    _part3 = importlib.import_module('.06_part3_k_sweep', __package__)
    _findings = importlib.import_module('.report_findings', __package__)
    from . import reports_common as _shared
else:
    _overview = importlib.import_module('02_overview_tables')
    _part1 = importlib.import_module('03_part1_encodings')
    _part2a = importlib.import_module('04_part2a_sat_methods')
    _part2b = importlib.import_module('05_part2b_solver_families')
    _part3 = importlib.import_module('06_part3_k_sweep')
    _findings = importlib.import_module('report_findings')
    import reports_common as _shared

_base_save = _shared.save
_base_select = _shared.select

def _call_shared_function(function, *args, **kwargs):
    shared_names = [
        name
        for name in globals()
        if not name.startswith('_') and hasattr(_shared, name)
    ]
    previous_values = {
        name: getattr(_shared, name)
        for name in shared_names
    }

    for name in shared_names:
        setattr(_shared, name, globals()[name])

    try:
        return function(*args, **kwargs)
    finally:
        for name, value in previous_values.items():
            setattr(_shared, name, value)

def save(name):
    return _call_shared_function(_base_save, name)

def select(*args, **kwargs):
    return _call_shared_function(_base_select, *args, **kwargs)

def _invoke_section(module, function_name, *args, **kwargs):
    facade_names = [
        name
        for name in globals()
        if not name.startswith('_') and hasattr(_shared, name)
    ]
    previous_shared_values = {
        name: getattr(_shared, name)
        for name in facade_names
    }
    previous_module_values = {
        name: getattr(module, name)
        for name in facade_names
        if hasattr(module, name)
    }

    for name in facade_names:
        value = globals()[name]
        setattr(_shared, name, value)
        if hasattr(module, name):
            setattr(module, name, value)

    try:
        return getattr(module, function_name)(*args, **kwargs)
    finally:
        for name, value in previous_module_values.items():
            setattr(module, name, value)
        for name, value in previous_shared_values.items():
            setattr(_shared, name, value)

def overview(runs, issues):
    return _invoke_section(_overview, 'overview', runs, issues)

def part1(runs, method='Repeated', exploratory=False):
    return _invoke_section(_part1, 'part1', runs, method, exploratory)

def part2a(runs, exploratory=False):
    return _invoke_section(_part2a, 'part2a', runs, exploratory)

def part2b(runs, exploratory=False):
    return _invoke_section(_part2b, 'part2b', runs, exploratory)

def part3():
    return _invoke_section(_part3, 'part3')

def conclusions(runs):
    return _invoke_section(_findings, 'conclusions', runs)

def empirical_findings():
    return _invoke_section(_findings, 'empirical_findings')

def write_figure_status():
    _shared.ROOT = ROOT
    _shared.FIG = FIG
    _shared.TABLES = TABLES
    _shared.FIGURE_STATUS = FIGURE_STATUS
    return _shared.write_figure_status()