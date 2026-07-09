from __future__ import annotations

from typing import Callable

import pystray
from PIL import Image, ImageDraw


def _make_icon_image() -> Image.Image:
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((4, 4, size - 4, size - 4), fill=(99, 102, 241, 255))
    draw.text((22, 22), "F", fill=(255, 255, 255, 255))
    return img


class TrayIcon:
    def __init__(
        self,
        on_show: Callable[[], None],
        on_start_server: Callable[[], None],
        on_stop_server: Callable[[], None],
        on_run_now: Callable[[], None],
        on_quit: Callable[[], None],
    ) -> None:
        self.icon = pystray.Icon(
            "trend-hopper",
            _make_icon_image(),
            "FOMO",
            menu=pystray.Menu(
                pystray.MenuItem("Open", lambda: on_show(), default=True),
                pystray.MenuItem("Start Server", lambda: on_start_server()),
                pystray.MenuItem("Stop Server", lambda: on_stop_server()),
                pystray.MenuItem("Run Collection Now", lambda: on_run_now()),
                pystray.MenuItem("Quit", lambda: on_quit()),
            ),
        )

    def run_detached(self) -> None:
        self.icon.run_detached()

    def stop(self) -> None:
        self.icon.stop()
