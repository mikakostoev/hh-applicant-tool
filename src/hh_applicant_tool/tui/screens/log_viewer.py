from __future__ import annotations

from pathlib import Path

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.timer import Timer
from textual.widgets import Button, Input, Static, TextArea

from .base import AppScreen


class LogViewerScreen(AppScreen):
    BINDINGS = [
        *AppScreen.BINDINGS,
        Binding("/", "focus_search", "Search", show=False),
    ]

    screen_title = "Log viewer"
    screen_subtitle = "Open the current profile log.txt directly from the filesystem"

    def __init__(self) -> None:
        super().__init__()
        self._follow_timer: Timer | None = None
        self._follow_enabled = False

    def compose_content(self) -> ComposeResult:
        yield Static("", id="log-summary", classes="panel")
        with Horizontal(classes="action-buttons"):
            yield Button("Refresh", id="refresh-log")
            yield Button("Follow: off", id="toggle-follow")
        with Horizontal(classes="action-buttons"):
            yield Input(value="400", placeholder="Last N lines", id="tail-lines")
            yield Input(placeholder="Search in visible lines", id="search-term")
        yield TextArea(
            text="",
            read_only=True,
            soft_wrap=False,
            show_line_numbers=False,
            id="log-area",
            classes="log-area",
        )

    def on_mount(self) -> None:
        super().on_mount()
        self._follow_timer = self.set_interval(2.0, self.refresh_log, pause=True)
        self.refresh_log()

    def action_focus_search(self) -> None:
        self.query_one("#search-term", Input).focus()

    def on_unmount(self) -> None:
        if self._follow_timer is not None:
            self._follow_timer.pause()
            self._follow_timer = None

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "refresh-log":
            self.refresh_log()
            return
        if event.button.id != "toggle-follow":
            return

        self._follow_enabled = not self._follow_enabled
        if self._follow_timer is not None:
            if self._follow_enabled:
                self._follow_timer.resume()
            else:
                self._follow_timer.pause()
        event.button.label = f"Follow: {'on' if self._follow_enabled else 'off'}"
        self.refresh_log()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id in {"tail-lines", "search-term"}:
            self.refresh_log()

    def refresh_log(self) -> None:
        log_path = self.tui_app.state.log_path
        summary = self.query_one("#log-summary", Static)
        area = self.query_one("#log-area", TextArea)

        if not log_path.exists():
            summary.update(f"Log file is missing: {log_path}")
            area.load_text("")
            return

        lines = self._read_lines(log_path)
        search = self.input_value("search-term").lower()
        if search:
            lines = [line for line in lines if search in line.lower()]

        tail_lines = self._tail_limit()
        if tail_lines > 0:
            lines = lines[-tail_lines:]

        area.load_text("\n".join(lines))
        area.scroll_end(animate=False)
        summary.update(
            f"Path: {log_path} | Showing: {len(lines)} lines | Follow: {'on' if self._follow_enabled else 'off'}"
        )

    def _tail_limit(self) -> int:
        raw = self.input_value("tail-lines")
        if not raw:
            return 400
        try:
            return max(1, int(raw))
        except ValueError:
            return 400

    @staticmethod
    def _read_lines(path: Path) -> list[str]:
        return path.read_text(encoding="utf-8", errors="replace").splitlines()
