# VMVI Annotation Explorer Results Summary

This summary records the results from the completed batch mining run:

```bash
python scripts/mine_vmvi_annotations.py --progress-every 25 --output-dir outputs/annotation_explorer
```

## Processing Result

- Images processed: 400
- Runtime: about 48 seconds after parser optimization
- Output directory: `outputs/annotation_explorer`
- Main metadata file: `outputs/annotation_explorer/annotation_metadata.csv`

## Sample Tags

| Tag | Count | Meaning |
|---|---:|---|
| `complex_scene` | 172 | Four or more meaningful interactions |
| `needs_review` | 110 | Unknown color fraction above threshold |
| `mixed_scene` | 90 | Multiple meaningful interactions, no clean dominant class |
| `clean_training_candidate` | 27 | Strong dominant interaction, low ambiguity |
| `off_road_dominant` | 1 | Off-road annotation is dominant |

## Dominant Interactions

| Dominant interaction | Count |
|---|---:|
| `being_passed` | 166 |
| `passing` | 96 |
| `oncoming` | 75 |
| `crossing` | 26 |
| `parallel` | 17 |
| `following` | 10 |
| `turning_away` | 5 |
| `off_road` | 3 |
| `front_approaching` | 1 |
| `front_leaving` | 1 |

## Dataset Structure Findings

- Average meaningful interaction count per image: `4.035`
- Median dominant interaction fraction: `0.473109`
- Images with unknown color fraction above 5%: `110`
- Clean single-dominant candidates are a minority: `27 / 400`

These findings support the project claim that VMVI `Label400` images are often multi-interaction scenes. A filename or single class label is not enough to describe the true annotation content.

## Frequent Auto-Generated Names

| Auto name | Count |
|---|---:|
| `being_passed_oncoming_passing` | 23 |
| `being_passed_passing_following` | 16 |
| `being_passed_oncoming` | 15 |
| `being_passed_passing_oncoming` | 15 |
| `passing_oncoming_being_passed` | 12 |
| `passing_being_passed_oncoming` | 12 |
| `being_passed_passing_parallel` | 10 |
| `passing_being_passed_parallel` | 9 |
| `being_passed_parallel_oncoming` | 8 |
| `being_passed_oncoming_following` | 8 |

## Validation Evidence

Completed checks:

- Python compile check passed for explorer modules and scripts.
- Batch miner processed all 400 `Label400` images.
- Streamlit app HTTP check returned `200 OK` at `http://127.0.0.1:8501`.
- Streamlit smoke test uploaded three real `Label400` images and rendered:
  - summary metrics,
  - results table,
  - charts section,
  - image inspector,
  - exports section.
- Auto-name check passed for `approaching 1_g_refined_add.png`:

```text
passing_being_passed_front_approaching
```

- Priority-sort check passed for the selected order:

```text
Merging > Crossing > Passing
```

## Main Product Claim

The finished tool converts VMVI's official color-coded annotations into structured, searchable, sortable, exportable interaction metadata. It directly addresses the dataset usability problem: the true labels are inside the annotation colors, not reliably captured by filenames.

