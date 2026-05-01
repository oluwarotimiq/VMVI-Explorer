# VMVI Dataset Exploration and Recognition

This workspace contains the rebuilt image-only VMVI project. The current direction is dataset exploration and supervised vehicle interaction recognition, with the earlier clustering pipeline retained as a baseline.

## Current A+ Project Direction

The corrected capstone product is the **VMVI Annotation Mining and Interaction Explorer**.

Start here:

- `VMVI_ANNOTATION_EXPLORER_README.md`
- `VMVI_ANNOTATION_EXPLORER_PLAN.md`
- `vmvi_explorer/app.py`
- `scripts/mine_vmvi_annotations.py`

The explorer parses official VMVI color-coded `Label400` annotations, identifies all interactions present, ranks them by dominance, generates names such as `passing_being_passed_front_approaching`, supports sorting/filtering, and exports structured metadata.

Run the app:

```bash
/tmp/vmvi_explorer_venv/bin/python -m streamlit run vmvi_explorer/app.py --server.headless true --server.port 8501 --server.address 127.0.0.1
```

Batch-mine all local labels:

```bash
python scripts/mine_vmvi_annotations.py --progress-every 25 --output-dir outputs/annotation_explorer
```

The previous recognition/clustering files are retained as exploratory history.

The recognition work normalizes noisy VMVI interaction labels, trains supervised models on refined `X-V-W` histogram features, and compares the result against the unsupervised clustering baseline.

## Current Recognition Result

- Dataset: aligned 400-image subset
- Inputs: `Label400`, `VTcenter_400`, `gradient`, `angle_mp`
- Point support: `VTcenter_400` centerlines
- Direction signal `v`: decoded from `angle_mp` using `center_128`
- Magnitude/reliability signal: `gradient`
- Magnitude gate: per-image percentile `p85`
- Width `w`: row-wise span of connected VTcenter trajectory/profile components at retained points
- Feature vector: normalized `frequency(x,v)` plus `frequency(w)` histograms
- Label cleanup: 96 raw labels normalized into 7 main recognition categories plus `other`
- Main model: square-root histogram transform + 16-component SVD + Linear SVM
- Cross-validation result: macro-F1 `0.379971`, accuracy `0.417225`
- Holdout result: macro-F1 `0.392286`, accuracy `0.441558`
- Clustering baseline agreement with cleaned labels: ARI `0.049979`, NMI `0.068574`

## Main Report Files

Start here:

- `docs/recognition_report.md`
- `docs/VMVI_recognition_report.pdf`
- `RECOGNITION_MODEL_PLAN.txt`
- `docs/VMVI_final_report.pdf`
- `docs/final_report.md`
- `FINAL_OUTPUTS.md`
- `AGENT_CHECKLIST.md`
- `docs/report_materials.md`
- `docs/decision_log.md`
- `docs/dataset_notes.md`

Main figures and tables are under `docs/assets/` and final baseline plots are under `outputs/`.

## Main Scripts

- `scripts/audit_dataset.py`: dataset inventory and matching
- `scripts/audit_signals.py`: angle and gradient audits
- `scripts/extract_feature_spaces.py`: global `frequency(x,v)` and `frequency(w)` extraction
- `scripts/build_per_image_features.py`: per-image histogram feature vectors
- `scripts/normalize_interaction_labels.py`: raw-label cleanup into recognition categories
- `scripts/train_recognition_model.py`: supervised recognition model sweep and evaluation
- `scripts/analyze_recognition_errors.py`: held-out prediction error analysis
- `scripts/compare_clustering_recognition.py`: clustering baseline comparison against cleaned labels
- `scripts/cluster_per_image_features.py`: PCA and KMeans clustering baseline
- `scripts/interpret_cluster_semantics.py`: post-clustering label interpretation baseline
- `scripts/assemble_report_artifacts.py`: report summary tables and manifest

## Main Result Interpretation

The refined clustering pipeline finds stable structural groups, but those groups do not align strongly with cleaned interaction categories. The supervised recognition pipeline is therefore a better match for the assigned dataset exploration and recognition topic.

The current recognition model is meaningful but not perfect. It beats the majority baseline clearly, while still showing confusion between visually overlapping categories such as `lane_change` and `passing`.

## Archived Work

Earlier project work is retained under `archive/`. It should be treated as historical reference, not as the current baseline.
