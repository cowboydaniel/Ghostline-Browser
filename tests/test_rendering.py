from ghostline.rendering.html_parser import parse_html
from ghostline.rendering.layout import compute_layout, snapshot_layout


def test_block_and_inline_layout_deterministic():
    html = """
    <main>
        <header>Title</header>
        <div>Block text content</div>
        <span>Inline note</span>
    </main>
    """
    dom = parse_html(html)
    layout = compute_layout(dom, viewport_width=600)
    snapshot = snapshot_layout(layout)
    assert snapshot["header"]["x"] == 0
    assert snapshot["div"]["width"] == 600
    assert snapshot["span"]["height"] == 18


def test_nested_children_snapshotting():
    html = """
    <div>
        <p>First</p>
        <p>Second</p>
    </div>
    """
    dom = parse_html(html)
    layout = compute_layout(dom)
    snapshot = snapshot_layout(layout)
    assert "div/p" in snapshot
    assert snapshot["div/p"]["y"] == 0
