"""Official VMVI interaction color constants."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class InteractionClass:
    code: str
    token: str
    name: str
    rgb: tuple[int, int, int]
    include_in_name: bool = True


INTERACTIONS: tuple[InteractionClass, ...] = (
    InteractionClass("CI", "cut_in", "Cut-in", (255, 140, 0)),
    InteractionClass("CL", "lane_changing", "Lane-changing", (255, 165, 0)),
    InteractionClass("FA", "front_approaching", "Front approaching", (255, 0, 0)),
    InteractionClass("FL", "front_leaving", "Front leaving", (240, 128, 128)),
    InteractionClass("FF", "following", "Following", (255, 99, 71)),
    InteractionClass("PN", "parallel", "Parallel", (255, 255, 0)),
    InteractionClass("PS", "passing", "Passing", (255, 215, 0)),
    InteractionClass("PD", "being_passed", "Being passed", (218, 165, 32)),
    InteractionClass("M", "merging", "Merging / approaching", (60, 179, 113)),
    InteractionClass("O", "oncoming", "Oncoming / opposite", (128, 0, 128)),
    InteractionClass("C", "crossing", "Crossing", (0, 0, 255)),
    InteractionClass("TW", "turning_away", "Turning away", (0, 255, 255)),
    InteractionClass("OR", "off_road", "Off-road / irrelevant", (255, 255, 255), include_in_name=False),
    InteractionClass("BG", "background", "Background", (0, 0, 0), include_in_name=False),
)

INTERACTION_BY_CODE = {item.code: item for item in INTERACTIONS}
INTERACTION_BY_RGB = {item.rgb: item for item in INTERACTIONS}
INTERACTION_CODES = [item.code for item in INTERACTIONS]
OFFICIAL_CODES = [item.code for item in INTERACTIONS if item.code != "BG"]
NAMEABLE_CODES = [item.code for item in INTERACTIONS if item.include_in_name and item.code != "BG"]
RGB_ARRAY = tuple(item.rgb for item in INTERACTIONS)

