"""Deterministic layout calculator for simplified block/inline elements."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .html_parser import Node


@dataclass
class LayoutBox:
    tag: str
    x: int
    y: int
    width: int
    height: int
    children: List["LayoutBox"]


class LayoutEngine:
    """A tiny layout engine meant for deterministic regression tests."""

    BLOCK_ELEMENTS = {"div", "p", "section", "header", "footer", "main"}

    def __init__(self, viewport_width: int = 800, line_height: int = 18) -> None:
        self.viewport_width = viewport_width
        self.line_height = line_height

    def layout(self, node: Node, origin_x: int = 0, origin_y: int = 0) -> LayoutBox:
        y_cursor = origin_y
        children_layout: List[LayoutBox] = []

        for child in node.children:
            if child.tag in self.BLOCK_ELEMENTS:
                height = self.line_height * max(1, len(child.text.split()))
                box = LayoutBox(
                    tag=child.tag,
                    x=origin_x,
                    y=y_cursor,
                    width=self.viewport_width,
                    height=height,
                    children=[],
                )
                y_cursor += height
            else:
                text_width = len(child.text) * 7
                width = min(self.viewport_width, text_width)
                box = LayoutBox(
                    tag=child.tag,
                    x=origin_x,
                    y=y_cursor,
                    width=width,
                    height=self.line_height,
                    children=[],
                )
                y_cursor += self.line_height
            if child.children:
                box.children.extend(self._layout_children(child, box))
            children_layout.append(box)
        total_height = y_cursor - origin_y
        return LayoutBox(tag=node.tag, x=origin_x, y=origin_y, width=self.viewport_width, height=total_height, children=children_layout)

    def _layout_children(self, node: Node, parent_box: LayoutBox) -> List[LayoutBox]:
        nested: List[LayoutBox] = []
        cursor = parent_box.y
        for child in node.children:
            width = min(self.viewport_width, len(child.text) * 7 or self.viewport_width)
            box = LayoutBox(
                tag=child.tag,
                x=parent_box.x,
                y=cursor,
                width=width,
                height=self.line_height,
                children=[],
            )
            cursor += self.line_height
            nested.append(box)
        return nested


def compute_layout(html_root: Node, viewport_width: int = 800) -> LayoutBox:
    engine = LayoutEngine(viewport_width=viewport_width)
    return engine.layout(html_root)


def snapshot_layout(box: LayoutBox) -> Dict[str, Dict[str, int]]:
    """Flatten a layout tree to a deterministic snapshot for tests."""

    snapshot: Dict[str, Dict[str, int]] = {}
    for child in box.children:
        snapshot[child.tag] = {
            "x": child.x,
            "y": child.y,
            "width": child.width,
            "height": child.height,
        }
        if child.children:
            for nested in child.children:
                snapshot[f"{child.tag}/{nested.tag}"] = {
                    "x": nested.x,
                    "y": nested.y,
                    "width": nested.width,
                    "height": nested.height,
                }
    return snapshot
