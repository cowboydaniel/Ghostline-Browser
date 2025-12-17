"""Deterministic HTML parser producing a minimal DOM tree."""
from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Dict, List, Optional


@dataclass
class Node:
    """Minimal DOM node representation with deterministic ordering."""

    tag: str
    attributes: Dict[str, str]
    children: List["Node"] = field(default_factory=list)
    text: str = ""

    def find(self, tag: str) -> Optional["Node"]:
        for child in self.children:
            if child.tag == tag:
                return child
            nested = child.find(tag)
            if nested:
                return nested
        return None


class DeterministicHTMLParser(HTMLParser):
    """HTML parser that builds a simplified DOM for layout tests."""

    def __init__(self) -> None:
        super().__init__()
        self.root = Node(tag="document", attributes={})
        self._stack: List[Node] = [self.root]

    def handle_starttag(self, tag: str, attrs) -> None:  # noqa: D401
        attribute_map = {key: value or "" for key, value in attrs}
        node = Node(tag=tag, attributes=attribute_map)
        self._stack[-1].children.append(node)
        self._stack.append(node)

    def handle_endtag(self, tag: str) -> None:  # noqa: D401
        while self._stack and self._stack[-1].tag != tag:
            self._stack.pop()
        if self._stack and self._stack[-1].tag == tag:
            self._stack.pop()

    def handle_data(self, data: str) -> None:  # noqa: D401
        if not data.strip():
            return
        self._stack[-1].text += data.strip()

    def parse(self, html: str) -> Node:
        self.root = Node(tag="document", attributes={})
        self._stack = [self.root]
        self.feed(html)
        self.close()
        return self.root


def parse_html(html: str) -> Node:
    parser = DeterministicHTMLParser()
    return parser.parse(html)
