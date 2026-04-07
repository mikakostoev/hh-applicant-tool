from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Checkbox, Input, Select, Static, TextArea

from ..command_builder import CommandBuilder
from .base import AppScreen


class AdvancedRunnerScreen(AppScreen):
    screen_title = "Advanced runner"
    screen_subtitle = "Run any CLI subcommand with one argv token per line"

    def compose_content(self) -> ComposeResult:
        yield Static(
            "Use this screen for rare or interactive commands such as authorize, query, migrate-db and call-api.",
            classes="panel",
        )
        yield Select(
            CommandBuilder.command_options(),
            value="whoami",
            allow_blank=False,
            id="command-selector",
        )
        yield Input(
            placeholder="Custom subcommand (used only when 'Custom command' is selected)",
            id="custom-command",
            disabled=True,
        )
        yield Checkbox("Interactive / PTY mode", id="interactive-toggle")
        yield Static("", id="runner-note", classes="panel muted")
        yield TextArea(
            text="",
            id="advanced-args",
            placeholder="One argument per line, for example:\n--resume-id\n123\n--dry-run",
            classes="multi-line",
        )
        with Horizontal(classes="action-buttons"):
            yield Button("Run command", id="run-advanced", variant="success")
            yield Button("Back", id="go-back")

    def on_mount(self) -> None:
        super().on_mount()
        self._sync_command_mode()

    def on_select_changed(self, event: Select.Changed) -> None:
        if event.select.id == "command-selector":
            self._sync_command_mode()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "go-back":
            self.tui_app.pop_screen()
            return
        if event.button.id != "run-advanced":
            return

        subcommand = self._selected_subcommand()
        if not subcommand:
            self.warn("Choose a command or provide a custom subcommand.")
            return

        args = self.multiline_values("advanced-args")
        request = self.tui_app.make_request(
            f"Advanced: {subcommand}",
            subcommand,
            args=args,
            interactive=self.checkbox_value("interactive-toggle"),
            note="Args are forwarded as-is: one argv token per line.",
        )
        self.tui_app.run_command(request)

    def _sync_command_mode(self) -> None:
        selected = self.select_value("command-selector") or "whoami"
        custom_input = self.query_one("#custom-command", Input)
        toggle = self.query_one("#interactive-toggle", Checkbox)
        note = self.query_one("#runner-note", Static)
        args_area = self.query_one("#advanced-args", TextArea)

        custom_mode = selected == "__custom__"
        custom_input.disabled = not custom_mode
        if custom_mode:
            note.update("Custom mode: provide the exact subcommand name in the field below. Arguments are still one token per line.")
            return

        if selected == "authorize" and not args_area.text.strip():
            args_area.load_text("--no-headless")

        is_tty = CommandBuilder.is_tty_sensitive(selected)
        if is_tty:
            toggle.value = True
            if selected == "authorize":
                note.update("Recommended: keep PTY mode enabled and start with --no-headless so the browser window is visible.")
            else:
                note.update("Recommended: keep PTY mode enabled for this command.")
        else:
            toggle.value = False
            note.update("PTY mode is optional. Leave it off for regular non-interactive commands.")

    def _selected_subcommand(self) -> str:
        selected = self.select_value("command-selector") or ""
        if selected == "__custom__":
            return self.input_value("custom-command")
        return selected
