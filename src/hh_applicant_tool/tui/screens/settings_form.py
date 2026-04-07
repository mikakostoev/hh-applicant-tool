from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Input, Select, Static

from .base import AppScreen


SETTINGS_MODE_OPTIONS = [
    ("List all settings", "list"),
    ("Get by key", "get"),
    ("Set value", "set"),
    ("Delete key", "delete"),
    ("Delete all settings", "delete-all"),
]


class SettingsFormScreen(AppScreen):
    screen_title = "settings"
    screen_subtitle = "Manage settings via the existing CLI command"

    def compose_content(self) -> ComposeResult:
        yield Select(
            SETTINGS_MODE_OPTIONS,
            value="list",
            allow_blank=False,
            id="settings-mode",
        )
        yield Input(placeholder="Key", id="settings-key")
        yield Input(placeholder="Value", id="settings-value")
        yield Static(
            "Values are forwarded to the CLI as raw strings. The CLI itself decides how to parse them.",
            classes="panel muted",
        )
        with Horizontal(classes="action-buttons"):
            yield Button("Run command", id="run-settings", variant="success")
            yield Button("Back", id="go-back")

    def on_mount(self) -> None:
        super().on_mount()
        self._sync_fields()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "settings-mode":
            self._sync_fields()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "go-back":
            self.tui_app.pop_screen()
            return
        if event.button.id != "run-settings":
            return

        mode = self.select_value("settings-mode") or "list"
        key = self.input_value("settings-key")
        value = self.input_value("settings-value")
        args: list[str] = []

        if mode == "get":
            if not key:
                self.warn("Key is required for get.")
                return
            args = [key]
        elif mode == "set":
            if not key or not value:
                self.warn("Key and value are required for set.")
                return
            args = [key, value]
        elif mode == "delete":
            if not key:
                self.warn("Key is required for delete.")
                return
            args = ["--delete", key]
        elif mode == "delete-all":
            args = ["--delete"]

        request = self.tui_app.make_request("settings", "settings", args=args)
        self.tui_app.run_command(request)

    def _sync_fields(self) -> None:
        mode = self.select_value("settings-mode") or "list"
        key_input = self.query_one("#settings-key", Input)
        value_input = self.query_one("#settings-value", Input)

        key_input.disabled = mode in {"list", "delete-all"}
        value_input.disabled = mode != "set"
