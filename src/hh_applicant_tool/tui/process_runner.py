from __future__ import annotations

import asyncio
import os
import pty
import signal
from asyncio.subprocess import Process
from typing import Literal, Protocol

from .state import RunStatus

StreamName = Literal["stdout", "stderr", "merged"]

_STOP_TIMEOUT_SECONDS = 2.0


class ProcessCallbacks(Protocol):
    def on_output(self, stream: StreamName, text: str) -> None: ...

    def on_exit(self, exit_code: int | None, status: RunStatus) -> None: ...


class BaseProcessRunner:
    def __init__(self) -> None:
        self.process: Process | None = None
        self.stop_requested = False

    async def run(
        self,
        argv: list[str],
        callbacks: ProcessCallbacks,
    ) -> None:
        raise NotImplementedError

    async def write_stdin(self, text: str) -> None:
        raise NotImplementedError

    async def stop(self) -> None:
        if not self.process or self.process.returncode is not None:
            return

        self.stop_requested = True
        await self._interrupt_then_kill()

    async def _interrupt_then_kill(self) -> None:
        process = self.process
        if not process or process.returncode is not None:
            return

        self._signal_process(signal.SIGINT)
        try:
            await asyncio.wait_for(process.wait(), timeout=_STOP_TIMEOUT_SECONDS)
            return
        except asyncio.TimeoutError:
            pass

        self._signal_process(signal.SIGTERM)
        try:
            await asyncio.wait_for(process.wait(), timeout=_STOP_TIMEOUT_SECONDS)
            return
        except asyncio.TimeoutError:
            pass

        self._signal_process(signal.SIGKILL)
        try:
            await asyncio.wait_for(process.wait(), timeout=_STOP_TIMEOUT_SECONDS)
        except asyncio.TimeoutError:
            pass

    def _signal_process(self, sig: signal.Signals) -> None:
        process = self.process
        if not process or process.returncode is not None:
            return

        try:
            if os.name == "posix":
                os.killpg(process.pid, sig)
                return
        except ProcessLookupError:
            return
        except PermissionError:
            pass
        except Exception:
            pass

        try:
            process.send_signal(sig)
        except ProcessLookupError:
            return
        except Exception:
            if sig in {signal.SIGTERM, signal.SIGKILL}:
                process.kill()
            else:
                process.terminate()

    def _resolve_status(self, exit_code: int | None) -> RunStatus:
        if self.stop_requested:
            return RunStatus.CANCELLED
        return RunStatus.SUCCESS if exit_code == 0 else RunStatus.ERROR


class PipeRunner(BaseProcessRunner):
    async def run(
        self,
        argv: list[str],
        callbacks: ProcessCallbacks,
    ) -> None:
        kwargs = {}
        if os.name == "posix":
            kwargs["start_new_session"] = True

        self.process = await asyncio.create_subprocess_exec(
            *argv,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            **kwargs,
        )

        stdout_task = asyncio.create_task(
            self._read_stream(self.process.stdout, "stdout", callbacks)
        )
        stderr_task = asyncio.create_task(
            self._read_stream(self.process.stderr, "stderr", callbacks)
        )

        exit_code = await self.process.wait()
        await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)
        callbacks.on_exit(exit_code, self._resolve_status(exit_code))

    async def _read_stream(
        self,
        stream: asyncio.StreamReader | None,
        stream_name: StreamName,
        callbacks: ProcessCallbacks,
    ) -> None:
        if stream is None:
            return

        while True:
            chunk = await stream.read(4096)
            if not chunk:
                return
            callbacks.on_output(stream_name, chunk.decode(errors="replace"))

    async def write_stdin(self, text: str) -> None:
        process = self.process
        if not process or process.stdin is None or process.returncode is not None:
            return

        payload = text if text.endswith("\n") else f"{text}\n"
        process.stdin.write(payload.encode())
        try:
            await process.stdin.drain()
        except (BrokenPipeError, ConnectionResetError):
            return


class PtyRunner(BaseProcessRunner):
    def __init__(self) -> None:
        super().__init__()
        self._master_fd: int | None = None
        self._slave_fd: int | None = None

    async def run(
        self,
        argv: list[str],
        callbacks: ProcessCallbacks,
    ) -> None:
        if os.name != "posix":
            raise RuntimeError("PTY runner is supported only on POSIX systems.")

        self._master_fd, self._slave_fd = pty.openpty()

        try:
            self.process = await asyncio.create_subprocess_exec(
                *argv,
                stdin=self._slave_fd,
                stdout=self._slave_fd,
                stderr=self._slave_fd,
                start_new_session=True,
            )
        finally:
            if self._slave_fd is not None:
                os.close(self._slave_fd)
                self._slave_fd = None

        read_task = asyncio.create_task(self._read_master(callbacks))
        exit_code = await self.process.wait()
        await asyncio.gather(read_task, return_exceptions=True)
        callbacks.on_exit(exit_code, self._resolve_status(exit_code))
        self._close_master()

    async def _read_master(self, callbacks: ProcessCallbacks) -> None:
        master_fd = self._master_fd
        if master_fd is None:
            return

        while True:
            try:
                data = await asyncio.to_thread(os.read, master_fd, 4096)
            except OSError:
                return
            if not data:
                return
            callbacks.on_output("merged", data.decode(errors="replace"))

    async def write_stdin(self, text: str) -> None:
        if self._master_fd is None:
            return
        payload = text if text.endswith("\n") else f"{text}\n"
        await asyncio.to_thread(os.write, self._master_fd, payload.encode())

    def _close_master(self) -> None:
        if self._master_fd is None:
            return
        try:
            os.close(self._master_fd)
        except OSError:
            pass
        self._master_fd = None
