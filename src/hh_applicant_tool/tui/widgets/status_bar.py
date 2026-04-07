from __future__ import annotations

from textual.widgets import Static

from ..state import AppState


class StatusBar(Static):
    """Compact status line with active profile and last run state."""

    def refresh_from_state(self, state: AppState) -> None:
        record = state.active_record
        last_command = record.request.title if record else "—"
        status = record.status.value if record else "idle"
        message = (
            f"Profile: {state.selected_profile_id}  |  "
            f"Path: {state.effective_profile_path}  |  "
            f"Last run: {last_command}  |  Status: {status}"
        )
        self.update(message)
