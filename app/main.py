from __future__ import annotations

import sys
from pathlib import Path

import webview

import api_bridge
from api_bridge import ApiBridge
from tray import TrayIcon

def _views_dir() -> Path:
    # __file__ isn't reliably meaningful once frozen (PyInstaller onedir) -- sys._MEIPASS
    # is the actual install/bundle root there, same convention as ktor_manager.py.
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS) / "views"  # type: ignore[attr-defined]
    return Path(__file__).parent / "views"


VIEWS_DIR = _views_dir()


def run_pipeline_once() -> int:
    """Hidden entry point Ktor's /sync/retry shells out to (see PIPELINE_EXE_PATH /
    PIPELINE_EXE_ARGS in ktor_manager.py) -- runs the pipeline synchronously, no GUI."""
    import backend_path  # noqa: F401

    import collector
    import filter as filter_module

    print("collector:", collector.run())
    print("filter:", filter_module.run())
    return 0


def run_mcp_server() -> int:
    """Hidden entry point Claude Desktop/Code spawns (see the MCP tab's config snippet,
    built in mcp_config.py) -- so MCP clients never need a separate Python install to
    reach backend/mcp_server.py's stdio server."""
    import backend_path  # noqa: F401

    import mcp_server

    mcp_server.mcp.run(transport="stdio")
    return 0


def main() -> None:
    api = ApiBridge()
    window = webview.create_window(
        "FOMO Control Panel",
        url=str(VIEWS_DIR / "setup.html"),
        js_api=api,
        width=820,
        height=900,
        min_size=(600, 500),
    )

    def show_window() -> None:
        window.show()
        window.restore()

    def hide_instead_of_close() -> bool:
        window.hide()
        return False  # cancel the actual close; window keeps running in the tray

    def quit_app() -> None:
        api_bridge.scheduler.stop()
        if api_bridge._ktor.is_running():
            api_bridge._ktor.stop()
        tray.stop()
        window.destroy()
        sys.exit(0)

    window.events.closing += hide_instead_of_close

    tray = TrayIcon(
        on_show=show_window,
        on_start_server=lambda: api.start_server(),
        on_stop_server=lambda: api.stop_server(),
        on_run_now=lambda: api.run_pipeline_now(),
        on_quit=quit_app,
    )
    tray.run_detached()

    api_bridge.scheduler.start()

    webview.start()


if __name__ == "__main__":
    if "--run-pipeline-once" in sys.argv:
        sys.exit(run_pipeline_once())
    if "--mcp-server" in sys.argv:
        sys.exit(run_mcp_server())
    main()
