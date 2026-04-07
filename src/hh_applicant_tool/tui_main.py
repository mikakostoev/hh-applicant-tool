from __future__ import annotations

import sys


def main() -> int:
    try:
        from .tui.app import ApplicantToolTuiApp
    except ImportError as exc:
        if exc.name == "textual" or "textual" in str(exc):
            print(
                "The TUI requires the 'textual' dependency. Reinstall hh-applicant-tool with TUI support.",
                file=sys.stderr,
            )
            return 1
        raise

    app = ApplicantToolTuiApp()
    app.run()
    return 0
