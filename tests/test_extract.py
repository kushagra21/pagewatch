import re

import pytest

from pagewatch.extract import SelectorNotFound, extract_text

HTML = """
<html><head><title>t</title><style>.x{}</style></head>
<body>
  <nav>Home  |  About</nav>
  <div id="jobs">
    <h2>Open roles</h2>
    <ul><li>Backend   Engineer</li><li>Data Analyst</li></ul>
    <p>Updated 2026-10-22 10:15</p>
  </div>
  <script>var tracking = 1;</script>
</body></html>
"""


def test_whole_page_drops_scripts_and_styles():
    text = extract_text(HTML)
    assert "tracking" not in text
    assert ".x{}" not in text
    assert "Home | About" in text


def test_selector_limits_to_section_and_normalizes_whitespace():
    text = extract_text(HTML, selector="#jobs")
    assert text.splitlines() == [
        "Open roles",
        "Backend Engineer",
        "Data Analyst",
        "Updated 2026-10-22 10:15",
    ]


def test_ignore_patterns_remove_noise_and_empty_lines():
    text = extract_text(HTML, selector="#jobs", ignore=[re.compile(r"^Updated .*$")])
    assert "Updated" not in text
    assert text.splitlines()[-1] == "Data Analyst"


def test_missing_selector_raises():
    with pytest.raises(SelectorNotFound):
        extract_text(HTML, selector="#nope")


TABLE_HTML = """
<article><div class="theme-doc-markdown markdown">
  <h2 id="schedule">Schedule</h2>
  <div class="releases-schedule-table"><div class="table-wrapper"><table>
    <thead><tr><th>Version</th><th>Branch cut date</th><th>Release date</th><th>Support</th><th>Blog post</th></tr></thead>
    <tbody>
      <tr><td>0.89.x</td><td>2026-11-03</td><td>2026-12-07</td><td>Future</td><td></td></tr>
      <tr><td>0.88.x</td><td>2026-09-07</td><td>2026-10-12</td><td>Future</td><td></td></tr>
      <tr><td>0.87.x</td><td>2026-07-06</td><td>2026-08-10</td><td>Active</td><td><a href="/blog">Details</a></td></tr>
    </tbody>
  </table></div></div>
  <h2>Release channels</h2>
  <table><tr><th>Channel</th><th>Install</th></tr><tr><td>latest</td><td>react-native@latest</td></tr></table>
</div></article>
"""


def test_table_rows_become_single_lines():
    text = extract_text(TABLE_HTML, selector=".releases-schedule-table table")
    assert text.splitlines() == [
        "Version | Branch cut date | Release date | Support | Blog post",
        "0.89.x | 2026-11-03 | 2026-12-07 | Future |",
        "0.88.x | 2026-09-07 | 2026-10-12 | Future |",
        "0.87.x | 2026-07-06 | 2026-08-10 | Active | Details",
    ]


def test_ignore_can_drop_trailing_columns():
    drop_support = re.compile(r"\s*\|\s*(Support|Future|Active|End of Cycle|Unsupported)\b.*$")
    text = extract_text(
        TABLE_HTML, selector=".releases-schedule-table table", ignore=[drop_support]
    )
    assert text.splitlines()[1] == "0.89.x | 2026-11-03 | 2026-12-07"


def test_tables_without_closing_tags_are_parsed_like_a_browser():
    # Valid HTML5 may omit </th>, </td> and </tr>; reactnative.dev does this.
    html = (
        '<div class="releases-schedule-table"><table><thead><tr><th>Version<th>Branch cut date'
        "<tbody><tr><td>0.89.x<td>2026-11-03<tr><td>0.88.x<td>2026-09-07</table></div>"
    )
    assert extract_text(html, ".releases-schedule-table table").splitlines() == [
        "Version | Branch cut date",
        "0.89.x | 2026-11-03",
        "0.88.x | 2026-09-07",
    ]
