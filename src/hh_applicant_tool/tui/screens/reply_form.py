from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalScroll
from textual.widgets import Button, Checkbox, Input, Static, TextArea

from ..command_builder import CommandBuilder
from .base import AppScreen


class ReplyFormScreen(AppScreen):
    screen_title = "reply-employers"
    screen_subtitle = "Reply to employers via the existing CLI command"

    def compose_content(self) -> ComposeResult:
        with VerticalScroll(classes="form-scroll"):
            yield Input(placeholder="Resume ID (optional)", id="resume-id")
            yield TextArea(
                text="",
                placeholder="Reply message template. Leave empty for interactive chat mode.",
                id="reply-message",
                classes="multi-line",
            )
            yield Input(placeholder="Ignore chats older than N days", id="period")
            yield Input(value="25", placeholder="Max pages", id="max-pages")
            yield Checkbox("Only invitations", id="only-invitations")
            yield Checkbox("Dry run", id="dry-run")
            yield Checkbox("Use AI", id="use-ai")
            yield TextArea(
                text="Ты — соискатель на HeadHunter. Отвечай вежливо и кратко.",
                id="system-prompt",
                classes="multi-line",
            )
            yield TextArea(
                text="Напиши короткий ответ работодателю на основе истории переписки.",
                id="message-prompt",
                classes="multi-line",
            )
            yield Static(
                "If reply message is empty and AI is disabled, the command runs in PTY mode so you can answer each chat manually.",
                classes="panel muted",
            )
            with Horizontal(classes="action-buttons"):
                yield Button("Run command", id="run-reply", variant="success")
                yield Button("Back", id="go-back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "go-back":
            self.tui_app.pop_screen()
            return
        if event.button.id != "run-reply":
            return

        args: list[str] = []
        CommandBuilder.add_value(args, "--resume-id", self.input_value("resume-id"))
        reply_message = self.text_area_value("reply-message")
        CommandBuilder.add_value(args, "--reply-message", reply_message)
        CommandBuilder.add_value(args, "--period", self.input_value("period"))
        CommandBuilder.add_value(args, "--max-pages", self.input_value("max-pages"))
        CommandBuilder.add_bool(args, "--only-invitations", self.checkbox_value("only-invitations"))
        CommandBuilder.add_bool(args, "--dry-run", self.checkbox_value("dry-run"))
        use_ai = self.checkbox_value("use-ai")
        CommandBuilder.add_bool(args, "--use-ai", use_ai)
        CommandBuilder.add_value(args, "--system-prompt", self.text_area_value("system-prompt"))
        CommandBuilder.add_value(args, "--message-prompt", self.text_area_value("message-prompt"))

        interactive = not reply_message and not use_ai
        note = "PTY mode is enabled for interactive chat replies." if interactive else ""
        request = self.tui_app.make_request(
            "reply-employers",
            "reply-employers",
            args=args,
            interactive=interactive,
            note=note,
        )
        self.tui_app.run_command(request)
