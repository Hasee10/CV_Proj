# M4-FINAL commands (PowerShell, project root)

```powershell
# IDRBT direct ZIP (attempted; DNS failure)
curl.exe -sSL --max-time 90 --connect-timeout 20 -o IDRBT_Cheque_Image_Dataset.zip "https://www.idrbt.ac.in/wp-content/uploads/2022/07/IDRBT_Cheque_Image_Dataset.zip"
# integrity audit (pixel evidence, lineage, overlap, provenance)
.\.venv\Scripts\python.exe -X utf8 -I scripts\audit_integrity.py artifacts\M4_FINAL\INTEGRITY_EVIDENCE.json
# joint validation of the frozen manifests and pairs
.\.venv\Scripts\python.exe -I scripts\validate_manifest.py data\public\gnhk\subset\manifest.json data\benchmarks\cvl_numeric\manifest.json data\benchmarks\gnhk_pairs\manifest.json data\benchmarks\syn_cheques\manifest.json --resolved data\benchmarks\duplicate_review.json --pairs data\benchmarks\amount_pairs.json --out artifacts\M4_FINAL\VALIDATION_REPORT.json
# regression tests (also runs the 27-test audit suite)
.\.venv\Scripts\python.exe -X utf8 -I tests\test_m4_online.py
```
