"""Streamlit UI for the VMVI Annotation Mining and Interaction Explorer."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd
import plotly.express as px
import streamlit as st

from vmvi_explorer.color_parser import (
    DEFAULT_NAME_THRESHOLD,
    DEFAULT_TOLERANCE,
    build_metadata_frame,
    class_distribution,
    cooccurrence_matrix,
    parse_uploaded_image,
    sort_by_priority,
)
from vmvi_explorer.constants import INTERACTION_BY_CODE, OFFICIAL_CODES


st.set_page_config(
    page_title="VMVI Annotation Explorer",
    page_icon="VMVI",
    layout="wide",
    initial_sidebar_state="expanded",
)


def csv_bytes(df: pd.DataFrame) -> bytes:
    return df.to_csv(index=False).encode("utf-8")


def json_bytes(df: pd.DataFrame) -> bytes:
    return df.to_json(orient="records", indent=2).encode("utf-8")


def code_label(code: str) -> str:
    item = INTERACTION_BY_CODE[code]
    return f"{code} - {item.name}"


def label_to_code(label: str) -> str:
    return label.split(" - ", 1)[0]


def interaction_options(include_off_road: bool = True) -> list[str]:
    return [
        code_label(code)
        for code in OFFICIAL_CODES
        if include_off_road or code != "OR"
    ]


def plot_distribution(distribution: pd.DataFrame):
    if distribution.empty:
        return None
    fig = px.bar(
        distribution,
        x="token",
        y="images_present",
        color="dominant_images",
        hover_data=["code", "interaction", "total_pixels", "mean_fraction"],
        title="Class presence and dominance",
        labels={"token": "interaction", "images_present": "images present", "dominant_images": "dominant images"},
    )
    fig.update_layout(xaxis_tickangle=-35, height=430)
    return fig


def plot_interaction_count(metadata: pd.DataFrame):
    if metadata.empty:
        return None
    fig = px.histogram(
        metadata,
        x="interaction_count",
        nbins=max(1, int(metadata["interaction_count"].max()) + 1),
        title="Interactions per image",
        labels={"interaction_count": "interaction count"},
    )
    fig.update_layout(height=360, bargap=0.1)
    return fig


def plot_cooccurrence(metadata: pd.DataFrame):
    if metadata.empty:
        return None
    matrix = cooccurrence_matrix(metadata)
    fig = px.imshow(
        matrix,
        text_auto=True,
        color_continuous_scale="Greens",
        title="Interaction co-occurrence",
        labels={"x": "interaction", "y": "interaction", "color": "images"},
    )
    fig.update_layout(height=560)
    return fig, matrix


def apply_filters(metadata: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, object]]:
    filtered = metadata.copy()

    with st.sidebar:
        st.header("Filters")
        filename_query = st.text_input("Filename or generated-name search", "")
        tag_options = sorted(filtered["recommended_tag"].unique().tolist()) if not filtered.empty else []
        selected_tags = st.multiselect("Recommended tags", tag_options, default=tag_options)
        dominant_options = [code_label(code) for code in OFFICIAL_CODES if code in set(filtered.get("dominant_code", []))]
        selected_dominant = st.multiselect("Dominant interactions", dominant_options)
        selected_present = st.multiselect("Contains interactions", interaction_options())
        contains_mode = st.radio("Contains match mode", ["ALL selected", "ANY selected"], horizontal=True)
        min_selected_fraction = st.slider("Minimum selected interaction %", 0, 100, 0, step=5)
        selected_excluded = st.multiselect("Exclude interactions", interaction_options())
        min_dominance = st.slider("Minimum dominant %", 0, 100, 0, step=5)
        min_interactions = st.slider("Minimum interaction count", 0, 12, 0)
        max_unknown = st.slider("Maximum unknown %", 0, 100, 100, step=5)

    if filename_query:
        query = filename_query.lower()
        filtered = filtered[
            filtered["original_filename"].str.lower().str.contains(query, regex=False)
            | filtered["auto_name"].str.lower().str.contains(query, regex=False)
        ]
    if selected_tags:
        filtered = filtered[filtered["recommended_tag"].isin(selected_tags)]
    if selected_dominant:
        codes = [label_to_code(label) for label in selected_dominant]
        filtered = filtered[filtered["dominant_code"].isin(codes)]
    if selected_present:
        present_codes = [label_to_code(label) for label in selected_present]
        conditions = []
        for code in present_codes:
            threshold = min_selected_fraction / 100.0
            conditions.append(filtered[f"{code}_fraction"] >= threshold if threshold > 0 else filtered[f"{code}_count"] > 0)
        if conditions:
            mask = conditions[0]
            for condition in conditions[1:]:
                if contains_mode == "ALL selected":
                    mask = mask & condition
                else:
                    mask = mask | condition
            filtered = filtered[mask]
    if selected_excluded:
        for code in [label_to_code(label) for label in selected_excluded]:
            filtered = filtered[filtered[f"{code}_count"] == 0]
    filtered = filtered[filtered["dominant_fraction"] >= min_dominance / 100.0]
    filtered = filtered[filtered["interaction_count"] >= min_interactions]
    filtered = filtered[filtered["unknown_fraction"] <= max_unknown / 100.0]
    context = {
        "present_codes": [label_to_code(label) for label in selected_present],
        "excluded_codes": [label_to_code(label) for label in selected_excluded],
        "dominant_codes": [label_to_code(label) for label in selected_dominant],
        "contains_mode": contains_mode,
        "min_selected_fraction": min_selected_fraction / 100.0,
    }
    return filtered, context


def apply_sort(metadata: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    with st.sidebar:
        st.header("Sorting")
        priority_labels = st.multiselect(
            "Interaction priority order",
            interaction_options(include_off_road=False),
            help="Rows are sorted by the selected interaction percentages in the order chosen.",
        )
        preset = st.selectbox(
            "Sort preset",
            [
                "Priority interaction sort",
                "Dominant strongest first",
                "Most mixed first",
                "Most complex first",
                "Needs review first",
                "Largest annotation first",
            ],
        )

    priority_codes = [label_to_code(label) for label in priority_labels]
    if metadata.empty:
        return metadata, priority_codes
    if preset == "Priority interaction sort" and priority_codes:
        return sort_by_priority(metadata, priority_codes), priority_codes
    if preset == "Dominant strongest first":
        return metadata.sort_values(["dominant_fraction", "official_pixel_count"], ascending=[False, False]).reset_index(drop=True), priority_codes
    if preset == "Most mixed first":
        return metadata.sort_values(["dominant_fraction", "interaction_count"], ascending=[True, False]).reset_index(drop=True), priority_codes
    if preset == "Most complex first":
        return metadata.sort_values(["interaction_count", "dominant_fraction"], ascending=[False, True]).reset_index(drop=True), priority_codes
    if preset == "Needs review first":
        return metadata.sort_values(["unknown_fraction", "unknown_pixel_count"], ascending=[False, False]).reset_index(drop=True), priority_codes
    if preset == "Largest annotation first":
        return metadata.sort_values(["official_pixel_count", "dominant_fraction"], ascending=[False, False]).reset_index(drop=True), priority_codes
    return metadata.sort_values(["dominant_fraction", "official_pixel_count"], ascending=[False, False]).reset_index(drop=True), priority_codes


def process_uploads(uploaded_files, tolerance: float, name_threshold: float):
    progress = st.progress(0, text="Starting annotation parsing")
    status = st.empty()
    parsed = []
    previews = {}
    total = len(uploaded_files)
    for idx, uploaded in enumerate(uploaded_files, start=1):
        status.text(f"Processing {idx}/{total}: {uploaded.name}")
        summary, image = parse_uploaded_image(uploaded, tolerance=tolerance, name_threshold=name_threshold)
        parsed.append(summary)
        previews[summary.sample_id] = image.copy()
        progress.progress(idx / total, text=f"Processed {idx}/{total}")
    status.text(f"Finished processing {total} image(s)")
    return parsed, previews


def selected_fraction_columns(filter_context: dict[str, object], priority_codes: list[str]) -> list[str]:
    selected_codes = []
    for key in ["present_codes", "dominant_codes"]:
        selected_codes.extend(filter_context.get(key, []))
    selected_codes.extend(priority_codes)

    columns = []
    seen = set()
    for code in selected_codes:
        column = f"{code}_fraction"
        if code not in seen and column not in seen:
            columns.append(column)
            seen.add(code)
            seen.add(column)
    return columns


def clear_uploaded_images() -> None:
    st.session_state.metadata = pd.DataFrame()
    st.session_state.previews = {}
    st.session_state.upload_widget_version = st.session_state.get("upload_widget_version", 0) + 1
    st.session_state.pop("selected_image_option", None)


def render_inspector(metadata: pd.DataFrame, previews: dict):
    st.subheader("Image Inspector")
    if metadata.empty:
        st.info("No rows match the current filters.")
        return

    options = [
        f"{row.auto_name} | {row.original_filename}"
        for row in metadata[["auto_name", "original_filename"]].itertuples(index=False)
    ]
    selected = st.selectbox("Select image", options, key="selected_image_option")
    selected_index = options.index(selected)
    row = metadata.iloc[selected_index]

    left, right = st.columns([1.15, 1])
    with left:
        image = previews.get(row["sample_id"])
        if image is not None:
            st.image(image, caption=row["original_filename"], width="stretch")
        else:
            st.warning("Image preview is not available for this row.")

    with right:
        st.markdown(f"**Generated name:** `{row['auto_name']}`")
        st.markdown(f"**Dominant interaction:** `{row['dominant_token']}` ({row['dominant_fraction']:.1%})")
        st.markdown(f"**Recommended tag:** `{row['recommended_tag']}`")
        st.markdown(f"**Interactions present:** `{int(row['interaction_count'])}`")
        st.markdown(f"**Unknown color fraction:** `{row['unknown_fraction']:.2%}`")

        detail_rows = []
        for code in OFFICIAL_CODES:
            count = int(row[f"{code}_count"])
            if count <= 0:
                continue
            item = INTERACTION_BY_CODE[code]
            detail_rows.append(
                {
                    "code": code,
                    "interaction": item.name,
                    "token": item.token,
                    "pixels": count,
                    "percent": float(row[f"{code}_fraction"]),
                }
            )
        detail_df = pd.DataFrame(detail_rows).sort_values("percent", ascending=False)
        st.dataframe(
            detail_df.assign(percent=lambda df: (df["percent"] * 100).round(2)),
            width="stretch",
            hide_index=True,
        )
        if not detail_df.empty:
            fig = px.bar(
                detail_df,
                x="token",
                y="percent",
                title="Interaction dominance",
                labels={"token": "interaction", "percent": "fraction"},
            )
            fig.update_layout(height=320, xaxis_tickangle=-30)
            st.plotly_chart(fig, width="stretch")


def main() -> None:
    st.title("VMVI Annotation Mining and Interaction Explorer")
    st.caption("Parse official color-coded Label400 annotations into meaningful interaction metadata.")

    with st.sidebar:
        st.header("Parser Settings")
        tolerance = st.slider("RGB tolerance", 0, 80, int(DEFAULT_TOLERANCE), step=5)
        name_threshold_percent = st.slider("Name threshold %", 0, 25, int(DEFAULT_NAME_THRESHOLD * 100), step=1)
        name_threshold = name_threshold_percent / 100.0

    if "metadata" not in st.session_state:
        st.session_state.metadata = pd.DataFrame()
        st.session_state.previews = {}
    if "upload_widget_version" not in st.session_state:
        st.session_state.upload_widget_version = 0

    upload_key = f"label400_uploads_{st.session_state.upload_widget_version}"
    uploaded_files = st.file_uploader(
        "Drag and drop Label400 PNG images",
        type=["png"],
        accept_multiple_files=True,
        help="Upload one or more VMVI Label400 annotation images.",
        key=upload_key,
    )

    action_left, action_right = st.columns([1, 1])
    with action_left:
        process_clicked = st.button("Process uploaded images", type="primary", disabled=not uploaded_files)
    with action_right:
        clear_disabled = not uploaded_files and st.session_state.metadata.empty
        clear_clicked = st.button("Clear all images", disabled=clear_disabled)
    if clear_clicked:
        clear_uploaded_images()
        st.rerun()

    if process_clicked and uploaded_files:
        parsed, previews = process_uploads(uploaded_files, tolerance=float(tolerance), name_threshold=float(name_threshold))
        st.session_state.metadata = build_metadata_frame(parsed)
        st.session_state.previews = previews

    metadata = st.session_state.metadata
    previews = st.session_state.previews

    if metadata.empty:
        st.info("Upload Label400 PNG images to begin. The tool will generate interaction names and dominance summaries from official colors.")
        return

    filtered, filter_context = apply_filters(metadata)
    sorted_df, priority_codes = apply_sort(filtered)

    st.subheader("Dataset Summary")
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Images", len(sorted_df))
    c2.metric("Clean", int((sorted_df["recommended_tag"] == "clean_training_candidate").sum()))
    c3.metric("Mixed/complex", int(sorted_df["recommended_tag"].isin(["mixed_scene", "complex_scene"]).sum()))
    c4.metric("Needs review", int((sorted_df["recommended_tag"] == "needs_review").sum()))
    c5.metric("Avg interactions", f"{sorted_df['interaction_count'].mean():.2f}" if len(sorted_df) else "0")

    st.subheader("Results Table")
    table_columns = [
        "auto_name",
        "original_filename",
        "dominant_token",
        "dominant_fraction",
        "interaction_count",
        "unknown_fraction",
        "recommended_tag",
        "official_pixel_count",
    ]
    for column in selected_fraction_columns(filter_context, priority_codes):
        if column in sorted_df.columns and column not in table_columns:
            table_columns.insert(-3, column)
    display_df = sorted_df[table_columns].copy()
    for column in [column for column in display_df.columns if column.endswith("_fraction")]:
        display_df[column] = (display_df[column] * 100).round(2)
    st.dataframe(display_df, width="stretch", hide_index=True)

    st.subheader("Charts")
    dist = class_distribution(sorted_df)
    chart_left, chart_right = st.columns(2)
    with chart_left:
        fig = plot_distribution(dist)
        if fig:
            st.plotly_chart(fig, width="stretch")
    with chart_right:
        fig = plot_interaction_count(sorted_df)
        if fig:
            st.plotly_chart(fig, width="stretch")

    cooccur_fig, cooccur_df = plot_cooccurrence(sorted_df)
    st.plotly_chart(cooccur_fig, width="stretch")

    render_inspector(sorted_df, previews)

    st.subheader("Exports")
    e1, e2, e3, e4 = st.columns(4)
    with e1:
        st.download_button("Download metadata CSV", csv_bytes(sorted_df), "annotation_metadata.csv", "text/csv")
    with e2:
        st.download_button("Download metadata JSON", json_bytes(sorted_df), "annotation_metadata.json", "application/json")
    with e3:
        st.download_button("Download class distribution", csv_bytes(dist), "class_distribution.csv", "text/csv")
    with e4:
        st.download_button("Download co-occurrence CSV", cooccur_df.to_csv().encode("utf-8"), "cooccurrence_matrix.csv", "text/csv")

    with st.expander("Raw metadata JSON preview"):
        st.code(json.dumps(sorted_df.head(5).to_dict(orient="records"), indent=2), language="json")


if __name__ == "__main__":
    main()
