from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Checkbox, Input, Static

from ..command_builder import CommandBuilder
from .base import AppScreen


class ClearSkippedFormScreen(AppScreen):
    screen_title = "clear-skipped"
    screen_subtitle = "Remove skipped vacancies records via the existing CLI"

    def compose_content(self) -> ComposeResult:
        yield Input(
            placeholder="Reason (ai_rejected, excluded_filter, blocked)",
            id="reason",
        )
        yield Checkbox("Dry run", id="dry-run")
        with Horizontal(classes="action-buttons"):
            yield Button("Run command", id="run-clear", variant="success")
            yield Button("Back", id="go-back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "go-back":
            self.tui_app.pop_screen()
            return
        if event.button.id != "run-clear":
            return

        args: list[str] = []
        CommandBuilder.add_value(args, "--reason", self.input_value("reason"))
        CommandBuilder.add_bool(args, "--dry-run", self.checkbox_value("dry-run"))
        request = self.tui_app.make_request("clear-skipped", "clear-skipped", args=args)
        self.tui_app.run_command(request)


class CreateResumeFormScreen(AppScreen):
    screen_title = "create-resume"
    screen_subtitle = "Create a resume from markdown or TOML template via the existing CLI"

    def compose_content(self) -> ComposeResult:
        yield Input(placeholder="Template path (.md or .toml)", id="template-path")
        yield Checkbox("Dry run", id="dry-run")
        yield Checkbox("Publish after creation", id="publish")
        yield Static(
            "A template path is required. The TUI does not inspect or transform the template.",
            classes="panel muted",
        )
        with Horizontal(classes="action-buttons"):
            yield Button("Run command", id="run-create", variant="success")
            yield Button("Back", id="go-back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "go-back":
            self.tui_app.pop_screen()
            return
        if event.button.id != "run-create":
            return

        template_path = self.input_value("template-path")
        if not template_path:
            self.warn("Template path is required.")
            return

        args = [template_path]
        CommandBuilder.add_bool(args, "--dry-run", self.checkbox_value("dry-run"))
        CommandBuilder.add_bool(args, "--publish", self.checkbox_value("publish"))
        request = self.tui_app.make_request("create-resume", "create-resume", args=args)
        self.tui_app.run_command(request)


class CloneResumeFormScreen(AppScreen):
    screen_title = "clone-resume"
    screen_subtitle = "Clone an existing resume via the existing CLI"

    def compose_content(self) -> ComposeResult:
        yield Input(placeholder="Resume ID (optional)", id="resume-id")
        yield Static(
            "Leave the field empty to clone the default/first resume.",
            classes="panel muted",
        )
        with Horizontal(classes="action-buttons"):
            yield Button("Run command", id="run-clone", variant="success")
            yield Button("Back", id="go-back")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "go-back":
            self.tui_app.pop_screen()
            return
        if event.button.id != "run-clone":
            return

        args: list[str] = []
        CommandBuilder.add_value(args, "--resume-id", self.input_value("resume-id"))
        request = self.tui_app.make_request("clone-resume", "clone-resume", args=args)
        self.tui_app.run_command(request)
