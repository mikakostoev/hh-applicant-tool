from __future__ import annotations

import os
import shlex
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import TYPE_CHECKING

from ..constants import CONFIG_DIR, LOG_FILENAME

if TYPE_CHECKING:
    from .process_runner import BaseProcessRunner


class RunStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    CANCELLED = "cancelled"


@dataclass(slots=True)
class CommandRequest:
    title: str
    subcommand: str
    args: list[str] = field(default_factory=list)
    interactive: bool = False
    note: str = ""


@dataclass(slots=True)
class RunRecord:
    request: CommandRequest
    argv: list[str]
    mode: str
    status: RunStatus = RunStatus.PENDING
    exit_code: int | None = None
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: datetime | None = None
    stdout_chunks: list[str] = field(default_factory=list)
    stderr_chunks: list[str] = field(default_factory=list)
    merged_chunks: list[str] = field(default_factory=list)
    runtime_note: str = ""

    def append_output(self, stream: str, text: str) -> None:
        if stream == "stdout":
            self.stdout_chunks.append(text)
            self.merged_chunks.append(text)
            return
        if stream == "stderr":
            self.stderr_chunks.append(text)
            self.merged_chunks.append(text)
            return
        self.merged_chunks.append(text)

    @property
    def command_text(self) -> str:
        return shlex.join(self.argv)

    @property
    def is_running(self) -> bool:
        return self.status == RunStatus.RUNNING

    @property
    def has_output(self) -> bool:
        return bool(self.merged_chunks or self.stdout_chunks or self.stderr_chunks)


@dataclass(slots=True)
class ManagedProcess:
    record: RunRecord
    runner: BaseProcessRunner
    started: bool = False
    task: object | None = None


@dataclass(slots=True)
class AppState:
    run_history_limit: int = 20
    config_dir_override: Path | None = None
    selected_profile_id: str = field(
        default_factory=lambda: os.getenv("HH_PROFILE_ID") or "."
    )
    last_run: RunRecord | None = None
    active_process: ManagedProcess | None = None
    run_history: list[RunRecord] = field(default_factory=list)

    @property
    def config_root(self) -> Path:
        root = self.config_dir_override
        if root is None:
            root = Path(os.getenv("CONFIG_DIR", str(CONFIG_DIR)))
        return Path(root).expanduser()

    @property
    def effective_profile_path(self) -> Path:
        return (self.config_root / (self.selected_profile_id or ".")).resolve()

    @property
    def log_path(self) -> Path:
        return self.effective_profile_path / LOG_FILENAME

    @property
    def active_record(self) -> RunRecord | None:
        if self.active_process:
            return self.active_process.record
        return self.last_run

    def register_run(self, record: RunRecord) -> None:
        self.last_run = record
        self.run_history.insert(0, record)
        del self.run_history[self.run_history_limit :]

    def list_profiles(self) -> list[str]:
        profiles = ["."]
        root = self.config_root
        if not root.exists():
            return profiles
        for child in sorted(root.iterdir(), key=lambda item: item.name.lower()):
            if child.is_dir() and child.name != ".":
                profiles.append(child.name)
        return profiles

    def set_profile(self, profile_id: str | None) -> None:
        self.selected_profile_id = profile_id or "."
