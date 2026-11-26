# M4-PILOT commands (PowerShell, project root)

```powershell
# 1. locate the photo (attempt 1: data/custom/raw/ was empty)
Get-ChildItem data\custom\raw
# 2. pilot extraction (attempt 1 result: "W01_A: no single valid photo found", exit 1, nothing written)
.\.venv\Scripts\python.exe -X utf8 -I scripts\custom_sheets.py extract --only W01_A
```
To run once the photo is present: repeat step 2, then inspect `data/custom/crops/W01_A_*.png` and `data/custom/annotation.csv`.
No inference, training, downloads or finalisation were performed.
