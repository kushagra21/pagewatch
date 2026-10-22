from pagewatch.diff import compare


def test_no_change():
    assert not compare("a\nb", "a\nb").changed


def test_added_and_removed_lines():
    change = compare("a\nb\nc", "a\nc\nd")
    assert change.added == ["d"]
    assert change.removed == ["b"]
    assert change.changed


def test_keywords_match_added_lines_case_insensitively():
    change = compare("Data Analyst", "Data Analyst\nSenior Backend Engineer")
    assert change.matching_keywords(["backend", "frontend"]) == ["backend"]


def test_keywords_ignore_removed_lines():
    change = compare("Backend Engineer", "Nothing here")
    assert change.matching_keywords(["backend"]) == []
