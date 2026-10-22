"""Command line interface: `python -m pagewatch run`."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable

from pagewatch.config import ConfigError, Watch, load_watches
from pagewatch.diff import compare
from pagewatch.extract import SelectorNotFound, extract_text
from pagewatch.fetch import FetchError, fetch
from pagewatch.notify import Alert, Notifier, notifiers_from_env
from pagewatch.store import SnapshotStore

Fetcher = Callable[[str, dict[str, str]], str]


def check_watch(
    watch: Watch,
    store: SnapshotStore,
    notifiers: list[Notifier],
    fetcher: Fetcher = fetch,
    dry_run: bool = False,
) -> str:
    """Check one watch. Returns a status: baseline | unchanged | changed | filtered | error."""
    try:
        html = fetcher(watch.url, watch.headers)
        text = extract_text(html, watch.selector, watch.compiled_ignore())
    except (FetchError, SelectorNotFound) as exc:
        print(f"[error]     {watch.id}: {exc}", file=sys.stderr)
        return "error"

    previous = store.load(watch.id)
    if previous is None:
        if not dry_run:
            store.save(watch.id, text)
        print(f"[baseline]  {watch.id}: first snapshot saved ({len(text.splitlines())} lines)")
        return "baseline"

    change = compare(previous, text)
    if not change.changed:
        print(f"[unchanged] {watch.id}")
        return "unchanged"

    if not dry_run:
        store.save(watch.id, text)

    matched = change.matching_keywords(watch.keywords)
    if watch.keywords and not matched:
        print(f"[filtered]  {watch.id}: changed, but no keyword matched")
        return "filtered"

    print(f"[changed]   {watch.id}: +{len(change.added)} / -{len(change.removed)} lines")
    alert = Alert(watch=watch, change=change, matched_keywords=matched)
    for notifier in notifiers:
        if dry_run and notifier.name != "console":
            continue
        try:
            notifier.send(alert)
        # Deliberately broad: one broken channel (network, SMTP, API) must not stop the others.
        except Exception as exc:  # noqa: BLE001
            print(f"[error]     {watch.id}: {notifier.name} notification failed: {exc}", file=sys.stderr)
    return "changed"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pagewatch", description="Get notified when web pages change.")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="check all watches once")
    run.add_argument("-c", "--config", default="watches.yml", help="path to watches.yml")
    run.add_argument("-s", "--snapshots", default="snapshots", help="snapshot directory")
    run.add_argument("--only", action="append", metavar="ID", help="check only this watch (repeatable)")
    run.add_argument("--dry-run", action="store_true", help="don't save snapshots or send notifications")
    run.add_argument("--strict", action="store_true", help="exit with code 1 if any watch errored")

    preview = sub.add_parser("preview", help="print the extracted text for a watch (for tuning selectors)")
    preview.add_argument("id")
    preview.add_argument("-c", "--config", default="watches.yml")

    sub.add_parser("list", help="list configured watches").add_argument("-c", "--config", default="watches.yml")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        watches = load_watches(args.config)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2

    if args.command == "list":
        for w in watches:
            state = "" if w.enabled else "  (disabled)"
            print(f"{w.id:<24} {w.url}{state}")
        return 0

    if args.command == "preview":
        watch = next((w for w in watches if w.id == args.id), None)
        if watch is None:
            print(f"no watch with id '{args.id}'", file=sys.stderr)
            return 2
        try:
            print(extract_text(fetch(watch.url, watch.headers), watch.selector, watch.compiled_ignore()))
        except (FetchError, SelectorNotFound) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 1
        return 0

    selected = [w for w in watches if w.enabled and (not args.only or w.id in args.only)]
    if args.only:
        unknown = set(args.only) - {w.id for w in watches}
        if unknown:
            print(f"unknown watch id(s): {', '.join(sorted(unknown))}", file=sys.stderr)
            return 2

    store = SnapshotStore(args.snapshots)
    notifiers = notifiers_from_env()
    statuses = [check_watch(w, store, notifiers, dry_run=args.dry_run) for w in selected]

    counts = {s: statuses.count(s) for s in sorted(set(statuses))}
    print("summary: " + (", ".join(f"{k}={v}" for k, v in counts.items()) or "no watches"))
    return 1 if args.strict and "error" in statuses else 0
