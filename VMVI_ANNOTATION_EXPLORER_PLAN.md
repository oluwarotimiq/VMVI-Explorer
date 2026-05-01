# VMVI Annotation Mining and Interaction Explorer Plan

## Project Goal

Build a classical, non-deep-learning data mining and exploration tool for VMVI.

The tool will let a user drag and drop VMVI `Label400` annotation images into a browser-based UI. It will parse the official color-coded vehicle interaction labels, identify all interactions present, rank them by dominance, automatically generate meaningful names, support useful sorting and filtering, show per-image details, and export structured metadata for future recognition work.

This project does not relabel the dataset manually and does not use deep learning. It converts the dataset's existing color-coded annotations into searchable, sortable, analyzable data.

## Final Project Statement

This project builds a VMVI annotation mining and interaction explorer that reads official color-coded vehicle interaction labels, identifies and ranks interactions by dominance, automatically names samples as `interaction1_interaction2_interaction3`, supports sorting and filtering by interaction content, displays annotation summaries in a browser UI, and exports structured metadata for dataset exploration and future classical recognition experiments.

## Why This Matters

The VMVI dataset is hand-labeled, but the labels are stored visually as colors in annotation images. That makes the dataset difficult to search, sort, summarize, and use directly.

The filenames are not sufficient labels. A file named `approaching` may contain several official interactions such as passing, being passed, following, oncoming, and front approaching. The official labels are the colors inside the `Label400` image, not the filename.

This tool matters because it turns:

```text
color-coded annotation images
```

into:

```text
structured interaction metadata
dominance scores
auto-generated names
class distribution tables
co-occurrence summaries
clean/mixed scene tags
CSV/JSON exports
```

This makes VMVI easier to understand, audit, curate, and prepare for recognition experiments.

## Core Scope For An A+ Project

The essential build is:

1. Official VMVI color parser.
2. Drag-and-drop browser UI for `Label400` images.
3. Per-image interaction extraction.
4. Dominance-based automatic naming.
5. Priority sorting by selected interaction order.
6. Filtering and useful preset views.
7. Dataset-level summaries.
8. Side-by-side per-image inspection within the app.
9. CSV/JSON export.
10. Report explaining findings, limitations, and significance.

The classifier is not the centerpiece. A classical recognition baseline can be added later if time allows, but the strongest contribution is the annotation mining and exploration tool.

## Explicit Non-Goals

The project will not:

- use deep learning,
- train a CNN, RNN, LSTM, Transformer, or neural network,
- claim to discover new interaction classes,
- claim to replace human annotations,
- treat filenames as ground-truth labels,
- overclaim that autonomous driving recognition is solved.

The project will:

- use deterministic color parsing,
- use official VMVI color codes,
- produce structured dataset metadata,
- expose multi-interaction structure,
- support useful visual inspection and export.

## Official Interaction Color Table

The parser will use the official VMVI interaction colors from the dataset document.

| Code | Token | Interaction Meaning | RGB |
|---|---|---|---|
| `CI` | `cut_in` | Cut-in from next lane to driving lane | `(255, 140, 0)` |
| `CL` | `lane_changing` | Lane-changing to driving lane | `(255, 165, 0)` |
| `FA` | `front_approaching` | Front vehicle approaching/slowing | `(255, 0, 0)` |
| `FL` | `front_leaving` | Front vehicle leaving/speeding up | `(240, 128, 128)` |
| `FF` | `following` | Following front vehicle | `(255, 99, 71)` |
| `PN` | `parallel` | Parallel vehicle on adjacent lane | `(255, 255, 0)` |
| `PS` | `passing` | Passing faster than ego vehicle | `(255, 215, 0)` |
| `PD` | `being_passed` | Being passed / slower adjacent vehicle | `(218, 165, 32)` |
| `M` | `merging` | Merging or approaching from ramp/crossing/T-junction | `(60, 179, 113)` |
| `O` | `oncoming` | Oncoming/opposite-lane vehicle | `(128, 0, 128)` |
| `C` | `crossing` | Crossing vehicle | `(0, 0, 255)` |
| `TW` | `turning_away` | Turning away from driving lane | `(0, 255, 255)` |
| `OR` | `off_road` | Off-road / irrelevant vehicle space | `(255, 255, 255)` |
| `BG` | `background` | Background/no vehicle | `(0, 0, 0)` |

The parser should also track unknown colors, including any high-frequency colors not in the official table. Some images contain near-colors caused by anti-aliasing or image processing, so the parser must support exact matching plus tolerance-based matching.

## Main User Story

1. User opens the local browser app.
2. User drags one or more `Label400` images into the upload area.
3. The app processes the images with a progress bar.
4. The app generates a results table.
5. User sorts by interaction dominance or selected interaction priority.
6. User clicks an image to inspect details.
7. User exports CSV/JSON summaries.

Example:

```text
Input:
approaching 1_g_refined_add.png

Detected interactions:
PS passing = 38.2%
PD being_passed = 23.6%
FA front_approaching = 9.9%
FL front_leaving = 8.3%
O oncoming = 7.8%
FF following = 7.8%

Generated name:
passing_being_passed_front_approaching

Tag:
mixed_scene
```

## Automatic Naming Rule

Generated names must immediately mean something.

Name format:

```text
interaction1_interaction2_interaction3
```

Rules:

1. Ignore `BG/background`.
2. Optionally exclude `OR/off_road` from the name unless it is dominant.
3. Sort official interactions by percentage of annotated pixels.
4. Keep up to the top 3 interactions.
5. Include only interactions above the minimum name threshold.
6. If no interaction passes the threshold, include the dominant non-background interaction.
7. Join tokens with underscores.

Recommended threshold:

```text
5% of annotated official pixels
```

Examples:

```text
passing_being_passed_front_approaching
crossing_turning_away_passing
merging_parallel_being_passed
lane_changing_following
passing
```

The table should store supporting fields separately:

```text
dominant_code
dominant_token
dominant_fraction
interaction_count
recommended_tag
unknown_fraction
```

Do not overload the generated name with every detail.

## Per-Image Outputs

For every image, produce one structured row with:

```text
sample_id
original_filename
auto_name
dominant_code
dominant_token
dominant_fraction
interaction_count
official_pixel_count
background_pixel_count
unknown_pixel_count
unknown_fraction
exact_match_pixel_count
approx_match_pixel_count
recommended_tag
CI_count
CI_fraction
CL_count
CL_fraction
FA_count
FA_fraction
FL_count
FL_fraction
FF_count
FF_fraction
PN_count
PN_fraction
PS_count
PS_fraction
PD_count
PD_fraction
M_count
M_fraction
O_count
O_fraction
C_count
C_fraction
TW_count
TW_fraction
OR_count
OR_fraction
```

## Recommended Tags

Each sample should receive a simple tag to support dataset curation.

| Tag | Rule | Meaning |
|---|---|---|
| `clean_training_candidate` | dominant fraction >= 70%, interaction count <= 2, unknown fraction <= 5% | Strong single-dominant sample |
| `mixed_scene` | dominant fraction < 70% and interaction count >= 2 | Multiple meaningful interactions |
| `complex_scene` | interaction count >= 4 | Many interactions present |
| `needs_review` | unknown fraction > 5% | Possible color/artifact issue |
| `sparse_annotation` | official pixel count is very low | Very little usable annotation |
| `off_road_dominant` | `OR` is dominant | Mostly irrelevant/off-road annotation |

If multiple tags apply, use the most important in this order:

```text
needs_review
sparse_annotation
off_road_dominant
complex_scene
mixed_scene
clean_training_candidate
```

## Sorting Requirements

The sort must be immediately useful.

### Priority Interaction Sort

The user selects a priority list:

```text
1. Merging
2. Crossing
3. Passing
```

The app sorts by:

```text
M_fraction desc
C_fraction desc
PS_fraction desc
dominant_fraction desc
official_pixel_count desc
```

This surfaces the strongest examples of the user's chosen interactions.

### Sort Presets

The app should also include sort presets:

| Preset | Sort Logic | Purpose |
|---|---|---|
| `Dominant strongest first` | `dominant_fraction desc` | Find clean examples |
| `Most mixed first` | `dominant_fraction asc`, `interaction_count desc` | Find ambiguous/mixed samples |
| `Most complex first` | `interaction_count desc` | Find multi-interaction scenes |
| `Needs review first` | `unknown_fraction desc` | Find color/artifact issues |
| `Largest annotation first` | `official_pixel_count desc` | Find dense annotations |
| `Rare class examples` | sort by selected rare class fraction | Inspect underrepresented classes |

## Filtering Requirements

The user should be able to filter by:

```text
dominant interaction
interaction present anywhere
minimum dominance percentage
minimum interaction count
maximum unknown fraction
recommended tag
filename search
auto-name search
```

Examples:

```text
show only samples containing crossing
show only samples where merging is dominant
show only samples with at least 4 interactions
show samples where dominant fraction > 70%
show needs_review samples
show clean_training_candidate samples
```

## GUI Requirements

Recommended stack:

```text
Python + Streamlit + Pillow + NumPy + pandas + Plotly
```

The app should have these sections.

### 1. Upload Panel

Features:

- drag/drop `Label400` images,
- accept multiple files,
- show file count,
- process button,
- progress bar,
- processing status text,
- cancellation can be future work.

### 2. Summary Dashboard

Show:

- total images processed,
- total official annotation pixels,
- total unknown pixels,
- number of dominant classes found,
- number of clean/mixed/complex/needs-review samples,
- top dominant interaction,
- average interaction count per image.

### 3. Results Table

Columns:

```text
auto_name
original_filename
dominant_token
dominant_fraction
interaction_count
unknown_fraction
recommended_tag
official_pixel_count
```

The table should update after filtering and sorting.

### 4. Interaction Priority Sort Control

Controls:

- multiselect for interaction priority,
- preset selector,
- ascending/descending toggle only if needed,
- reset sort button.

For the first version, `st.multiselect` is enough. The selected order from the multiselect becomes the priority order.

### 5. Image Inspector

When a row is selected, show:

- image preview,
- original filename,
- generated name,
- dominant interaction,
- recommended tag,
- interaction breakdown table,
- bar chart of interaction percentages,
- exact/approx/unknown color counts.

### 6. Dataset Charts

Charts:

- dominant class distribution,
- class presence distribution,
- interaction count histogram,
- co-occurrence heatmap,
- unknown color distribution.

### 7. Export Panel

Downloads:

```text
annotation_metadata.csv
annotation_metadata.json
class_distribution.csv
cooccurrence_matrix.csv
clean_samples.csv
mixed_samples.csv
unknown_color_report.csv
```

## Side-by-Side Aligned File Viewer

This is useful but should be Phase 2.

Phase 1 only requires uploaded `Label400` images.

Phase 2 can add folder upload or local folder selection for:

```text
Label400
VTcenter_400
gradient
angle_mp
MPTV800/AutomaticLabelSource800
```

Then the tool can show:

```text
Label400 | VTcenter_400 | gradient | angle_mp | width/profile
```

This requires filename canonicalization, which already exists in earlier scripts and can be adapted later.

## Parser Design

Create a reusable parser module:

```text
vmvi_explorer/color_parser.py
```

Core functions:

```python
parse_label_image(image, filename) -> ImageAnnotationSummary
count_exact_colors(rgb_array) -> dict
match_nearest_official_colors(rgb_array, tolerance) -> dict
generate_auto_name(class_fractions) -> str
assign_recommended_tag(summary) -> str
build_metadata_frame(summaries) -> pandas.DataFrame
build_cooccurrence_matrix(metadata) -> pandas.DataFrame
```

Use dataclasses for internal clarity:

```python
InteractionClass
ImageAnnotationSummary
```

## Color Matching Strategy

Use a two-stage strategy for speed and correctness.

### Stage 1: Exact Matching

Count exact RGB values in the image.

Fast approach:

```python
colors, counts = np.unique(image.reshape(-1, 3), axis=0, return_counts=True)
```

Map exact official colors directly.

### Stage 2: Tolerance Matching

Only process non-background colors that are not exact official colors.

For each unknown color:

1. Compute RGB distance to official colors.
2. Match to nearest official color if distance <= tolerance.
3. Otherwise mark as unknown.

Recommended initial tolerance:

```text
30 RGB Euclidean distance
```

The app should expose this as an advanced setting.

### Performance Note

Each image is roughly:

```text
2592 x 1800 = 4,665,600 pixels
```

For 400 images:

```text
about 1.87 billion pixels
```

Therefore:

- process images one at a time,
- show progress,
- cache per-file results,
- avoid pixel-by-pixel Python loops,
- use NumPy vectorized operations.

## Output Files

Default output directory:

```text
outputs/annotation_explorer/
```

Files:

```text
annotation_metadata.csv
annotation_metadata.json
class_distribution.csv
dominant_class_distribution.csv
class_presence_distribution.csv
cooccurrence_matrix.csv
clean_samples.csv
mixed_samples.csv
unknown_color_report.csv
processing_summary.json
```

## Implementation Structure

Recommended file layout:

```text
vmvi_explorer/
  __init__.py
  app.py
  constants.py
  color_parser.py
  summaries.py
  sorting.py
  exports.py
scripts/
  run_annotation_explorer.py
outputs/
  annotation_explorer/
```

`app.py` should be the Streamlit entry point.

Run command:

```bash
streamlit run vmvi_explorer/app.py
```

Alternative run command:

```bash
python -m streamlit run vmvi_explorer/app.py
```

## Tool And Dependency Availability Check

Environment checked on the current workspace.

### Already Available

| Tool / Package | Status | Notes |
|---|---|---|
| Python | available | `Python 3.12.3` |
| pip | available | `pip 24.0` |
| Pillow / PIL | available | image loading and preview |
| NumPy | available | vectorized color counting |
| pandas | available | metadata tables and exports |
| matplotlib | available | fallback plotting |
| scikit-learn | available | optional classical recognition baseline |
| SciPy | available | optional image/statistical utilities |
| pypdf | available | report verification |
| reportlab | available | PDF generation |

### Needed But Not Currently Installed

| Tool / Package | Current Status | Availability Search Result | Action |
|---|---|---|---|
| Streamlit | not installed | available on PyPI, latest seen `1.57.0` | add to requirements and install before GUI work |
| Plotly | not installed | available on PyPI, latest seen `6.7.0` | add to requirements and install before GUI work |

### Required Install Command

Before building/running the GUI:

```bash
python -m pip install streamlit plotly
```

Recommended pinned additions to requirements:

```text
streamlit>=1.57.0
plotly>=6.7.0
```

If Streamlit installation becomes blocked, fallback is a simple local static HTML/JavaScript viewer plus Python-generated CSV files. That fallback is less clean and should only be used if Streamlit cannot be installed.

## Data Availability Check

Local dataset folders exist:

```text
data/Label400
data/VTcenter_400
data/gradient
data/angle_mp
data/MPTV800/AutomaticLabelSource800
```

Phase 1 only requires:

```text
data/Label400
```

Phase 2 side-by-side aligned viewing can use the other directories.

## Build Phases

### Phase 1: Parser Core

Deliverables:

- official color table constants,
- exact color parser,
- tolerance matching,
- auto-name generator,
- recommended tag logic,
- unit/sample tests on a few images,
- CSV metadata export.

Success criteria:

- parser identifies official classes in sample images,
- auto-names are dominance ordered,
- unknown colors are reported,
- results are reproducible.

### Phase 2: Batch Dataset Mining

Deliverables:

- process all `Label400` images from local folder,
- progress tracking,
- class distribution,
- dominant class distribution,
- co-occurrence matrix,
- clean/mixed/needs-review exports.

Success criteria:

- all 400 images process without crashing,
- output tables are generated,
- multi-interaction structure is quantified.

### Phase 3: Streamlit UI

Deliverables:

- drag/drop upload,
- batch process progress bar,
- results table,
- priority sort,
- filters,
- image inspector,
- charts,
- downloads.

Success criteria:

- user can drag/drop images and get meaningful names/details,
- table sorting and filtering works,
- exported CSV matches displayed results.

### Phase 4: Side-by-Side Viewer

Deliverables:

- optional local folder matching,
- display aligned `Label400`, `VTcenter_400`, `gradient`, `angle_mp`, and width/profile images,
- show computed details alongside aligned views.

Success criteria:

- selected sample shows aligned images when paths are available,
- missing aligned files are handled gracefully.

### Phase 5: Report And Presentation

Deliverables:

- report section explaining why filenames are not labels,
- color parser method,
- dataset findings,
- screenshots of GUI,
- class distribution chart,
- co-occurrence heatmap,
- auto-naming examples,
- sort/filter examples,
- limitations and future work.

Success criteria:

- layperson can understand the tool,
- technical reviewer can verify the method,
- project is clearly non-deep-learning data mining/exploration.

## Validation Plan

Validate with:

1. Manual inspection of 5 to 10 images.
2. Compare visible dominant colors to parser output.
3. Confirm generated names follow dominance order.
4. Confirm `BG/background` is ignored in naming.
5. Confirm unknown colors are reported.
6. Confirm tolerance matching does not swallow real unknowns too aggressively.
7. Confirm exported CSV rows equal UI rows.
8. Confirm sorting by selected priority produces expected order.

## Risk Register

| Risk | Impact | Mitigation |
|---|---|---|
| Near-colors from anti-aliasing | exact matching misses annotation pixels | use tolerance matching and unknown report |
| Unknown high-frequency color such as gray | may represent undocumented annotation class | report separately; do not silently map |
| Large image batches are slow | poor UX | progress bar, caching, vectorized NumPy |
| Browser upload memory limits | large batch may be heavy | allow local-folder batch script as alternate |
| GUI becomes the whole project | weak capstone framing | emphasize data mining outputs and exports |
| Auto names become too long | hard to read | top 3 interactions only |
| Dominant-class view oversimplifies multi-interaction scenes | misleading conclusion | keep all interactions and co-occurrence metrics |

## Presentation Story

Use this 20-minute story:

1. VMVI labels are official colors inside images.
2. Filenames are not enough because images can contain multiple interactions.
3. The project mines those colors into structured interaction data.
4. The tool auto-generates names by interaction dominance.
5. The tool sorts/filter samples by actual annotation content.
6. The tool reveals class frequency, dominance, and co-occurrence.
7. The GUI makes the dataset inspectable by a non-expert.
8. The exported metadata prepares the dataset for future classical recognition.

## Final A+ Claim

This project does not invent a new AI model. Its contribution is a useful, reproducible VMVI annotation mining system. It reads the dataset's official color-coded labels, exposes the true interaction content of each sample, automatically names samples by dominant interactions, enables practical sorting/filtering, identifies clean and mixed scenes, and exports structured metadata for future recognition and dataset analysis.

