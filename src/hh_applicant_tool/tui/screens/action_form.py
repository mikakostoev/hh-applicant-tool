from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Static

from .base import AppScreen


class SimpleActionScreen(AppScreen):
    def __init__(
        self,
        title: str,
        subcommand: str,
        description: str,
        *,
        note: str = "",
        interactive: bool = False,
    ) -> None:
        super().__init__()
        self.screen_title = title
        self.screen_subtitle = description
        self._subcommand = subcommand
        self._note = note
        self._interactive = interactive

    def compose_content(self) -> ComposeResult:
        yield Static(
            "This guided screen runs the existing CLI command without changing its behaviour.",
            classes="panel",
        )
        if self._note:
            yield Static(self._note, classes="panel muted")
        with Horizontal(classes="action-buttons"):
            yield Button("Run command", id="run-command", variant="success")
            yield Button("Back", id="go-back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "go-back":
            self.tui_app.pop_screen()
            return

        if event.button.id != "run-command":
            return

        request = self.tui_app.make_request(
            self.screen_title,
            self._subcommand,
            interactive=self._interactive,
            note=self._note,
        )
        self.tui_app.run_command(request)
