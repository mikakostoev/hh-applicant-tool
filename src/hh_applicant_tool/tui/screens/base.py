from __future__ import annotations

from typing import TYPE_CHECKING

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Container
from textual.screen import Screen
from textual.widgets import Checkbox, Footer, Header, Input, Select, TextArea

from ..command_builder import CommandBuilder
from ..widgets import ScreenHeader, StatusBar

if TYPE_CHECKING:
    from ..app import ApplicantToolTuiApp


class AppScreen(Screen[None]):
    BINDINGS = [
        Binding("q", "app.back_or_quit", "Back/Quit"),
        Binding("escape", "app.back_or_quit", "Back", show=False),
    ]

    screen_title = "HH Applicant Tool TUI"
    screen_subtitle = "Textual shell over the existing CLI"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield StatusBar(id="status-bar")
        with Container(id="screen-root"):
            yield ScreenHeader(self.screen_title, self.screen_subtitle)
            yield from self.compose_content()
        yield Footer()

    def compose_content(self) -> ComposeResult:
        raise NotImplementedError

    @property
    def tui_app(self) -> "ApplicantToolTuiApp":
        return self.app  # type: ignore[return-value]

    def on_mount(self) -> None:
        self.tui_app.refresh_status_bars()

    def on_show(self) -> None:
        self.tui_app.refresh_status_bars()

    def input_value(self, widget_id: str) -> str:
        return self.query_one(f"#{widget_id}", Input).value.strip()

    def text_area_value(self, widget_id: str) -> str:
        return self.query_one(f"#{widget_id}", TextArea).text.strip()

    def checkbox_value(self, widget_id: str) -> bool:
        return self.query_one(f"#{widget_id}", Checkbox).value

    def select_value(self, widget_id: str) -> str | None:
        value = self.query_one(f"#{widget_id}", Select).value
        if value == Select.NULL:
            return None
        return str(value)

    def multiline_values(self, widget_id: str) -> list[str]:
        return CommandBuilder.split_multiline(self.text_area_value(widget_id))

    def warn(self, message: str) -> None:
        self.tui_app.notify(message, severity="warning")
