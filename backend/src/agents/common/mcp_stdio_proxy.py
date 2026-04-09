"""Proxy stdio MCP server output and filter non-JSON lines.

This wrapper is used for MCP servers that accidentally print plain logs to stdout
in stdio mode. MCP protocol requires stdout to contain JSON-RPC messages only.
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from typing import BinaryIO


def _is_jsonrpc_line(raw_line: bytes) -> bool:
    text = raw_line.decode("utf-8", errors="replace").strip()
    if not text:
        return False
    try:
        payload = json.loads(text)
    except Exception:
        return False
    return isinstance(payload, dict) and payload.get("jsonrpc") == "2.0"


def _pump_stdin_to_child(child_stdin: BinaryIO) -> None:
    try:
        while True:
            chunk = sys.stdin.buffer.read(8192)
            if not chunk:
                break
            child_stdin.write(chunk)
            child_stdin.flush()
    except BrokenPipeError:
        pass
    finally:
        try:
            child_stdin.close()
        except Exception:
            pass


def _pump_child_stdout_filtered(child_stdout: BinaryIO) -> None:
    while True:
        line = child_stdout.readline()
        if not line:
            break
        if _is_jsonrpc_line(line):
            sys.stdout.buffer.write(line)
            sys.stdout.buffer.flush()
        else:
            sys.stderr.write(f"[mcp-stdio-proxy] filtered non-json stdout: {line.decode('utf-8', errors='replace')}")
            sys.stderr.flush()


def _pump_child_stderr(child_stderr: BinaryIO) -> None:
    while True:
        chunk = child_stderr.read(8192)
        if not chunk:
            break
        sys.stderr.buffer.write(chunk)
        sys.stderr.buffer.flush()


def main() -> int:
    if len(sys.argv) < 2:
        sys.stderr.write("Usage: python -m src.agents.common.mcp_stdio_proxy <command> [args...]\n")
        return 2

    child_cmd = sys.argv[1:]
    child = subprocess.Popen(
        child_cmd,
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        bufsize=0,
    )

    assert child.stdin is not None
    assert child.stdout is not None
    assert child.stderr is not None

    t_in = threading.Thread(target=_pump_stdin_to_child, args=(child.stdin,), daemon=True)
    t_out = threading.Thread(target=_pump_child_stdout_filtered, args=(child.stdout,), daemon=True)
    t_err = threading.Thread(target=_pump_child_stderr, args=(child.stderr,), daemon=True)

    t_in.start()
    t_out.start()
    t_err.start()

    return_code = child.wait()
    t_in.join(timeout=1)
    t_out.join(timeout=1)
    t_err.join(timeout=1)
    return return_code


if __name__ == "__main__":
    raise SystemExit(main())
