"""Parse official VMVI color-coded interaction annotations."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO

import numpy as np
import pandas as pd
from PIL import Image

from .constants import (
    INTERACTION_BY_CODE,
    INTERACTION_BY_RGB,
    INTERACTION_CODES,
    INTERACTIONS,
    NAMEABLE_CODES,
    OFFICIAL_CODES,
)


DEFAULT_TOLERANCE = 30.0
DEFAULT_NAME_THRESHOLD = 0.05
DEFAULT_MIN_OFFICIAL_PIXELS = 1000


@dataclass
class ParsedAnnotation:
    sample_id: str
    original_filename: str
    width: int
    height: int
    total_pixels: int
    counts: dict[str, int]
    exact_counts: dict[str, int]
    approx_counts: dict[str, int]
    unknown_pixel_count: int
    unknown_colors: list[dict[str, object]] = field(default_factory=list)
    tolerance: float = DEFAULT_TOLERANCE
    name_threshold: float = DEFAULT_NAME_THRESHOLD

    @property
    def background_pixel_count(self) -> int:
        return self.counts.get("BG", 0)

    @property
    def official_pixel_count(self) -> int:
        return sum(self.counts.get(code, 0) for code in OFFICIAL_CODES)

    @property
    def exact_match_pixel_count(self) -> int:
        return sum(self.exact_counts.values())

    @property
    def approx_match_pixel_count(self) -> int:
        return sum(self.approx_counts.values())

    @property
    def denominator(self) -> int:
        return max(1, self.official_pixel_count)

    @property
    def fractions(self) -> dict[str, float]:
        return {code: self.counts.get(code, 0) / self.denominator for code in INTERACTION_CODES}

    @property
    def present_codes(self) -> list[str]:
        return [code for code in OFFICIAL_CODES if self.counts.get(code, 0) > 0]

    @property
    def interaction_count(self) -> int:
        return sum(1 for code in OFFICIAL_CODES if self.counts.get(code, 0) / self.denominator >= self.name_threshold)

    @property
    def dominant_code(self) -> str:
        present = [(code, self.counts.get(code, 0)) for code in OFFICIAL_CODES]
        present.sort(key=lambda item: item[1], reverse=True)
        return present[0][0] if present and present[0][1] > 0 else "none"

    @property
    def dominant_fraction(self) -> float:
        code = self.dominant_code
        if code == "none":
            return 0.0
        return self.counts.get(code, 0) / self.denominator

    @property
    def unknown_fraction(self) -> float:
        annotated = self.official_pixel_count + self.unknown_pixel_count
        return self.unknown_pixel_count / max(1, annotated)

    @property
    def auto_name(self) -> str:
        candidates = []
        for code in NAMEABLE_CODES:
            fraction = self.counts.get(code, 0) / self.denominator
            if fraction >= self.name_threshold:
                candidates.append((code, fraction, self.counts.get(code, 0)))
        candidates.sort(key=lambda item: (item[1], item[2]), reverse=True)
        if not candidates and self.dominant_code in NAMEABLE_CODES:
            candidates = [(self.dominant_code, self.dominant_fraction, self.counts.get(self.dominant_code, 0))]
        if not candidates:
            return "no_official_interaction"
        return "_".join(INTERACTION_BY_CODE[code].token for code, _, _ in candidates[:3])

    @property
    def recommended_tag(self) -> str:
        if self.unknown_fraction > 0.05:
            return "needs_review"
        if self.official_pixel_count < DEFAULT_MIN_OFFICIAL_PIXELS:
            return "sparse_annotation"
        if self.dominant_code == "OR":
            return "off_road_dominant"
        if self.interaction_count >= 4:
            return "complex_scene"
        if self.dominant_fraction < 0.70 and self.interaction_count >= 2:
            return "mixed_scene"
        if self.dominant_fraction >= 0.70 and self.interaction_count <= 2:
            return "clean_training_candidate"
        return "mixed_scene"

    def to_row(self) -> dict[str, object]:
        dominant = INTERACTION_BY_CODE.get(self.dominant_code)
        row: dict[str, object] = {
            "sample_id": self.sample_id,
            "original_filename": self.original_filename,
            "auto_name": self.auto_name,
            "dominant_code": self.dominant_code,
            "dominant_token": dominant.token if dominant else "none",
            "dominant_name": dominant.name if dominant else "none",
            "dominant_fraction": round(self.dominant_fraction, 6),
            "interaction_count": self.interaction_count,
            "recommended_tag": self.recommended_tag,
            "width": self.width,
            "height": self.height,
            "total_pixels": self.total_pixels,
            "official_pixel_count": self.official_pixel_count,
            "background_pixel_count": self.background_pixel_count,
            "unknown_pixel_count": self.unknown_pixel_count,
            "unknown_fraction": round(self.unknown_fraction, 6),
            "exact_match_pixel_count": self.exact_match_pixel_count,
            "approx_match_pixel_count": self.approx_match_pixel_count,
            "tolerance": self.tolerance,
            "name_threshold": self.name_threshold,
            "unknown_colors_json": json.dumps(self.unknown_colors[:20]),
        }
        fractions = self.fractions
        for code in INTERACTION_CODES:
            row[f"{code}_count"] = self.counts.get(code, 0)
            row[f"{code}_fraction"] = round(fractions.get(code, 0.0), 6)
        return row

    def interaction_rows(self) -> list[dict[str, object]]:
        rows = []
        fractions = self.fractions
        for code in OFFICIAL_CODES:
            count = self.counts.get(code, 0)
            if count <= 0:
                continue
            item = INTERACTION_BY_CODE[code]
            rows.append(
                {
                    "code": code,
                    "interaction": item.name,
                    "token": item.token,
                    "rgb": str(item.rgb),
                    "pixel_count": count,
                    "fraction": fractions[code],
                    "exact_count": self.exact_counts.get(code, 0),
                    "approx_count": self.approx_counts.get(code, 0),
                }
            )
        rows.sort(key=lambda row: row["fraction"], reverse=True)
        return rows


def sample_id_from_name(filename: str, content: bytes | None = None) -> str:
    stem = Path(filename).stem.replace(" ", "_")
    if content is None:
        return stem
    digest = hashlib.sha1(content).hexdigest()[:8]
    return f"{stem}__{digest}"


def load_rgb_image(source: str | Path | BinaryIO) -> np.ndarray:
    with Image.open(source) as image:
        return np.array(image.convert("RGB"))


def _unique_colors(rgb: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    flat = rgb.reshape(-1, 3).astype(np.uint32, copy=False)
    packed = (flat[:, 0] << 16) | (flat[:, 1] << 8) | flat[:, 2]
    unique_packed, counts = np.unique(packed, return_counts=True)
    colors = np.column_stack(
        [
            (unique_packed >> 16) & 255,
            (unique_packed >> 8) & 255,
            unique_packed & 255,
        ]
    ).astype(np.uint8, copy=False)
    return colors, counts


def parse_rgb_array(
    rgb: np.ndarray,
    filename: str,
    content: bytes | None = None,
    tolerance: float = DEFAULT_TOLERANCE,
    name_threshold: float = DEFAULT_NAME_THRESHOLD,
) -> ParsedAnnotation:
    if rgb.ndim != 3 or rgb.shape[2] != 3:
        raise ValueError("Expected an RGB image array with shape (height, width, 3).")

    colors, color_counts = _unique_colors(rgb.astype(np.uint8, copy=False))
    counts = {code: 0 for code in INTERACTION_CODES}
    exact_counts = {code: 0 for code in INTERACTION_CODES}
    approx_counts = {code: 0 for code in INTERACTION_CODES}
    unknown_pixel_count = 0
    unknown_colors: list[dict[str, object]] = []

    official_rgbs = np.array([item.rgb for item in INTERACTIONS], dtype=np.int32)
    official_codes = [item.code for item in INTERACTIONS]

    for color, count_raw in zip(colors, color_counts):
        rgb_tuple = tuple(int(value) for value in color.tolist())
        count = int(count_raw)
        exact = INTERACTION_BY_RGB.get(rgb_tuple)
        if exact is not None:
            counts[exact.code] += count
            exact_counts[exact.code] += count
            continue

        if rgb_tuple == (0, 0, 0):
            counts["BG"] += count
            exact_counts["BG"] += count
            continue

        color_vec = color.astype(np.int32)
        distances = np.sqrt(np.sum((official_rgbs - color_vec) ** 2, axis=1))
        nearest_index = int(np.argmin(distances))
        nearest_distance = float(distances[nearest_index])
        if nearest_distance <= tolerance:
            code = official_codes[nearest_index]
            counts[code] += count
            approx_counts[code] += count
        else:
            unknown_pixel_count += count
            if len(unknown_colors) < 100:
                unknown_colors.append(
                    {
                        "rgb": rgb_tuple,
                        "pixel_count": count,
                        "nearest_code": official_codes[nearest_index],
                        "nearest_distance": round(nearest_distance, 3),
                    }
                )

    unknown_colors.sort(key=lambda row: int(row["pixel_count"]), reverse=True)
    height, width = rgb.shape[:2]
    return ParsedAnnotation(
        sample_id=sample_id_from_name(filename, content),
        original_filename=filename,
        width=int(width),
        height=int(height),
        total_pixels=int(width * height),
        counts=counts,
        exact_counts=exact_counts,
        approx_counts=approx_counts,
        unknown_pixel_count=unknown_pixel_count,
        unknown_colors=unknown_colors,
        tolerance=tolerance,
        name_threshold=name_threshold,
    )


def parse_image_file(
    path: Path,
    tolerance: float = DEFAULT_TOLERANCE,
    name_threshold: float = DEFAULT_NAME_THRESHOLD,
) -> ParsedAnnotation:
    content = path.read_bytes()
    rgb = load_rgb_image(path)
    return parse_rgb_array(rgb, path.name, content, tolerance=tolerance, name_threshold=name_threshold)


def parse_uploaded_image(
    uploaded_file,
    tolerance: float = DEFAULT_TOLERANCE,
    name_threshold: float = DEFAULT_NAME_THRESHOLD,
) -> tuple[ParsedAnnotation, Image.Image]:
    content = uploaded_file.getvalue()
    image = Image.open(uploaded_file).convert("RGB")
    rgb = np.array(image)
    parsed = parse_rgb_array(rgb, uploaded_file.name, content, tolerance=tolerance, name_threshold=name_threshold)
    return parsed, image


def build_metadata_frame(summaries: list[ParsedAnnotation]) -> pd.DataFrame:
    return pd.DataFrame([summary.to_row() for summary in summaries])


def class_distribution(metadata: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for code in OFFICIAL_CODES:
        item = INTERACTION_BY_CODE[code]
        count_column = f"{code}_count"
        fraction_column = f"{code}_fraction"
        if count_column not in metadata:
            continue
        rows.append(
            {
                "code": code,
                "token": item.token,
                "interaction": item.name,
                "images_present": int((metadata[count_column] > 0).sum()),
                "dominant_images": int((metadata["dominant_code"] == code).sum()),
                "total_pixels": int(metadata[count_column].sum()),
                "mean_fraction": round(float(metadata[fraction_column].mean()), 6),
            }
        )
    return pd.DataFrame(rows).sort_values(["dominant_images", "images_present", "total_pixels"], ascending=False)


def cooccurrence_matrix(metadata: pd.DataFrame, min_fraction: float = DEFAULT_NAME_THRESHOLD) -> pd.DataFrame:
    codes = [code for code in OFFICIAL_CODES if code != "OR"]
    matrix = pd.DataFrame(0, index=codes, columns=codes, dtype=int)
    for _, row in metadata.iterrows():
        present = [code for code in codes if float(row.get(f"{code}_fraction", 0.0)) >= min_fraction]
        for left in present:
            for right in present:
                matrix.loc[left, right] += 1
    matrix.index.name = "interaction"
    return matrix


def sort_by_priority(metadata: pd.DataFrame, priority_codes: list[str]) -> pd.DataFrame:
    sort_columns = [f"{code}_fraction" for code in priority_codes if f"{code}_fraction" in metadata.columns]
    sort_columns.extend(["dominant_fraction", "official_pixel_count"])
    sort_columns = [column for column in sort_columns if column in metadata.columns]
    if not sort_columns:
        return metadata
    return metadata.sort_values(sort_columns, ascending=[False] * len(sort_columns)).reset_index(drop=True)


def export_summary_tables(metadata: pd.DataFrame, output_dir: Path) -> dict[str, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    distribution = class_distribution(metadata)
    cooccur = cooccurrence_matrix(metadata)
    clean = metadata[metadata["recommended_tag"] == "clean_training_candidate"].copy()
    mixed = metadata[metadata["recommended_tag"].isin(["mixed_scene", "complex_scene"])].copy()
    unknown = metadata[metadata["unknown_pixel_count"] > 0].copy()

    paths = {
        "metadata_csv": output_dir / "annotation_metadata.csv",
        "metadata_json": output_dir / "annotation_metadata.json",
        "class_distribution": output_dir / "class_distribution.csv",
        "cooccurrence_matrix": output_dir / "cooccurrence_matrix.csv",
        "clean_samples": output_dir / "clean_samples.csv",
        "mixed_samples": output_dir / "mixed_samples.csv",
        "unknown_color_report": output_dir / "unknown_color_report.csv",
        "processing_summary": output_dir / "processing_summary.json",
    }

    metadata.to_csv(paths["metadata_csv"], index=False)
    metadata.to_json(paths["metadata_json"], orient="records", indent=2)
    distribution.to_csv(paths["class_distribution"], index=False)
    cooccur.to_csv(paths["cooccurrence_matrix"])
    clean.to_csv(paths["clean_samples"], index=False)
    mixed.to_csv(paths["mixed_samples"], index=False)
    unknown.to_csv(paths["unknown_color_report"], index=False)

    payload = {
        "sample_count": int(len(metadata)),
        "official_pixel_count": int(metadata["official_pixel_count"].sum()) if len(metadata) else 0,
        "unknown_pixel_count": int(metadata["unknown_pixel_count"].sum()) if len(metadata) else 0,
        "tag_counts": metadata["recommended_tag"].value_counts().to_dict() if len(metadata) else {},
        "dominant_counts": metadata["dominant_token"].value_counts().to_dict() if len(metadata) else {},
        "files": {key: str(value) for key, value in paths.items() if key != "processing_summary"},
    }
    paths["processing_summary"].write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return paths
