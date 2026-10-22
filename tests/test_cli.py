from pagewatch.cli import check_watch
from pagewatch.config import Watch
from pagewatch.store import SnapshotStore


class RecordingNotifier:
    name = "recording"

    def __init__(self):
        self.alerts = []

    def send(self, alert):
        self.alerts.append(alert)


def page(*items):
    lis = "".join(f"<li>{i}</li>" for i in items)
    return f"<html><body><ul id='list'>{lis}</ul></body></html>"


def fetcher_for(html):
    return lambda url, headers: html


def test_first_run_saves_baseline_without_alert(tmp_path):
    store, notifier = SnapshotStore(tmp_path), RecordingNotifier()
    watch = Watch(id="w", url="https://x.io", selector="#list")
    assert check_watch(watch, store, [notifier], fetcher_for(page("a"))) == "baseline"
    assert store.load("w") == "a\n"
    assert notifier.alerts == []


def test_change_triggers_alert_and_updates_snapshot(tmp_path):
    store, notifier = SnapshotStore(tmp_path), RecordingNotifier()
    watch = Watch(id="w", url="https://x.io", selector="#list")
    check_watch(watch, store, [notifier], fetcher_for(page("a")))

    assert check_watch(watch, store, [notifier], fetcher_for(page("a"))) == "unchanged"
    assert check_watch(watch, store, [notifier], fetcher_for(page("a", "b"))) == "changed"
    assert notifier.alerts[0].change.added == ["b"]
    assert store.load("w") == "a\nb\n"


def test_keyword_filter_suppresses_irrelevant_changes(tmp_path):
    store, notifier = SnapshotStore(tmp_path), RecordingNotifier()
    watch = Watch(id="w", url="https://x.io", selector="#list", keywords=["engineer"])
    check_watch(watch, store, [notifier], fetcher_for(page("a")))

    assert check_watch(watch, store, [notifier], fetcher_for(page("a", "Analyst"))) == "filtered"
    assert check_watch(watch, store, [notifier], fetcher_for(page("a", "Analyst", "Engineer"))) == "changed"
    assert notifier.alerts[0].matched_keywords == ["engineer"]


def test_dry_run_does_not_write(tmp_path):
    store = SnapshotStore(tmp_path)
    watch = Watch(id="w", url="https://x.io")
    check_watch(watch, store, [], fetcher_for(page("a")), dry_run=True)
    assert store.load("w") is None


def test_missing_selector_is_reported_as_error(tmp_path):
    watch = Watch(id="w", url="https://x.io", selector="#gone")
    assert check_watch(watch, SnapshotStore(tmp_path), [], fetcher_for(page("a"))) == "error"


def test_one_failing_notifier_does_not_block_others(tmp_path):
    class Broken:
        name = "broken"

        def send(self, alert):
            raise RuntimeError("boom")

    store, notifier = SnapshotStore(tmp_path), RecordingNotifier()
    watch = Watch(id="w", url="https://x.io")
    check_watch(watch, store, [Broken(), notifier], fetcher_for(page("a")))
    check_watch(watch, store, [Broken(), notifier], fetcher_for(page("b")))
    assert len(notifier.alerts) == 1
