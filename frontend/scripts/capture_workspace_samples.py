"""Supplement the live lab with predetermined DEV examples, preserving exact responses."""
from datetime import datetime, timezone
import json
import shutil
import urllib.request
from pathlib import Path
from capture_backend_results import multipart, sha

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / 'frontend/public'
run = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-workspace'
out = PUBLIC / 'results' / run
out.mkdir(parents=True, exist_ok=False)
with urllib.request.urlopen('http://127.0.0.1:8000/health') as r:
    assert json.load(r)['model_loaded']
studies = []
for dataset, source_id, slug, title, field_type in [
    ('cvl_numeric', 'CVL_136075_0002_03', 'digit-string-02', 'Digit string / CVL 02', 'numeric'),
    ('syn_cheques', 'SYN_0031_num', 'synthetic-02', 'Numeric field / Synthetic 02', 'numeric'),
    ('syn_cheques', 'SYN_0032_num', 'synthetic-03', 'Numeric field / Synthetic 03', 'numeric'),
    ('syn_cheques', 'SYN_0013_words', 'written-02', 'Written amount / Synthetic', 'written'),
]:
    manifest = json.loads((ROOT / f'data/benchmarks/{dataset}/manifest.json').read_text())
    sample = next(s for s in manifest['samples'] if s['id'] == source_id)
    assert sample['split'] == 'dev'
    path = ROOT / sample['file']
    assert sha(path.read_bytes()) == sample['sha256']
    shutil.copyfile(path, out / path.name)
    study = dict(id=slug, title=title, field_type=field_type, split='dev', synthetic=not sample['genuine_handwriting'], source_path=sample['file'], source_id=source_id, licence=manifest['license'], image=f'/results/{run}/{path.name}', image_sha256=sample['sha256'], responses={})
    # Written ATHN can be slow; retain both methods faithfully without automatic retries.
    for mode in ('baseline', 'proposed'):
        data, headers = multipart({'mode': mode, 'field_type': field_type}, 'image', path)
        request = urllib.request.Request('http://127.0.0.1:8000/api/recognize', data=data, headers=headers)
        with urllib.request.urlopen(request, timeout=260) as r:
            raw, request_id = r.read(), r.headers.get('X-Request-ID')
        name = f'{slug}-{mode}.json'
        (out / name).write_bytes(raw)
        result = json.loads(raw)
        study['responses'][mode] = dict(path=f'/results/{run}/{name}', sha256=sha(raw), request_id=request_id, result=result)
        print(slug, mode, repr(result['raw_text']), result['parsed_value'], flush=True)
    studies.append(study)
manifest = dict(run_id=run, captured_at=datetime.now(timezone.utc).isoformat(), selection='Four source IDs chosen before inference; DEV only; no outcome filtering.', studies=studies)
(out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
(ROOT / 'frontend/src/generated/workspaceSamples.ts').write_text('// Exact DEV API captures; see public/results/' + run + '/manifest.json.\nexport const workspaceSamples = ' + json.dumps(studies, indent=2) + ' as const;\n')
print('Saved', run)
