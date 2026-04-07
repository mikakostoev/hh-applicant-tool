from __future__ import annotations

import asyncio
import os
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

from textual.app import App
from textual.binding import Binding

from .command_builder import CommandBuilder
from .process_runner import BaseProcessRunner, PipeRunner, ProcessCallbacks, PtyRunner
from .state import (
    AppState,
    CommandRequest,
    ManagedProcess,
    RunRecord,
    RunStatus,
)
from .widgets import StatusBar

if TYPE_CHECKING:
    from .screens.output import OutputScreen


class _RunnerBridge(ProcessCallbacks):
    def __init__(self, app: "ApplicantToolTuiApp", record: RunRecord) -> None:
        self._app = app
        self._record = record

    def on_output(self, stream: str, text: str) -> None:
        self._app.handle_process_output(self._record, stream, text)

    def on_exit(self, exit_code: int | None, status: RunStatus) -> None:
        self._app.handle_process_exit(self._record, exit_code, status)


class ApplicantToolTuiApp(App[None]):
    CSS_PATH = Path(__file__).with_name("styles.tcss")
    TITLE = "HH Applicant Tool TUI"
    SUB_TITLE = "Textual frontend over the existing CLI"
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [
        Binding("q", "back_or_quit", "Back/Quit", priority=True),
        Binding("escape", "back_or_quit", "Back", show=False, priority=True),
    ]

    def __init__(self) -> None:
        super().__init__()
        self.state = AppState()
        self.command_builder = CommandBuilder(self.state)
        self._output_screen: OutputScreen | None = None
        self._process_tasks: set[asyncio.Task[None]] = set()

    def on_mount(self) -> None:
        from .screens.home import HomeScreen

        self.push_screen(HomeScreen())

    def action_back_or_quit(self) -> None:
        if len(self.screen_stack) > 1:
            self.pop_screen()
            return
        self.exit()

    def make_request(
        self,
        title: str,
        subcommand: str,
        args: list[str] | None = None,
        *,
        interactive: bool = False,
        note: str = "",
    ) -> CommandRequest:
        return CommandRequest(
            title=title,
            subcommand=subcommand.strip(),
            args=list(args or []),
            interactive=interactive,
            note=note,
        )

    def refresh_status_bars(self) -> None:
        for bar in self.query(StatusBar):
            bar.refresh_from_state(self.state)

    def current_record(self) -> RunRecord | None:
        return self.state.active_record

    def bind_output_screen(self, screen: "OutputScreen") -> None:
        self._output_screen = screen
        record = self.current_record()
        if record is not None:
            screen.load_record(record)

    def unbind_output_screen(self, screen: "OutputScreen") -> None:
        if self._output_screen is screen:
            self._output_screen = None

    def open_output_screen(self) -> None:
        from .screens.output import OutputScreen

        record = self.current_record()
        if record is None:
            self.notify("No runs yet.", severity="warning")
            return

        if self._output_screen is not None:
            self._output_screen.load_record(record)
            if self.screen is not self._output_screen:
                self.push_screen(self._output_screen)
            return

        self.push_screen(OutputScreen())

    def run_command(self, request: CommandRequest) -> None:
        active = self.state.active_process
        if active and active.record.is_running:
            self.notify(
                "Another process is already running. Open Live Output or stop it first.",
                severity="warning",
            )
            self.open_output_screen()
            return

        argv = self.command_builder.build(request)
        mode = "pipe"
        runtime_note = request.note
        runner: BaseProcessRunner

        if request.interactive and os.name == "posix":
            mode = "pty"
        else:
            if request.interactive and os.name != "posix":
                extra = "PTY mode is unavailable on this platform, fallback to pipe mode."
                runtime_note = f"{runtime_note}\n{extra}".strip()
        self._start_run(
            request=request,
            argv=argv,
            mode=mode,
            runtime_note=runtime_note,
        )

    def _start_run(
        self,
        *,
        request: CommandRequest,
        argv: list[str],
        mode: str,
        runtime_note: str,
    ) -> None:
        runner = self._make_runner(mode)
        record = RunRecord(request=request, argv=argv, mode=mode)
        record.runtime_note = runtime_note
        record.status = RunStatus.RUNNING
        managed = ManagedProcess(record=record, runner=runner, started=True)
        self.state.active_process = managed
        self.state.register_run(record)

        self.open_output_screen()

        task = asyncio.create_task(self._drive_process(managed))
        managed.task = task
        self._process_tasks.add(task)
        task.add_done_callback(self._process_tasks.discard)
        self.refresh_status_bars()

    async def _drive_process(self, managed: ManagedProcess) -> None:
        bridge = _RunnerBridge(self, managed.record)
        try:
            await managed.runner.run(managed.record.argv, bridge)
        except Exception as exc:
            managed.record.status = RunStatus.ERROR
            managed.record.exit_code = -1
            managed.record.finished_at = datetime.now()
            note = managed.record.runtime_note.strip()
            managed.record.runtime_note = f"{note}\nRunner error: {exc}".strip()
            if self.state.active_process is managed:
                self.state.active_process = None
            if self._output_screen is not None:
                self._output_screen.refresh_status()
            self.notify(f"Runner error: {exc}", severity="error")
            self.refresh_status_bars()

    def handle_process_output(
        self,
        record: RunRecord,
        stream: str,
        text: str,
    ) -> None:
        record.append_output(stream, text)
        if self._output_screen is not None:
            self._output_screen.append_output(stream, text)

    def handle_process_exit(
        self,
        record: RunRecord,
        exit_code: int | None,
        status: RunStatus,
    ) -> None:
        record.exit_code = exit_code
        record.status = status
        record.finished_at = datetime.now()
        if self.state.active_process and self.state.active_process.record is record:
            self.state.active_process = None
        if self._output_screen is not None:
            self._output_screen.refresh_status()
        self.refresh_status_bars()

    def rerun_last_command(self) -> None:
        if self.state.active_process and self.state.active_process.record.is_running:
            self.notify("Stop the current process before rerun.", severity="warning")
            return
        record = self.state.last_run
        if record is None:
            self.notify("Nothing to rerun yet.", severity="warning")
            return
        self._rerun_record(record)

    def _rerun_record(self, record: RunRecord) -> None:
        request = CommandRequest(
            title=record.request.title,
            subcommand=record.request.subcommand,
            args=list(record.request.args),
            interactive=record.mode == "pty",
            note=record.request.note,
        )
        self._start_run(
            request=request,
            argv=record.argv.copy(),
            mode=record.mode,
            runtime_note=record.request.note,
        )

    def request_copy_command(self) -> None:
        record = self.current_record()
        if record is None:
            self.notify("No command to copy.", severity="warning")
            return
        self.copy_to_clipboard(record.command_text)
        self.notify("Command copied to clipboard.")

    def request_stop_active_process(self) -> None:
        active = self.state.active_process
        if active is None:
            self.notify("No active process.", severity="warning")
            return
        asyncio.create_task(active.runner.stop())

    def request_send_stdin(self, text: str) -> None:
        active = self.state.active_process
        if active is None:
            self.notify("No active process.", severity="warning")
            return
        asyncio.create_task(active.runner.write_stdin(text))

    def select_profile(self, profile_id: str) -> None:
        self.state.set_profile(profile_id)
        self.refresh_status_bars()

    @staticmethod
    def _make_runner(mode: str) -> BaseProcessRunner:
        if mode == "pty":
            return PtyRunner()
        return PipeRunner()
