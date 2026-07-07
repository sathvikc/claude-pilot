#!/usr/bin/env python3
# Vendored from https://github.com/FabianWesner/claude-code-codex-skill (commit 0250cfc)
# MIT License, Copyright (c) 2026 Fabian Wesner.
# Modifications by Pilot: bounded JSON-RPC request deadlines with per-call
# terminate opt-out (child terminated+reaped only when nothing useful survives);
# CODEX_BIN env resolution; failed-turn handling (turn/failed clears the active
# turn and surfaces the error in result.txt); startup/turn-command errors surfaced
# to progress.log instead of crashing the daemon silently; item/completed result
# fallback (mirrors the one-shot client); control-file offset captured at launch
# so commands appended before READY are not lost; serialized stdin writes;
# process-group spawn + group-wide reap (no orphaned tool subprocesses);
# SIGTERM/SIGINT shutdown handlers; UTF-8 pipe encoding; lint reformatting
# + charset normalization.
# pyright: reportOptionalMemberAccess=false, reportOptionalIterable=false
"""Interactive Codex session daemon (app-server) - lets an orchestration agent drive Codex as a
mid-flight-steerable sub-agent. Runs on the ChatGPT subscription (no API key).

Fire-and-wait `codex exec` can't be corrected once running. This daemon holds ONE
app-server thread and exposes a file-based control plane that fits how an agent works:
  - the agent APPENDS line-commands to <dir>/control
  - the daemon STREAMS Codex's live activity to <dir>/progress.log (tail it with Monitor)
  - final answers land in <dir>/result.txt (a failed turn writes "[turn failed] <error>")

Control commands (one per line, appended to <dir>/control):
  turn: <prompt>   start a new turn
  steer: <text>    inject text into the ACTIVE turn (mid-flight correction)
  interrupt        stop the active turn
  status           dump state to <dir>/status.json
  quit             shut down

Usage:
  codex_session.py --dir <session-dir> --cwd <repo> [--model gpt-5.5] [--effort xhigh]
                   [--sandbox read-only|workspace-write] [--prompt "<first turn>"]
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import threading
import time


class Conn:
    def __init__(self, on_note):
        self.p = subprocess.Popen(
            [os.environ.get("CODEX_BIN", "codex"), "app-server"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            encoding="utf-8",
            errors="replace",
            bufsize=1,
            start_new_session=True,
        )
        self._id = 0
        self._resp = {}
        self._lock = threading.Lock()
        self._wlock = threading.Lock()
        self._on_note = on_note
        threading.Thread(target=self._reader, daemon=True).start()

    def _reap(self):
        # start_new_session=True gave the child its own process group, so signal
        # the GROUP: the app-server's own tool subprocesses must not be orphaned
        try:
            pgid = os.getpgid(self.p.pid)
        except Exception:
            pgid = None
        try:
            os.killpg(pgid, signal.SIGTERM) if pgid is not None else self.p.terminate()
            self.p.wait(timeout=5)
        except Exception:
            try:
                os.killpg(pgid, signal.SIGKILL) if pgid is not None else self.p.kill()
                self.p.wait(timeout=5)
            except Exception:
                pass

    def _send(self, m):
        with self._wlock:
            self.p.stdin.write(json.dumps(m) + "\n")
            self.p.stdin.flush()

    def request(
        self, method: str, params: dict | None = None, deadline: float = 60.0, terminate_on_timeout: bool = True
    ):
        with self._lock:
            self._id += 1
            rid = self._id
        self._send({"id": rid, "method": method, "params": params or {}})
        # bounded wait - a live but silent app-server fails loud instead of hanging.
        # terminate_on_timeout=False lets secondary requests (steer/interrupt) give up
        # without destroying the shared server and its active turn.
        start = time.monotonic()
        while rid not in self._resp:
            if self.p.poll() is not None:
                raise RuntimeError("app-server exited")
            if time.monotonic() - start >= deadline:
                if terminate_on_timeout:
                    self._reap()
                    raise RuntimeError(f"{method}: no response within {deadline}s; app-server terminated")
                raise RuntimeError(f"{method}: no response within {deadline}s; app-server left running")
            time.sleep(0.02)
        r = self._resp.pop(rid)
        if "error" in r:
            raise RuntimeError(f"{method}: {r['error']}")
        return r.get("result", {})

    def notify(self, method, params=None):
        self._send({"method": method, "params": params or {}})

    def _reader(self):
        for line in self.p.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                m = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "id" in m and ("result" in m or "error" in m):
                self._resp[m["id"]] = m
            elif "method" in m:
                self._on_note(m.get("method"), m.get("params") or {}, m.get("id"))


class Session:
    def __init__(self, a):
        self.a = a
        self.dir = a.dir
        os.makedirs(self.dir, exist_ok=True)
        self.ctl = os.path.join(self.dir, "control")
        self.log_path = os.path.join(self.dir, "progress.log")
        open(self.ctl, "a").close()
        # snapshot NOW (not after the multi-second startup) so commands appended
        # between daemon launch and READY are processed, not silently skipped
        self.ctl_off = os.path.getsize(self.ctl)
        self.logf = open(self.log_path, "a", buffering=1)
        self.turn_id = None
        self.buf = []
        self.turns_done = 0
        self.conn = Conn(self._on_note)

    def log(self, s):
        self.logf.write(s + "\n")

    def _on_note(self, method, params, req_id):
        if method == "turn/started":
            self.turn_id = (params.get("turn") or {}).get("id")
            self.buf = []
            self.log(f"[turn started id={self.turn_id}]")
        elif method and method.endswith("/delta") and "delta" in params:
            self.buf.append(params["delta"])
            self.logf.write(params["delta"])
        elif method == "item/started":
            it = params.get("item") or {}
            desc = it.get("command") or it.get("text") or it.get("type") or ""
            if isinstance(desc, list):
                desc = " ".join(map(str, desc))
            if desc:
                self.log(f"\n[item {it.get('type', '?')}] {str(desc)[:200]}")
        elif method == "item/completed":
            it = params.get("item") or {}
            if not self.buf and isinstance(it.get("text"), str):
                self.buf.append(it["text"])
        elif method == "turn/completed":
            final = "".join(self.buf).strip()
            with open(os.path.join(self.dir, "result.txt"), "w") as f:
                f.write(final)
            self.turns_done += 1
            self.turn_id = None
            self.log(f"\n[turn complete -> result.txt, {len(final)} chars]")
        elif method == "turn/failed" or (params.get("error") and method and method.startswith("turn/")):
            err = params.get("error")
            with open(os.path.join(self.dir, "result.txt"), "w") as f:
                f.write(f"[turn failed] {err}")
            self.turn_id = None
            self.log(f"\n[turn FAILED: {err}]")
        elif req_id is not None:
            self.conn._send({"id": req_id, "result": {}})

    def status(self):
        with open(os.path.join(self.dir, "status.json"), "w") as f:
            json.dump(
                {"thread": self.thread, "active_turn": self.turn_id, "turns_completed": self.turns_done},
                f,
            )

    def start_turn(self, prompt):
        if self.turn_id:
            self.log("[reject turn: one already active]")
            return
        sb = (
            {"type": "readOnly", "networkAccess": False}
            if self.a.sandbox == "read-only"
            else {"type": "workspaceWrite"}
        )
        try:
            r = self.conn.request(
                "turn/start",
                {
                    "threadId": self.thread,
                    "input": [{"type": "text", "text": prompt}],
                    "model": self.a.model,
                    "effort": self.a.effort,
                    "sandboxPolicy": sb,
                },
            )
        except Exception as e:  # noqa
            self.log(f"\n[turn start FAILED: {e}]")
            return
        self.turn_id = (r.get("turn") or {}).get("id")

    def steer(self, text):
        if not self.turn_id:
            self.log("[reject steer: no active turn]")
            return
        try:
            self.conn.request(
                "turn/steer",
                {
                    "threadId": self.thread,
                    "expectedTurnId": self.turn_id,
                    "input": [{"type": "text", "text": text}],
                },
                terminate_on_timeout=False,
            )
            self.log(f"\n[STEER accepted -> {text[:80]}]")
        except Exception as e:  # noqa
            self.log(f"\n[steer rejected: {e}]")

    def interrupt(self):
        if self.turn_id:
            try:
                self.conn.request(
                    "turn/interrupt",
                    {"threadId": self.thread, "turnId": self.turn_id},
                    terminate_on_timeout=False,
                )
                self.log("\n[interrupt sent]")
            except Exception as e:  # noqa
                self.log(f"\n[interrupt failed: {e}]")

    def run(self):
        try:
            self.conn.request("initialize", {"clientInfo": {"name": "ask-codex-session", "version": "0.1.0"}})
            self.conn.notify("initialized")
            th = self.conn.request("thread/start", {"cwd": self.a.cwd, "approvalPolicy": "never"})
        except Exception as e:  # noqa
            self.log(f"[startup FAILED: {e}]")
            with open(os.path.join(self.dir, "result.txt"), "w") as f:
                f.write(f"[startup failed] {e}")
            self.conn._reap()
            return
        self.thread = (th.get("thread") or {}).get("id")
        self.log(f"[READY thread={self.thread} model={th.get('model')} sandbox={self.a.sandbox}]")
        self.status()
        if self.a.prompt:
            self.start_turn(self.a.prompt)
        # poll the control file for appended commands
        off = self.ctl_off
        while True:
            time.sleep(0.15)
            try:
                sz = os.path.getsize(self.ctl)
            except OSError:
                break
            if sz <= off:
                continue
            with open(self.ctl) as f:
                f.seek(off)
                new = f.read()
                off = f.tell()
            for raw in new.splitlines():
                cmd = raw.strip()
                if not cmd:
                    continue
                low = cmd.lower()
                if low.startswith("turn:"):
                    self.start_turn(cmd[5:].strip())
                elif low.startswith("steer:"):
                    self.steer(cmd[6:].strip())
                elif low == "interrupt":
                    self.interrupt()
                elif low == "status":
                    self.status()
                elif low == "quit":
                    self.log("[quit]")
                    self.conn._reap()
                    return


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", required=True)
    ap.add_argument("--cwd", default=os.getcwd())
    ap.add_argument("--model", default="gpt-5.5")
    ap.add_argument("--effort", default="xhigh")
    ap.add_argument("--sandbox", default="read-only", choices=["read-only", "workspace-write"])
    ap.add_argument("--prompt")
    sess = Session(ap.parse_args())

    def _shutdown(signum, _frame):
        # service shutdown must not orphan the app-server group
        sess.log(f"[signal {signum} -> shutdown]")
        sess.conn._reap()
        raise SystemExit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)
    try:
        sess.run()
    finally:
        sess.conn._reap()


if __name__ == "__main__":
    main()
