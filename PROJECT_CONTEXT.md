# ChequeVerify — full research handoff

Handoff date: 26 November 2026 (Pakistan). Working name is provisional. Course: Computer Vision, Department of AI & DS, FAST-NUCES, Fall 2026. The student is using Claude Code on Windows 11 with a Dell Latitude 7430, Intel Core i7 12th generation, 16 GB RAM, integrated graphics (no dedicated NVIDIA GPU reported). Preferred working directory `D:\Projects\ChequeVerify`; use actual current project root if different. Budget: zero additional paid tools/compute; CPU first, free Colab if necessary. Student prefers one copyable prompt and one evidence-backed milestone at a time.

## Approved topic (as supplied)
Domain: Finance & Banking. Subdomain: Check verification.
Description: This project develops specialized vision models to analyze physical banking checks and financial slips. Students will utilize handwriting recognition, signature verification matching, and forensic pixel analysis to detect fraudulent alterations, amount discrepancies, and forged authorizations within automated banking clearing pipelines.

Two candidate papers were approved by the professor. Student wants exactly ONE, chosen for lowest implementation/training complexity while meeting the actual rubric. The description lists multiple capabilities; whether a focused amount-verification scope is sufficient has not been confirmed by the professor. Ask the student to seek clarification; do not invent an approval. No need to implement all three tasks unless required.

## Instructor requirements — controlling specification
Read `research/guidelines/Professor_Guidelines.pdf` (6 pages) and optional `Professor_Guidelines.md` extraction. The original PDF controls. Requirements:
- Implement reproducible core methodology of selected paper(s), plus functional data acquisition → preprocessing → training/inference → evaluation → deployment/demo pipeline.
- Document custom/public dataset, challenging conditions, stress-test subset, sources, sizes, formats, preprocessing, curation/augmentation, ethics/legal constraints.
- Systematically identify failures under differing conditions (lighting, occlusion, domain shift, imbalance, noise, low resolution, OOD etc.). Diagnose root causes with quantitative and visual evidence.
- Design, justify and implement a concrete methodological, architectural, data-centric or training-level improvement. Training from scratch is not stated as mandatory; the guideline allows inference and pretrained weights if applicable. An unchanged model wrapper alone is insufficient.
- Compare baseline vs improved quantitatively and qualitatively on standard and challenging sets; document trade-offs and ablations where applicable. Demonstrate improved handling of failures live; reproducibility mandatory.
- Source code separated into baseline/improved, training/evaluation/inference scripts as applicable (explain if no training performed, provide upstream training instructions and applicable pipeline scripts), configs, pretrained weights if applicable and redistribution permitted, dataset or download instructions, README installation/run instructions and expected output examples.
- Report: abstract, introduction/problem, literature review, baseline architecture, dataset incl. challenging subsets, failure/root-cause analysis, proposed improvement/rationale, implementation, experiments/results/comparisons/ablations where applicable, discussion/trade-offs/remaining limitations, conclusion/future work, citations.
- Presentation 10–15 minutes covering problem, baseline, failures, modifications, comparative evaluation, live before/after demo, insights and contributions. Submit PPTX.
- Academic integrity: no plagiarism, undisclosed borrowed code/data, copied report text, manipulated or cherry-picked results, or work completed by another student or external party. Consequences zero credit and F in course. AI assistance policy is not explicitly specified; student must confirm permissible scope and own assessed work, cite reuse, and independently understand and defend it.
- GCR: code ZIP/GitHub link, dataset files/link incl. stress split, report PDF, slides PPTX. Late penalties apply; submissions close 3 days after due date. Only report weighting (20%) is visible; other category weights are truncated in original PDF, do not guess.

| Deadline | Deliverable |
|---|---|
| 2 Dec 2026 | Implementation, models, dataset |
| 3 Dec 2026 | Report and documentation |
| 4 Dec 2026 | Presentation submission/delivery and live demonstration |

## Candidate 1 — ProtoSig
Kecia G. de Moura, Robert Sabourin, Rafael M.O. Cruz. Pattern Recognition 180 (2026), 114258. DOI https://doi.org/10.1016/j.patcog.2026.114258 . Official publication https://pure.etsmtl.ca/en/publications/protosig-enhancing-training-data-for-offline-handwritten-signatur/ . Archive `research/paper1/Paper 1.md` contains all extracted text of 77 unique pages, six research articles and an editorial board document. Only ProtoSig is directly relevant to the approved candidate. The other five articles are independent articles, not supplementary materials; don't implement them. Original standalone PDF and issue PDFs, plus rendered pages, are in the archive. ProtoSig full paper reviewed previously; other papers extracted in full but not manually reviewed word-for-word. Separate supplement missing.
- Core: pretrained SigNet-S extracts 2048-d embeddings, cluster development signatures once, K-means k=50 prototype vectors as negatives; use each writer's genuine signatures as positives and fit WD RBF-SVM (C=1, gamma=2^-11). Inference requires enrollment and writer-specific classifiers. No neural training may be needed but K-means/SVM fitting is mandatory to reproduce the methodology.
- Preprocessing: centered canvas, Otsu background removal, invert, resize 170×242, center crop 150×220. Datasets CEDAR, MCYT-75, GPDS Synthetic. EER/FAR/FRR. Paper's original results are not our own. Exact source, licenses, data availability and SigNet-S compatibility not verified locally. Prior discussion identified possible noncommercial backbone restrictions; verify actual license. Exact ProtoSig repo was not confirmed.
- Paper reports 97.39 s vs 1.01 s SVM training on its largest GPDS-S config, not local results; prose ratio discrepancy noted in archive. This paper is a fallback, not a second implementation target.

## Candidate 2 — LoGo-HTR (conditionally selected)
Shree Mitra, Ajoy Mondal, C.V. Jawahar, IIIT Hyderabad. Learning Beyond Labels: Self-Supervised Handwritten Text Recognition, WACV 2026, pages 6653–6663. Full 11-page paper, all 60 bibliography entries and figures/tables archived; supplementary Appendices A–G not supplied. Read `research/paper2/paper2.md` and `research/paper2/original/paper2(1).pdf`.
- Official paper: https://openaccess.thecvf.com/content/WACV2026/papers/Mitra_Learning_Beyond_Labels_Self-Supervised_Handwritten_Text_Recognition_WACV_2026_paper.pdf
- Project: https://logo-ssl.github.io/
- Code: https://github.com/shreemitra/LoGoHTR
- Model listing: https://huggingface.co/Shree10/LoGo-HTR
- Dataset listing: https://huggingface.co/datasets/Shree10/SSL-HWD-Words
- Prior conversation reported two publicly listed files: `Downstream_Full_Model_Best.ckpt` (~52 MB), `DenseNet_backbone_step290000.pth` (~12.2 MB), and Apache 2.0 model-repository listing. These are historical reported listing observations, NOT verified downloads, actual license rights for every component, checkpoint compatibility, or successful local inference. Verify all independently; repo may have changed. Do not assume model training corpus or vocabulary from filename.
- Model: SSL local patch contrastive + global Barlow Twins decorrelation pretraining, then supervised downstream CoMER transformer with coverage attention/ARM. DenseNet 3 blocks of 16 bottleneck layers; growth 24, dropout 0.2, compression 0.5; local/global weights 0.6/0.4; 5×5 patches after first conv; projection 1024→512; decoder 3 layers, d=256, FFN=1024, 8 heads, dropout 0.3. Paper reports 6.4M parameters, original two RTX A6000 48GB each. Confirm checkpoint/config from code, don't force inferred values.
- SSL-HWD: 10M word images, 852 writers, 81,280 pages, 2.08M labeled / 7.92M unlabeled; labeled 60/40 split. IAM, GNHK, RIMES, LAM benchmarks. Table 3 full-label WER/CER: IAM 10.27/2.01, GNHK 12.07/7.20, RIMES 5.50/1.78, LAM 6.3/2.39 (authors' results). Table 4 own-domain 5.20/1.20. RIMES prose 80% conflicts with table 60% (7.20/2.38); LAM 6.3 vs 6.9 across tables; preserve discrepancies, don't claim replication.
- Complete encoder+decoder checkpoint may permit inference with zero training. Encoder-only cannot produce text. Code reportedly includes architecture/transforms/dictionary/decoding but no straightforward single-image inference command; inspect actual repository. CPU throughput and numeric capability unverified. Original full pretraining is infeasible on available hardware/time. No large dataset downloads at first gate.
- Decision: LoGo-HTR is preferred over ProtoSig because a full downstream checkpoint was reportedly listed, no enrollment/classifier fit should be necessary, and a training-free preprocessing robustness study is feasible if actual failures and improvements are measured. Selection is CONDITIONAL on actual checkpoint load and genuine inference. No final commitment if blocked. Do not switch papers without student review.

## Proposed research/product — hypothesis, not an established result
Working title: Robust Handwritten Bank Cheque Amount Verification Using Adaptive Image Enhancement and Self-Supervised Handwriting Recognition.
Baseline: authors' unchanged compatible checkpoint, original preprocessing and decoding. Improved candidate: quality-aware adaptive preprocessing or multi-view inference using the same frozen model. First measure failures; only then choose improvements (e.g. illumination normalization, CLAHE, gamma, denoising, deskew, background suppression). No claim any method improves accuracy until measured. Evaluate added latency and clean performance. Freeze final test split and transform seeds before tuning. Use same source images/labels and corruptions for paired comparisons; avoid writer/document leakage, including related augmented copies; report denominator, aggregate metrics, per-condition severity and all failures. Separate standard benchmark and held-out bank-specific stress test. Use data with clear rights, documented labels and consent/synthetic bank checks. No claim of full benchmark reproduction if only subset tested; disclose checkpoint domain and overlap uncertainty. Aim for CER/WER/WRR (define exactly; WRR not always 100-WER), numeric exact match, written amount accuracy, amount discrepancy detection metrics, latency; uncertainty/review coverage if used. Include clean performance, ablation and paired uncertainty estimates where feasible.

Product idea: upload sample cheque → locate amount regions (manual selection or known template first; full check localization is separate from paper) → original or improved HTR → normalize numeric and written amounts independently → compare, show evidence and flag uncertainty for human review → report. Use a focused template or manual crop if arbitrary layout detection is too costly. Never auto-clear cheques or claim signature forgery/pixel tampering detection from this model. Do not add unrelated functionality without scope approval. Frontend/backend technology deferred until feasibility passes; local lightweight web demo preferred over complex infrastructure.

## Schedule / milestones
M0 professor requirements reviewed (VERIFIED); M1 both relevant paper bodies reviewed and archived (VERIFIED for document review, not replication); M2 selection (PARTIAL/conditional); M3-A checkpoint and smoke inference (NOT STARTED). M4 dataset sourcing/splits, M5 baseline evaluation, M6 stress/failure analysis, M7 improve, M8 comparative/ablation evaluation, M9 application, M10 reproducibility and testing, M11 report, M12 presentation/demo: NOT STARTED. Suggested dates 26 Nov smoke, 27 Nov dataset+baseline, 28 Nov failure analysis, 29 Nov improvements, 30 Nov comparisons and app, 1 Dec integration and submission preparation; 2–4 Dec formal deadlines. This is a proposed schedule, not a promise. Prioritize evidence over UI. Stop on each gate for review. Only M3-A authorized now.

## Source index and authority
`research/guidelines/Professor_Guidelines.pdf`: authoritative rubric.
`research/paper2/paper2.md`, `original/paper2(1).pdf`, `pages/`: candidate 2 notes, complete native extraction, original and rendered pages.
`research/paper1/Paper 1.md`, `sources/`, `pages/`: candidate 1 plus supplied issue archive, original PDFs and rendered pages. Other articles not required to reread at M3-A. Native extraction may alter symbols/columns/image-only text; original PDF controls. The source archive is for private research reference, not redistribution/submission as original work. Separate supplements missing; find legally from official project/publisher only if needed. No checkpoints or upstream source code shipped in this handoff; acquire and verify independently.

## Decisions update (2026-11-26, after M3-A, M3-B and M4 work)
This section supersedes conflicting status lines above. Earlier text is kept as the original handoff.
- **Paper:** LoGo-HTR is the single selected paper, FINALIZED WITH DOCUMENTED LIMITATIONS. ProtoSig is dropped. The professor permits a single-paper baseline.
- **Milestones:** M0, M1, M2, M3-A and M3-B are VERIFIED. M4 is current (PARTIAL: custom data not yet collected). See `PROJECT_TRACKER.md`.
- **Scope:** handwritten cheque amount recognition and numeric/words discrepancy detection with human review. Signature verification and forensic tampering detection appear in the approved topic description but are out of scope unless explicitly authorised.
- **Documented limitations:**
  - The checkpoint's fine-tuning dataset is unknown, so training/evaluation overlap cannot be ruled out.
  - M3-A showed checkpoint feasibility only.
  - M3-B was exploratory: 9 samples from one writer. Its 21 inference entries are conditions or derived crops of those 9 samples, not independent samples.
  - Manually segmented words are not automatic full-line recognition.
  - The model has never emitted a space token.
  - The paper's published benchmark scores have not been independently reproduced.
- **Ground truth:** M3-B H05 = `75,450.50`, confirmed by the writer (a visual audit had proposed `75,430.50`). H04 stays ambiguous (`1250-00` / `1250.00`). See `artifacts/M3_B_final/CORRECTION_LOG.md`.
- **Data:** the standard benchmark is the GNHK test-split subset (CC-BY-4.0, 240 words, page-disjoint dev/test). The custom banking set is designed (`artifacts/M4/`) but not collected. The baseline definition is in `artifacts/M4/BASELINE_DEFINITION.md`.
- **Environment:** the actual project root is this OneDrive folder (`D:\Projects` does not exist). Do not relocate without authorisation.

## Decisions update (2026-11-26, M4-ONLINE)
- **Collection retired.** The student will not collect handwriting manually; the ArUco sheet workflow is optional only, and M4-PILOT is superseded, not passed.
- **Evaluation data now:**
  - D1 GNHK subset (genuine);
  - D4 CVL digit strings (genuine, CC-BY-NC-4.0, writer-disjoint);
  - D5 GNHK number-word pairs (genuine, constructed);
  - D6 synthetic cheques (font-rendered, HF arunchincheti/cheques_data).
  - See `artifacts/M4_ONLINE/`.
- **No genuine English handwritten cheque dataset was obtainable** (IDRBT unreachable, ORAND-CAR gated). Report genuine and synthetic results separately, and never present D6 as handwriting.
- **M4 is VERIFIED** under the revised strategy. Next is M5 (baseline evaluation), awaiting authorisation.

## Decisions update (2026-11-26, M4-FINAL)
- **Final datasets are frozen** (hashes in `artifacts/M4_FINAL/SUMMARY.json`). IDRBT could not be downloaded (DNS failure), so the genuine multiword written-amount gap remains.
- **Blank synthetic fields** (24) are excluded from recognition metrics. Unresolved pairs are reported separately.
- **M4 status:** VERIFIED WITH DOCUMENTED LIMITATIONS.
