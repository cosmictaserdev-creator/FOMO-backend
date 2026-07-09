from __future__ import annotations

import os
import sys
from datetime import date
from pathlib import Path

import collector
import config
import filter as filter_module


def _already_ran_today() -> bool:
    path = Path(__file__).parent / "last_run.txt"
    if path.exists():
        stored = path.read_text().strip()
        return stored == date.today().isoformat()
    return False


def _mark_ran() -> None:
    path = Path(__file__).parent / "last_run.txt"
    path.write_text(date.today().isoformat())


def run() -> None:
    if _already_ran_today():
        print("Already ran today, exiting.")
        return

    print("Starting collector...")
    collector_result = collector.run()
    print(f"Collector: {collector_result}")

    print("Starting filter...")
    filter_result = filter_module.run()
    print(f"Filter: {filter_result}")

    _mark_ran()
    print("Done.")


if __name__ == "__main__":
    run()
