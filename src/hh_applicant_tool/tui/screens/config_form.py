from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Input, Select, Static

from .base import AppScreen


CONFIG_MODE_OPTIONS = [
    ("Show full config", "show"),
    ("Show path", "path"),
    ("Get key", "get"),
    ("Set key", "set"),
    ("Delete key", "delete"),
    ("Open in editor", "edit"),
]


class ConfigFormScreen(AppScreen):
    screen_title = "config"
    screen_subtitle = "Inspect and mutate config.json via the existing CLI command"

    def compose_content(self) -> ComposeResult:
        yield Select(
            CONFIG_MODE_OPTIONS,
            value="show",
            allow_blank=False,
            id="config-mode",
        )
        yield Input(placeholder="Key", id="config-key")
        yield Input(placeholder="Value", id="config-value")
        yield Static(
            "The TUI does not parse config values itself. Whatever you type is forwarded to the CLI.",
            classes="panel muted",
        )
        with Horizontal(classes="action-buttons"):
            yield Button("Run command", id="run-config", variant="success")
            yield Button("Back", id="go-back")

    def on_mount(self) -> None:
        super().on_mount()
        self._sync_fields()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "config-mode":
            self._sync_fields()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "go-back":
            self.tui_app.pop_screen()
            return
        if event.button.id != "run-config":
            return

        mode = self.select_value("config-mode") or "show"
        key = self.input_value("config-key")
        value = self.input_value("config-value")
        args: list[str] = []

        if mode == "path":
            args = ["--show-path"]
        elif mode == "get":
            if not key:
                self.warn("Key is required for get.")
                return
            args = ["--key", key]
        elif mode == "set":
            if not key or not value:
                self.warn("Key and value are required for set.")
                return
            args = ["--set", key, value]
        elif mode == "delete":
            if not key:
                self.warn("Key is required for delete.")
                return
            args = ["--unset", key]
        elif mode == "edit":
            args = ["--edit"]

        request = self.tui_app.make_request("config", "config", args=args)
        self.tui_app.run_command(request)

    def _sync_fields(self) -> None:
        mode = self.select_value("config-mode") or "show"
        key_input = self.query_one("#config-key", Input)
        value_input = self.query_one("#config-value", Input)

        key_input.disabled = mode in {"show", "path", "edit"}
        value_input.disabled = mode != "set"
