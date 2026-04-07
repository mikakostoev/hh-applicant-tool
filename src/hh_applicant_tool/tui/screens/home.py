from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Button, Static

from .action_form import SimpleActionScreen
from .advanced_runner import AdvancedRunnerScreen
from .apply_form import ApplyFormScreen
from .base import AppScreen
from .config_form import ConfigFormScreen
from .log_viewer import LogViewerScreen
from .profiles import ProfilesScreen
from .reply_form import ReplyFormScreen
from .settings_form import SettingsFormScreen
from .support_forms import (
    ClearSkippedFormScreen,
    CloneResumeFormScreen,
    CreateResumeFormScreen,
)


class HomeScreen(AppScreen):
    screen_title = "HH Applicant Tool TUI"
    screen_subtitle = "Guided forms for common commands plus an advanced runner for everything else"

    def compose_content(self) -> ComposeResult:
        yield Static("", id="home-summary", classes="panel compact-panel")
        yield Static("Navigation", classes="section-title")
        with Horizontal(classes="button-row"):
            yield Button("Profiles", id="profiles", variant="primary")
            yield Button("Live output", id="live-output", variant="primary")
            yield Button("Logs", id="logs", variant="primary")
            yield Button("Advanced runner", id="advanced-runner", variant="primary")
        yield Static("Quick actions", classes="section-title")
        with Horizontal(classes="button-row"):
            yield Button("whoami", id="whoami")
            yield Button("list-resumes", id="list-resumes")
            yield Button("refresh-token", id="refresh-token")
        with Horizontal(classes="button-row"):
            yield Button("update-resumes", id="update-resumes")
            yield Button("test-session", id="test-session")
            yield Button("logout", id="logout")
            yield Button("check-proxy", id="check-proxy")
        yield Static("Guided forms", classes="section-title")
        with Horizontal(classes="button-row"):
            yield Button("apply-vacancies", id="apply-vacancies")
            yield Button("reply-employers", id="reply-employers")
            yield Button("settings", id="settings")
            yield Button("config", id="config")
        with Horizontal(classes="button-row"):
            yield Button("clear-skipped", id="clear-skipped")
            yield Button("create-resume", id="create-resume")
            yield Button("clone-resume", id="clone-resume")

    def on_mount(self) -> None:
        super().on_mount()
        self.refresh_summary()

    def on_show(self) -> None:
        super().on_show()
        self.refresh_summary()

    def refresh_summary(self) -> None:
        record = self.tui_app.current_record()
        last_run = record.request.title if record else "—"
        self.query_one("#home-summary", Static).update(
            f"Profile: {self.tui_app.state.selected_profile_id} | "
            f"Path: {self.tui_app.state.effective_profile_path}\n"
            f"Last run: {last_run}"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id is None:
            return

        simple_actions = {
            "whoami": ("whoami", "whoami", "Show the current account identity."),
            "list-resumes": (
                "list-resumes",
                "list-resumes",
                "Fetch and print all resumes.",
            ),
            "refresh-token": (
                "refresh-token",
                "refresh-token",
                "Refresh OAuth tokens when needed.",
            ),
            "update-resumes": (
                "update-resumes",
                "update-resumes",
                "Update all published resumes.",
            ),
            "test-session": (
                "test-session",
                "test-session",
                "Check whether browser cookies still represent a logged in session.",
            ),
            "logout": (
                "logout",
                "logout",
                "Delete the current OAuth token from the active profile.",
            ),
            "check-proxy": (
                "check-proxy",
                "check-proxy",
                "Print the IP address visible through the configured proxy.",
            ),
        }

        if button_id in simple_actions:
            title, subcommand, description = simple_actions[button_id]
            self.tui_app.push_screen(
                SimpleActionScreen(title, subcommand, description)
            )
            return

        if button_id == "apply-vacancies":
            self.tui_app.push_screen(ApplyFormScreen())
            return
        if button_id == "reply-employers":
            self.tui_app.push_screen(ReplyFormScreen())
            return
        if button_id == "settings":
            self.tui_app.push_screen(SettingsFormScreen())
            return
        if button_id == "config":
            self.tui_app.push_screen(ConfigFormScreen())
            return
        if button_id == "clear-skipped":
            self.tui_app.push_screen(ClearSkippedFormScreen())
            return
        if button_id == "create-resume":
            self.tui_app.push_screen(CreateResumeFormScreen())
            return
        if button_id == "clone-resume":
            self.tui_app.push_screen(CloneResumeFormScreen())
            return
        if button_id == "profiles":
            self.tui_app.push_screen(ProfilesScreen())
            return
        if button_id == "logs":
            self.tui_app.push_screen(LogViewerScreen())
            return
        if button_id == "advanced-runner":
            self.tui_app.push_screen(AdvancedRunnerScreen())
            return
        if button_id == "live-output":
            self.tui_app.open_output_screen()
