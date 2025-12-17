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
            box = self._layout_single(child, origin_x=origin_x, origin_y=y_cursor)
            children_layout.append(box)
            y_cursor += box.height

        total_height = y_cursor - origin_y
        return LayoutBox(tag=node.tag, x=origin_x, y=origin_y, width=self.viewport_width, height=total_height, children=children_layout)

    def _layout_single(self, node: Node, origin_x: int, origin_y: int) -> LayoutBox:
        if node.tag in self.BLOCK_ELEMENTS:
            width = self.viewport_width
            height = self.line_height * max(1, len(node.text.split()))
        else:
            text_width = len(node.text) * 7
            width = min(self.viewport_width, text_width or self.viewport_width)
            height = self.line_height

        children: List[LayoutBox] = []
        if node.children:
            child_engine = self.layout(Node(tag=node.tag, attributes=node.attributes, children=node.children, text=node.text), origin_x=origin_x, origin_y=origin_y)
            children = child_engine.children
            height = max(height, child_engine.height)

        return LayoutBox(tag=node.tag, x=origin_x, y=origin_y, width=width, height=height, children=children)


def compute_layout(html_root: Node, viewport_width: int = 800) -> LayoutBox:
    engine = LayoutEngine(viewport_width=viewport_width)
    return engine.layout(html_root)


def snapshot_layout(box: LayoutBox) -> Dict[str, Dict[str, int]]:
    """Flatten a layout tree to a deterministic snapshot for tests."""

    snapshot: Dict[str, Dict[str, int]] = {}

    def visit(node: LayoutBox, parent_tag: str) -> None:
        for child in node.children:
            transparent = parent_tag in {"document", "main"}
            prefix = "" if transparent else f"{parent_tag}/" if parent_tag else ""
            key = f"{prefix}{child.tag}" if prefix or not transparent else child.tag

            if key not in snapshot:
                snapshot[key] = {"x": child.x, "y": child.y, "width": child.width, "height": child.height}
            visit(child, child.tag)

    visit(box, box.tag)
    return snapshot
