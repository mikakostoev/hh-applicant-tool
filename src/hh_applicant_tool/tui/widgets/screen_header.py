from __future__ import annotations

from textual.widgets import Static


class ScreenHeader(Static):
    """Simple title + subtitle block reused across screens."""

    def __init__(self, title: str, subtitle: str = "") -> None:
        super().__init__(classes="screen-header")
        self._title = title
        self._subtitle = subtitle

    def on_mount(self) -> None:
        parts = [f"[b]{self._title}[/b]"]
        if self._subtitle:
            parts.append(self._subtitle)
        self.update("\n".join(parts))
