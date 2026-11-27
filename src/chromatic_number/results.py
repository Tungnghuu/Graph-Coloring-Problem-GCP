"""Attempt CSV plus an atomic run manifest. Legacy columns remain readable."""
import csv
import hashlib
import json
import os
import platform
import uuid
from datetime import datetime, timezone
from importlib.metadata import version, PackageNotFoundError
from pathlib import Path
from time import perf_counter


def environment():
    versions = {}
    for package in ('python-sat','gurobipy','docplex','cplex'):
        try: versions[package] = version(package)
        except PackageNotFoundError: versions[package] = None
    cpu = platform.processor()
    try:
        cpu = next(line.split(':',1)[1].strip() for line in Path('/proc/cpuinfo').read_text().splitlines() if line.startswith('model name'))
    except (OSError, StopIteration): pass
    try: ram = os.sysconf('SC_PAGE_SIZE') * os.sysconf('SC_PHYS_PAGES')
    except (ValueError, OSError, AttributeError): ram = None
    return dict(cpu=cpu, ram_bytes=ram, os=platform.platform(), python=platform.python_version(), versions=versions)

class ResultsWriter:
    FIELDNAMES = ['method','encoding','k','status','num_variables','num_clauses',
        'valid_coloring','bounds_time','encoding_time','solving_time','total_time',
        'setup_time','solver_called','timeout_phase','backend_status','timed_out','best_k']

    def __init__(self, col_file_path, metadata=None):
        path = Path(col_file_path)
        self.file_path = path if path.suffix.lower()=='.csv' else Path('results') / f'{path.stem}.csv'
        self.file_path.parent.mkdir(parents=True,exist_ok=True)
        self.started = perf_counter()
        self.meta = dict(schema_version=2, run_id=str(uuid.uuid4()), started_at=datetime.now(timezone.utc).isoformat(),
                         environment=environment(), completion='Partial', **(metadata or {}))
        config = {k:v for k,v in self.meta.items() if k not in ('run_id','started_at','completion','graph','initial_lb','initial_ub','bounds_time')}
        # Include source fingerprints so old/new encodings cannot silently mix.
        source_root = Path(__file__).resolve().parents[1]
        digest = hashlib.sha256()
        for source in sorted(source_root.rglob('*.py')):
            digest.update(str(source.relative_to(source_root)).encode()); digest.update(source.read_bytes())
        self.meta['implementation'] = digest.hexdigest()
        config['implementation'] = self.meta['implementation']
        self.meta['config_id'] = hashlib.sha256(json.dumps(config,sort_keys=True).encode()).hexdigest()[:16]
        with self.file_path.open('w',newline='') as f:
            csv.DictWriter(f,fieldnames=self.FIELDNAMES).writeheader()
        self._manifest()
        self.started = perf_counter()

    def _manifest(self):
        path = self.file_path.with_suffix('.meta.json')
        tmp = path.with_suffix('.json.tmp')
        tmp.write_text(json.dumps(self.meta,indent=2),encoding='utf-8')
        tmp.replace(path)

    def save(self, result):
        with self.file_path.open('a',newline='') as f:
            csv.DictWriter(f,fieldnames=self.FIELDNAMES).writerow(result)

    def finish(self, *, completion, lower_bound, best_k, reason):
        self.meta.update(completion=completion, final_lb=lower_bound, best_k=best_k,
                         termination_reason=reason, search_wall_time=perf_counter()-self.started,
                         ended_at=datetime.now(timezone.utc).isoformat())
        self.meta['total_wall_time'] = self.meta['search_wall_time'] + self.meta.get('bounds_time',0)
        self._manifest()
