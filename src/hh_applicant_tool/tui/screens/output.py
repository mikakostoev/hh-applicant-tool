from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal
from textual.widgets import Button, Input, RichLog, Static, TabPane, TabbedContent

from ..state import RunRecord, RunStatus
from .base import AppScreen


class OutputScreen(AppScreen):
    BINDINGS = [
        *AppScreen.BINDINGS,
        Binding("r", "rerun_command", "Rerun"),
        Binding("s", "stop_process", "Stop"),
    ]

    screen_title = "Live Output"
    screen_subtitle = "Streaming stdout/stderr from the existing CLI subprocess"

    def __init__(self) -> None:
        super().__init__()
        self._record: RunRecord | None = None

    def compose_content(self) -> ComposeResult:
        yield Static("No process started yet.", id="output-summary", classes="panel")
        yield Static("", id="command-preview", classes="panel code-block")
        yield Static("", id="output-note", classes="panel muted")
        with Horizontal(classes="action-buttons"):
            yield Button("Stop", id="stop-process", variant="error")
            yield Button("Rerun", id="rerun-command")
            yield Button("Copy command", id="copy-command")
        with Horizontal(id="stdin-row"):
            yield Input(placeholder="Send one line to stdin", id="stdin-input")
            yield Button("Send", id="send-stdin", variant="primary")
        yield Static("", id="recent-runs", classes="panel muted")
        with TabbedContent(initial="merged-tab", id="output-tabs"):
            with TabPane("Merged", id="merged-tab"):
                yield RichLog(id="merged-log", wrap=False, markup=False, highlight=False)
            with TabPane("Stdout", id="stdout-tab"):
                yield RichLog(id="stdout-log", wrap=False, markup=False, highlight=False)
            with TabPane("Stderr", id="stderr-tab"):
                yield RichLog(id="stderr-log", wrap=False, markup=False, highlight=False)

    def on_mount(self) -> None:
        super().on_mount()
        self.tui_app.bind_output_screen(self)
        if self.tui_app.current_record() is not None:
            self.load_record(self.tui_app.current_record())
        else:
            self.refresh_status()

    def on_unmount(self) -> None:
        self.tui_app.unbind_output_screen(self)

    def load_record(self, record: RunRecord | None) -> None:
        self._record = record
        if not self.is_mounted:
            return
        self._clear_logs()
        if record is None:
            self.refresh_status()
            return
        for chunk in record.merged_chunks:
            self._write_chunk("merged", chunk)
        for chunk in record.stdout_chunks:
            self._write_chunk("stdout", chunk)
        for chunk in record.stderr_chunks:
            self._write_chunk("stderr", chunk)
        self.refresh_status()

    def append_output(self, stream: str, text: str) -> None:
        if self._record is None or not self.is_mounted:
            return
        if stream == "stdout":
            self._write_chunk("stdout", text)
            self._write_chunk("merged", text)
            return
        if stream == "stderr":
            self._write_chunk("stderr", text)
            self._write_chunk("merged", text)
            return
        self._write_chunk("merged", text)

    def refresh_status(self) -> None:
        summary = self.query_one("#output-summary", Static)
        preview = self.query_one("#command-preview", Static)
        note = self.query_one("#output-note", Static)
        history = self.query_one("#recent-runs", Static)
        stdin_input = self.query_one("#stdin-input", Input)
        send_button = self.query_one("#send-stdin", Button)
        stop_button = self.query_one("#stop-process", Button)
        rerun_button = self.query_one("#rerun-command", Button)
        copy_button = self.query_one("#copy-command", Button)

        record = self._record
        if record is None:
            summary.update("No process started yet.")
            preview.update("")
            note.update("")
            history.update("Recent runs: none yet.")
            stdin_input.disabled = True
            send_button.disabled = True
            stop_button.disabled = True
            rerun_button.disabled = True
            copy_button.disabled = True
            return

        finished = record.finished_at.strftime("%Y-%m-%d %H:%M:%S") if record.finished_at else "—"
        started = record.started_at.strftime("%Y-%m-%d %H:%M:%S")
        summary.update(
            f"Status: {record.status.value} | Exit code: {record.exit_code} | Mode: {record.mode} | Started: {started} | Finished: {finished}"
        )
        preview.update(record.command_text)
        note_text = record.runtime_note or (
            "PTY mode merges stdout/stderr into a single stream." if record.mode == "pty" else ""
        )
        note.update(note_text)
        history.update(self._history_text())

        is_running = record.status == RunStatus.RUNNING
        stdin_input.disabled = not is_running
        send_button.disabled = not is_running
        stop_button.disabled = not is_running
        rerun_button.disabled = is_running
        copy_button.disabled = False

    def action_rerun_command(self) -> None:
        self.tui_app.rerun_last_command()

    def action_stop_process(self) -> None:
        self.tui_app.request_stop_active_process()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id
        if button_id == "copy-command":
            self.tui_app.request_copy_command()
            return
        if button_id == "rerun-command":
            self.action_rerun_command()
            return
        if button_id == "stop-process":
            self.action_stop_process()
            return
        if button_id != "send-stdin":
            return
        self._send_stdin()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "stdin-input":
            self._send_stdin()

    def _send_stdin(self) -> None:
        stdin_input = self.query_one("#stdin-input", Input)
        value = stdin_input.value
        if not value.strip():
            self.warn("Nothing to send.")
            return
        self.tui_app.request_send_stdin(value)
        stdin_input.value = ""

    def _clear_logs(self) -> None:
        self.query_one("#merged-log", RichLog).clear()
        self.query_one("#stdout-log", RichLog).clear()
        self.query_one("#stderr-log", RichLog).clear()

    def _write_chunk(self, stream: str, text: str) -> None:
        log_id = {
            "merged": "#merged-log",
            "stdout": "#stdout-log",
            "stderr": "#stderr-log",
        }[stream]
        log = self.query_one(log_id, RichLog)
        lines = text.splitlines()
        if not lines:
            lines = [text]
        for line in lines:
            log.write(Text.from_ansi(line))

    def _history_text(self) -> str:
        history = self.tui_app.state.run_history[:5]
        if not history:
            return "Recent runs: none yet."

        rows = ["Recent runs:"]
        for entry in history:
            started = entry.started_at.strftime("%H:%M:%S")
            exit_code = "—" if entry.exit_code is None else str(entry.exit_code)
            rows.append(
                f"{started} | {entry.request.title} ({entry.request.subcommand}) | "
                f"{entry.status.value} | {entry.mode} | exit {exit_code}"
            )
        return "\n".join(rows)
