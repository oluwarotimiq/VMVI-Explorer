# VMVI Annotation Mining and Interaction Explorer

This is the finished browser-based tool for the corrected capstone direction.

The app reads VMVI `Label400` annotation images, parses the official color-coded interaction labels, identifies all interactions present, ranks them by dominance, auto-generates meaningful names, supports sorting/filtering, shows charts and image-level details, and exports structured metadata.

## Run The App

Use the Linux-side virtual environment created during setup:

```bash
/tmp/vmvi_explorer_venv/bin/python -m streamlit run vmvi_explorer/app.py --server.headless true --server.port 8501 --server.address 127.0.0.1
```

Then open:

```text
http://127.0.0.1:8501
```

For hosted deployment instructions, see:

```text
DEPLOYMENT.md
```

If you need to recreate the environment:

```bash
python -m venv /tmp/vmvi_explorer_venv
/tmp/vmvi_explorer_venv/bin/python -m pip install --upgrade pip
/tmp/vmvi_explorer_venv/bin/python -m pip install -r requirements.txt
```

## Batch-Mine The Local Dataset

Process all local `data/Label400` images and write reproducible outputs:

```bash
python scripts/mine_vmvi_annotations.py --progress-every 25 --output-dir outputs/annotation_explorer
```

Main outputs:

```text
outputs/annotation_explorer/annotation_metadata.csv
outputs/annotation_explorer/annotation_metadata.json
outputs/annotation_explorer/class_distribution.csv
outputs/annotation_explorer/cooccurrence_matrix.csv
outputs/annotation_explorer/clean_samples.csv
outputs/annotation_explorer/mixed_samples.csv
outputs/annotation_explorer/unknown_color_report.csv
outputs/annotation_explorer/processing_summary.json
```

## Verify It Works

Run the parser and app smoke checks:

```bash
python -m py_compile vmvi_explorer/*.py scripts/mine_vmvi_annotations.py
/tmp/vmvi_explorer_venv/bin/python scripts/smoke_test_annotation_explorer.py
curl -I http://127.0.0.1:8501
```

Expected smoke-test result:

```text
VMVI Annotation Explorer smoke test passed
```

## What The App Does

For every uploaded `Label400` image, the app computes:

- official interactions present,
- pixel count per interaction,
- percentage per interaction,
- dominant interaction,
- interaction count,
- exact/approximate/unknown color counts,
- recommended sample tag,
- generated name in dominance order.

Generated names follow this rule:

```text
interaction1_interaction2_interaction3
```

Example:

```text
passing_being_passed_front_approaching
```

This means the top interactions by dominance are:

```text
1. passing
2. being_passed
3. front_approaching
```

## Useful UI Features

- Drag and drop multiple `Label400` PNG images.
- Adjust RGB tolerance and naming threshold.
- Filter by dominant interaction, interaction presence, interaction exclusion, tag, dominance percentage, selected-class percentage, interaction count, unknown percentage, filename, or generated name.
- Use `ALL selected` or `ANY selected` matching for category filters.
- Sort by selected interaction priority.
- Use presets for strongest dominant, most mixed, most complex, needs review, and largest annotation.
- Inspect an image with its generated name, dominant interaction, interaction table, and dominance chart.
- Download metadata CSV/JSON, class distribution, and co-occurrence matrix.

## Category Filtering

The category filters are designed for practical dataset review.

Examples:

```text
Contains interactions: PS - Passing, O - Oncoming
Contains match mode: ALL selected
Minimum selected interaction %: 10
```

This finds images where both passing and oncoming are meaningful.

```text
Contains interactions: M - Merging / approaching, C - Crossing
Contains match mode: ANY selected
Minimum selected interaction %: 10
```

This finds images where either merging or crossing is meaningful.

```text
Exclude interactions: OR - Off-road / irrelevant
```

This removes samples containing off-road annotation pixels.

When category filters or priority sorting are active, the results table adds the selected category percentage columns so the sort/filter reason is visible.

## Current Full-Dataset Findings

The optimized parser processed 400 local images in about 48 seconds.

Summary from `outputs/annotation_explorer`:

- Samples processed: 400
- Clean training candidates: 27
- Mixed/complex samples: 262
- Needs-review samples: 110
- Most common dominant class: `being_passed`

Top dominant classes:

```text
being_passed: 166
passing: 96
oncoming: 75
crossing: 26
parallel: 17
following: 10
```

This supports the project claim that VMVI images are often multi-interaction scenes, and filenames are not enough to describe the annotation content.
