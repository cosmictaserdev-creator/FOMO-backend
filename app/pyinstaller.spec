# -*- mode: python ; coding: utf-8 -*-
# Built with: uv run --group dev pyinstaller pyinstaller.spec
#
# onedir (not onefile): this app has a system tray icon meant to run continuously /
# start at login, so onefile's self-extract-to-temp-on-every-launch cost (startup
# latency + repeated AV re-scanning) is a worse tradeoff here than one extra folder.
from pathlib import Path

app_dir = Path(SPECPATH)
backend_dir = app_dir.parent / "backend"

a = Analysis(
    ["main.py"],
    # Including backend/ in pathex lets Analysis trace `import config`, `import db`,
    # `import collector`, `import filter`, `sources.*` as real source and pull in their
    # transitive deps (supabase, groq, praw, feedparser, bs4, requests, dotenv)
    # automatically -- same as if backend/ were part of this project.
    pathex=[str(app_dir), str(backend_dir)],
    binaries=[],
    datas=[
        (str(app_dir / "views"), "views"),
    ],
    hiddenimports=[
        # collector.py picks these via importlib.import_module(f"sources.{name}") --
        # a dynamic string Analysis can't trace statically.
        "sources.reddit",
        "sources.hackernews",
        "sources.github_trending",
        "sources.rss",
        "sources.youtube",
        "sources.soundcloud",
        # pywebview/pystray select their OS backend via a try/except-wrapped import
        # inside a function; harmless to pin explicitly in case Analysis's detection
        # of that pattern ever misses it on a future library version.
        "webview.platforms.winforms",
        "webview.platforms.win32",
        "pystray._win32",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="FomoControlPanel",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # no console window -- this app must never show a CLI to the user
    icon=None,  # TODO: replace with a real .ico asset before shipping
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="FomoControlPanel",
)
