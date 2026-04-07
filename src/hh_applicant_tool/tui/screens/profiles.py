from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Button, Static

from .base import AppScreen


class ProfilesScreen(AppScreen):
    screen_title = "Profiles"
    screen_subtitle = "Switch the active profile used for all subsequent CLI runs"

    def compose_content(self) -> ComposeResult:
        yield Static("", id="profiles-summary", classes="panel compact-panel")
        with Horizontal(classes="action-buttons"):
            yield Button("Refresh", id="refresh-profiles")
            yield Button("Back", id="go-back")
        yield Vertical(id="profiles-list", classes="panel")

    def on_mount(self) -> None:
        super().on_mount()
        self.reload_profiles()

    def reload_profiles(self) -> None:
        summary = self.query_one("#profiles-summary", Static)
        summary.update(
            "Select one profile from the config directory.\n"
            f"Config root: {self.tui_app.state.config_root} | "
            f"Active profile: {self.tui_app.state.selected_profile_id}"
        )
        container = self.query_one("#profiles-list", Vertical)
        container.remove_children()

        buttons: list[Button] = []
        current = self.tui_app.state.selected_profile_id
        for index, profile_id in enumerate(self.tui_app.state.list_profiles(), start=1):
            classes = "profile-button"
            if profile_id == current:
                classes += " current-profile"
            buttons.append(
                Button(
                    profile_id,
                    id=f"profile-item-{index}",
                    name=profile_id,
                    classes=classes,
                )
            )
        container.mount(*buttons)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id == "refresh-profiles":
            self.reload_profiles()
            return
        if button_id == "go-back":
            self.tui_app.pop_screen()
            return
        if not button_id.startswith("profile-item-"):
            return
        profile_id = event.button.name or "."
        self.tui_app.select_profile(profile_id)
        self.tui_app.notify(f"Active profile: {profile_id}")
        self.tui_app.pop_screen()
