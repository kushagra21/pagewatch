import pytest

from pagewatch.config import ConfigError, parse_watches


def test_minimal_watch():
    [w] = parse_watches({"watches": [{"id": "jobs", "url": "https://example.com"}]})
    assert w.selector is None and w.keywords == [] and w.enabled


def test_string_keyword_becomes_list():
    [w] = parse_watches({"watches": [{"id": "a", "url": "https://x.io", "keywords": "python"}]})
    assert w.keywords == ["python"]


@pytest.mark.parametrize(
    "data",
    [
        {},
        {"watches": [{"url": "https://x.io"}]},
        {"watches": [{"id": "Bad Id", "url": "https://x.io"}]},
        {"watches": [{"id": "a", "url": "ftp://x.io"}]},
        {"watches": [{"id": "a", "url": "https://x.io"}, {"id": "a", "url": "https://y.io"}]},
        {"watches": [{"id": "a", "url": "https://x.io", "ignore": ["("]}]},
    ],
)
def test_invalid_configs(data):
    with pytest.raises(ConfigError):
        parse_watches(data)
