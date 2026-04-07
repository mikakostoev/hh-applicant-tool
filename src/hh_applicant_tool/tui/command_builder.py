from __future__ import annotations

import sys
from pathlib import Path
from typing import Iterable

from .state import AppState, CommandRequest

ADVANCED_COMMAND_OPTIONS: list[tuple[str, str]] = [
    ("whoami", "whoami"),
    ("list-resumes", "list-resumes"),
    ("apply-vacancies", "apply-vacancies"),
    ("reply-employers", "reply-employers"),
    ("settings", "settings"),
    ("config", "config"),
    ("refresh-token", "refresh-token"),
    ("update-resumes", "update-resumes"),
    ("clear-skipped", "clear-skipped"),
    ("test-session", "test-session"),
    ("logout", "logout"),
    ("check-proxy", "check-proxy"),
    ("create-resume", "create-resume"),
    ("clone-resume", "clone-resume"),
    ("authorize", "authorize"),
    ("query", "query"),
    ("migrate-db", "migrate-db"),
    ("call-api", "call-api"),
    ("log", "log"),
    ("Custom command", "__custom__"),
]

TTY_SENSITIVE_COMMANDS = {
    "authorize",
    "auth",
    "authenticate",
    "login",
    "query",
    "sql",
    "migrate-db",
    "migrate",
    "reply-employers",
    "reply-empls",
    "reply-chats",
    "reall",
}


class CommandBuilder:
    def __init__(self, state: AppState, *, verbosity: int = 0):
        self._state = state
        self._verbosity = verbosity

    def build(self, request: CommandRequest) -> list[str]:
        argv = [sys.executable, "-m", "hh_applicant_tool"]

        if self._verbosity > 0:
            argv.append("-" + "v" * self._verbosity)

        if self._state.config_dir_override is not None:
            argv.extend(["--config-dir", str(self._state.config_root)])

        if self._state.selected_profile_id:
            argv.extend(["--profile-id", self._state.selected_profile_id])

        argv.append(request.subcommand.strip())
        argv.extend(request.args)
        return argv

    @staticmethod
    def add_value(
        target: list[str],
        flag: str,
        value: str | int | float | Path | None,
    ) -> None:
        if value is None:
            return
        text = str(value).strip()
        if not text:
            return
        target.extend([flag, text])

    @staticmethod
    def add_bool(target: list[str], flag: str, enabled: bool) -> None:
        if enabled:
            target.append(flag)

    @staticmethod
    def add_multi_values(
        target: list[str],
        flag: str,
        values: Iterable[str],
    ) -> None:
        cleaned = [value.strip() for value in values if value.strip()]
        if not cleaned:
            return
        target.append(flag)
        target.extend(cleaned)

    @staticmethod
    def split_multiline(text: str) -> list[str]:
        return [line.strip() for line in text.splitlines() if line.strip()]

    @staticmethod
    def command_options() -> list[tuple[str, str]]:
        return ADVANCED_COMMAND_OPTIONS.copy()

    @staticmethod
    def is_tty_sensitive(subcommand: str) -> bool:
        return subcommand.strip() in TTY_SENSITIVE_COMMANDS
