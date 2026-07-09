from __future__ import annotations

import logging
import threading
from collections import deque
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import backend_path  # noqa: F401 -- must run before backend imports below

import collector
import config
import filter as filter_module

LOG_MAX_LINES = 500
log_buffer: deque[str] = deque(maxlen=LOG_MAX_LINES)


class _BufferHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        log_buffer.append(self.format(record))


_logger = logging.getLogger("trendhopper.scheduler")
_logger.setLevel(logging.INFO)
_handler = _BufferHandler()
_handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
_logger.addHandler(_handler)


class Scheduler:
    def __init__(self) -> None:
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def start(self) -> None:
        if self._thread is not None and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

    def _next_fire(self) -> datetime:
        time_str = config.get_setting("SCHEDULE_TIME", "06:00") or "06:00"
        tz_name = config.get_setting("SCHEDULE_TIMEZONE", "UTC") or "UTC"
        try:
            tz = ZoneInfo(tz_name)
        except ZoneInfoNotFoundError:
            tz = ZoneInfo("UTC")
        hour, minute = (int(p) for p in time_str.split(":"))
        now = datetime.now(tz)
        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        if candidate <= now:
            candidate += timedelta(days=1)
        return candidate

    def _loop(self) -> None:
        _logger.info("Scheduler started")
        last_logged_fire_at: datetime | None = None
        # Re-derives the next fire time on every wake so a schedule change made in the
        # Settings screen takes effect within one poll cycle, without restarting the app.
        while not self._stop_event.is_set():
            try:
                fire_at = self._next_fire()
            except Exception:
                # Most likely: API keys not saved yet (fresh install, Setup screen still
                # empty) so config.get_setting() can't reach Supabase. Don't let this kill
                # the thread permanently -- retry once the user finishes setup.
                self._stop_event.wait(timeout=30)
                continue
            if fire_at != last_logged_fire_at:
                _logger.info(f"Next collection run scheduled for {fire_at.isoformat()}")
                last_logged_fire_at = fire_at
            remaining = (fire_at - datetime.now(fire_at.tzinfo)).total_seconds()
            if remaining <= 0:
                self._run_pipeline()
                last_logged_fire_at = None
                self._stop_event.wait(timeout=60)  # avoid re-firing within the same minute
                continue
            self._stop_event.wait(timeout=min(remaining, 30))

    def _run_pipeline(self) -> None:
        try:
            _logger.info("Running scheduled collection...")
            result = collector.run()
            _logger.info(f"Collector: {result}")
            result = filter_module.run()
            _logger.info(f"Filter: {result}")
        except Exception as e:
            _logger.error(f"Scheduled run failed: {e}")

    def run_now(self) -> None:
        threading.Thread(target=self._run_pipeline, daemon=True).start()
