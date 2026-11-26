# M10-A commands

```powershell
# start the real backend (loads the checkpoint once)
.venv\Scripts\python.exe -X utf8 -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
# in a second terminal: exercise every endpoint over HTTP; writes artifacts\M10\LIVE_HTTP_CHECK.json and openapi.json
.venv\Scripts\python.exe -X utf8 -I scripts\m10_live_check.py
# backend tests (examples in artifacts\M10\examples\ are written by the integration tests)
.venv\Scripts\python.exe -X utf8 -m pytest tests\test_backend_unit.py tests\test_backend_integration.py -q
```
