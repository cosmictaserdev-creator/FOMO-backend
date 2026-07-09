from __future__ import annotations

import os
import subprocess
import sys
import threading
from collections import deque
from pathlib import Path
from typing import Optional

import requests

import backend_path  # noqa: F401 -- ensures backend_dir() works the same way as elsewhere

APP_DIR = Path(__file__).parent
LOG_MAX_LINES = 2000


def _dev_or_frozen(dev_relative: str, frozen_relative: str) -> Path:
    if getattr(sys, "frozen", False):
        # jre/ and ktor/ are staged by our own installer build script as siblings of the
        # exe -- NOT via PyInstaller's `datas` (which lands under _internal/ in onedir
        # builds) -- so resolve against the exe's own directory, not sys._MEIPASS.
        return Path(sys.executable).parent / frozen_relative
    return APP_DIR / dev_relative


def javaw_path() -> Path:
    return _dev_or_frozen("../ktor-api/runtime/bin/javaw.exe", "jre/bin/javaw.exe")


def ktor_jar_path() -> Path:
    return _dev_or_frozen("../ktor-api/build/libs/trend-hopper-api.jar", "ktor/trend-hopper-api.jar")


ARGS_SEP = "\x1f"  # ASCII unit separator -- avoids quoting headaches for paths with spaces


def pipeline_trigger_env() -> dict[str, str]:
    """Env vars so Ktor's /sync/retry (SyncRoutes.kt) can shell out to re-run the
    pipeline when co-located with this GUI on the same machine (see main.py's
    --run-pipeline-once). Frozen builds re-invoke the packaged exe with a flag; in dev
    mode this re-invokes the same Python interpreter against main.py."""
    if getattr(sys, "frozen", False):
        return {"PIPELINE_EXE_PATH": sys.executable, "PIPELINE_EXE_ARGS": "--run-pipeline-once"}
    main_py = str((APP_DIR / "main.py").resolve())
    return {"PIPELINE_EXE_PATH": sys.executable, "PIPELINE_EXE_ARGS": f"{main_py}{ARGS_SEP}--run-pipeline-once"}


class KtorManager:
    def __init__(self, port: int = 8080) -> None:
        self.port = port
        self._proc: Optional[subprocess.Popen] = None
        self._log_lines: deque[str] = deque(maxlen=LOG_MAX_LINES)
        self._log_lock = threading.Lock()
        self._reader_thread: Optional[threading.Thread] = None

    def _append_log(self, line: str) -> None:
        with self._log_lock:
            self._log_lines.append(line.rstrip("\n"))

    def _reader_loop(self, proc: subprocess.Popen) -> None:
        assert proc.stdout is not None
        for line in proc.stdout:
            self._append_log(line)

    def start(self, env: dict[str, str]) -> dict[str, object]:
        if self.is_running():
            return {"ok": False, "error": "Ktor server is already running"}

        javaw = javaw_path()
        jar = ktor_jar_path()
        if not javaw.exists():
            return {"ok": False, "error": f"Bundled Java runtime not found at {javaw}"}
        if not jar.exists():
            return {"ok": False, "error": f"Ktor server jar not found at {jar}"}

        # env=... replaces the child's entire environment rather than extending it --
        # merge onto os.environ so SystemRoot/WINDIR/etc. survive (their absence breaks
        # Winsock provider init on Windows: WSA error 10106 "provider failed to init").
        run_env = {**os.environ, **env, "PORT": str(self.port)}
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        self._proc = subprocess.Popen(
            [str(javaw), "-jar", str(jar)],
            env=run_env,
            cwd=str(jar.parent),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            creationflags=creationflags,
        )
        self._log_lines.clear()
        self._reader_thread = threading.Thread(target=self._reader_loop, args=(self._proc,), daemon=True)
        self._reader_thread.start()
        return {"ok": True}

    def stop(self, timeout: float = 5.0) -> dict[str, object]:
        if self._proc is None or self._proc.poll() is not None:
            return {"ok": False, "error": "Ktor server is not running"}
        self._proc.terminate()
        try:
            self._proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            self._proc.kill()
            self._proc.wait(timeout=timeout)
        return {"ok": True}

    def is_running(self) -> bool:
        return self._proc is not None and self._proc.poll() is None

    def health_check(self) -> bool:
        try:
            resp = requests.get(f"http://127.0.0.1:{self.port}/health", timeout=2)
            return resp.status_code == 200
        except requests.RequestException:
            return False

    def status(self) -> dict[str, object]:
        if not self.is_running():
            exit_code = self._proc.returncode if self._proc is not None else None
            return {"state": "stopped", "exit_code": exit_code, "port": self.port}
        if self.health_check():
            return {"state": "running", "port": self.port}
        return {"state": "starting", "port": self.port}

    def logs(self, last_n: int = 200) -> list[str]:
        with self._log_lock:
            return list(self._log_lines)[-last_n:]
