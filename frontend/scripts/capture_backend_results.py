"""Capture real local API responses, without changing frozen project inputs.

Run from repo root with .venv/Scripts/python.exe frontend/scripts/capture_backend_results.py.
Only constructed DEV demos and short crops are inferred. Benchmark is GET-only.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import urllib.request
import uuid

ROOT = Path(__file__).resolve().parents[2]
PUBLIC = ROOT / 'frontend/public/results'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def multipart(fields, file_field, path):
    boundary = 'ChequeVerify' + uuid.uuid4().hex
    body = bytearray()
    for name, value in fields.items():
        body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
    body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; filename="{path.name}"\r\nContent-Type: image/png\r\n\r\n'.encode())
    body.extend(path.read_bytes())
    body.extend(f'\r\n--{boundary}--\r\n'.encode())
    return bytes(body), {'Content-Type': f'multipart/form-data; boundary={boundary}'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    args = parser.parse_args()
    base = args.base_url.rstrip('/')
    run_id = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ') + '-' + uuid.uuid4().hex[:6]
    out = PUBLIC / run_id
    out.mkdir(parents=True, exist_ok=False)
    records = []

    def capture(name, endpoint, fields=None, file_field=None, image=None, extra=None):
        data, headers = multipart(fields, file_field, image) if image else (None, {})
        started = datetime.now(timezone.utc).isoformat()
        req = urllib.request.Request(base + endpoint, data=data, headers=headers)
        with urllib.request.urlopen(req, timeout=260) as response:
            raw = response.read()
            status, request_id = response.status, response.headers.get('X-Request-ID')
        result = json.loads(raw)
        # Preserve the exact response bytes, not a manually reconstructed result.
        (out / f'{name}.json').write_bytes(raw)
        record = dict(id=name, endpoint=endpoint, method='POST' if image else 'GET',
                      captured_at=started, http_status=status, request_id=request_id,
                      response=f'/results/{run_id}/{name}.json', response_sha256=sha(raw))
        if image:
            target = out / image.name
            if not target.exists():
                shutil.copyfile(image, target)
            record.update(image=f'/results/{run_id}/{image.name}', source_path=image.relative_to(ROOT).as_posix(),
                          image_sha256=sha(image.read_bytes()), fields=fields)
        record.update(extra or {})
        records.append(record)
        print(f'{name}: HTTP {status}' + (f", decision={result['decision']}" if 'decision' in result else ''), flush=True)
        return result

    health = capture('health', '/health')
    if not health.get('model_loaded'):
        raise RuntimeError('Backend model is not loaded; no inference attempted')
    info = capture('model-info', '/api/model-info')
    capture('benchmark', '/api/benchmark', extra={'kind': 'saved_research', 'note': 'Existing locked-test metrics read through the API; no evaluation rerun.'})
    demos = json.loads((ROOT / 'data/demo/demo_manifest.json').read_text())
    for name, sheet in demos['sheets'].items():
        fields = {'mode': 'baseline', 'numeric_roi': json.dumps(sheet['numeric']['roi']), 'written_roi': json.dumps(sheet['written']['roi'])}
        result = capture(name, '/api/verify', fields, 'cheque_image', ROOT / sheet['file'],
                         {'kind': 'verification', 'description': sheet['description'], 'split': 'dev',
                          'constructed': True, 'synthetic': name == 'sheet_review',
                          'licences': [sheet['numeric']['licence'], sheet['written']['licence']]})
        expected = {'sheet_accept': 'accept', 'sheet_flag': 'flag', 'sheet_review': 'review'}[name]
        if result['decision'] != expected:
            raise RuntimeError(f'{name}: actual {result["decision"]} differs from documented {expected}; capture retained, latest index not published')
        for field in ('numeric', 'written'):
            actual = result['rois'][field + '_px']
            if any(abs(a-b) > 1 for a, b in zip(actual, sheet[field]['box_px'])):
                raise RuntimeError(f'{name}: ROI mismatch; latest index not published')
    for mode in ('baseline', 'proposed'):
        capture('numeric-' + mode, '/api/recognize', {'mode': mode, 'field_type': 'numeric'}, 'image',
                ROOT / 'data/benchmarks/syn_cheques/SYN_0001_num.png',
                {'kind': 'recognition', 'description': 'Synthetic numeric DEV crop; the same input in both modes.', 'split': 'dev', 'synthetic': True,
                 'licences': ['arunchincheti/cheques_data, Apache-2.0 (declared)']})
    capture('written-baseline', '/api/recognize', {'mode': 'baseline', 'field_type': 'written'}, 'image',
            ROOT / 'data/benchmarks/gnhk_pairs/GNHKP_eng_EU_117_w051.png',
            {'kind': 'recognition', 'description': 'Genuine handwritten word from a DEV crop, not a real cheque.', 'split': 'dev', 'synthetic': False,
             'licences': ['GNHK, CC-BY-4.0']})
    manifest = dict(run_id=run_id, captured_at=datetime.now(timezone.utc).isoformat(), base_url=base,
                    source_git_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
                    checkpoint_sha256=info['checkpoint_sha256'], upstream_commit=info['upstream_commit'],
                    notice='Constructed DEV demonstration captures, not a new accuracy evaluation. Only the benchmark endpoint contains the previously saved locked-test results.', records=records)
    (out / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n', encoding='utf-8')
    # Publish only a complete capture. Older runs are never overwritten.
    (PUBLIC / 'latest.json').write_text(json.dumps({'manifest': f'/results/{run_id}/manifest.json'}) + '\n', encoding='utf-8')
    print(f'Saved {len(records)} actual responses in {out}', flush=True)


if __name__ == '__main__':
    main()
