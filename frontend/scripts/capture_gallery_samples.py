"""Capture three predetermined DEV crops, once in each mode; never use TEST."""
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import urllib.request
from capture_backend_results import multipart, sha

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / 'frontend/public'
run = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-gallery'
out = PUBLIC / 'results' / run
out.mkdir(parents=True, exist_ok=False)
with urllib.request.urlopen('http://127.0.0.1:8000/health') as r:
    assert json.load(r)['model_loaded']
studies = []
# Select by source order/category before inference, not by model outcome.
for dataset, category, slug, title in [
    ('cvl_numeric', 'cvl_numeric', 'digits', 'A longer digit string.'),
    ('gnhk_pairs', 'gnhk_numeric', 'handwriting', 'A small handwritten field.'),
    ('syn_cheques', 'syn_num', 'synthetic', 'Another scale. Another reading.'),
]:
    manifest = json.loads((ROOT / f'data/benchmarks/{dataset}/manifest.json').read_text())
    candidates = [s for s in manifest['samples'] if s['split'] == 'dev' and s['category'] == category and s['ground_truth'] not in ('1', 'one', '3083')]
    sample = candidates[0]
    path = ROOT / sample['file']
    assert sha(path.read_bytes()) == sample['sha256']
    shutil.copyfile(path, out / path.name)
    study = dict(id=slug, title=title, split='dev', synthetic=not sample['genuine_handwriting'], source_path=sample['file'], source_id=sample['id'], licence=manifest['license'], image=f'/results/{run}/{path.name}', image_sha256=sample['sha256'], responses={})
    for mode in ('baseline', 'proposed'):
        data, headers = multipart({'mode': mode, 'field_type': 'numeric'}, 'image', path)
        request = urllib.request.Request('http://127.0.0.1:8000/api/recognize', data=data, headers=headers)
        with urllib.request.urlopen(request, timeout=260) as r:
            raw = r.read()
            request_id = r.headers.get('X-Request-ID')
        name = f'{slug}-{mode}.json'
        (out / name).write_bytes(raw)
        result = json.loads(raw)
        study['responses'][mode] = dict(path=f'/results/{run}/{name}', sha256=sha(raw), request_id=request_id, result=result)
        print(slug, mode, result['raw_text'], result['parsed_value'], flush=True)
    studies.append(study)
index = dict(run_id=run, captured_at=datetime.now(timezone.utc).isoformat(), selection='First DEV crop per category excluding previously displayed 1/one/3083; selected before inference. No outcome filtering.', notice='Individual development demonstrations, not an accuracy evaluation. Ground truth is never substituted for model output.', studies=studies)
(out / 'manifest.json').write_text(json.dumps(index, indent=2) + '\n')
(PUBLIC / 'gallery/samples.json').write_text(json.dumps(index, indent=2) + '\n')
generated = ROOT / 'frontend/src/generated/sampleStudies.ts'
generated.write_text('// Generated from exact local API response captures. See public/gallery/samples.json.\nexport const sampleStudies = ' + json.dumps(studies, indent=2) + ' as const;\n')
print('Saved supplemental capture', run)
