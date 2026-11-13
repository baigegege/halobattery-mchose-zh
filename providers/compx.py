"""MCHOSE / Compx 2.4G receiver (3554:fa09) — the 20-byte bidirectional protocol.

Why this file exists
--------------------
The receiver exposes several HID collections on Windows. Exactly one of them is the
control channel: the one with usage page 0xFF02.

    Input     20 bytes
    Output    20 bytes
    Feature    0 bytes          <- so any feature-report approach is doomed here

Every earlier attempt on this device (this project's first MCHOSE provider, and the
community projects we compared against) spoke feature reports, and therefore found
nothing but static frames. The real command goes out as an *output* report with
report id 0x13.

Frame layout
------------
    [0]      0x13              report id
    [1]      command
    [2]      subcommand / fragment count
    [3]      fragment index
    [4..18]  15-byte payload
    [19]     sum(frame[0:19]) & 0xFF

Commands measured on a MCHOSE G75 3.0 through a 3554:fa09 receiver:

    0x07  link state   -> 13 07 01 00 01 <online> ...      online 1 / switched off 0
    0x4A  battery      -> 13 4A 01 00 02 <level> <state> ...
    0x44  RGB config, 10 fragments
    0x41  macro table, 36 fragments
    0x42  key map,     27 fragments
    0x43  config block, 37 fragments
    0x49  colour palette, 35 fragments

How the battery read was proven
-------------------------------
    keyboard on   -> 0x4A answers 64 (100 %)
    keyboard off  -> 0x4A answers nothing at all
    keyboard on   -> 0x4A answers 64 again

The 0x07 reply's byte 5 flipped from 1 to 0 across the same power cycle, so the link
is live and the level comes from the keyboard, not from a receiver-side cache or a
hard-coded placeholder. (A placeholder would keep answering 100 % while the keyboard
was off; this one went silent.)

The receiver is a single USB node that carries both keyboard and mouse collections,
but only the keyboard answers 0x4A. The mouse level comes from a separate SINO WEALTH
258a receiver and is handled by providers/sino.py.

Long-term check (2026-11-12, two weeks after the first read)
-----------------------------------------------------------
    2026-10-29  0x4A returned 0x64 = 100 %
    2026-11-12  0x4A returned 0x55 =  85 %, three consecutive reads

A hard-coded placeholder cannot drift by 15 points, so byte 5 is a real level.
The keyboard was running on battery, unplugged, for the whole interval.
"""
from __future__ import annotations

import time
from dataclasses import replace
from typing import List, Optional

import hid

from . import hidlist
from .base import DeviceStatus, Provider, hexdump, log

VID = 0x3554
PID = 0xFA09
CONTROL_USAGE_PAGE = 0xFF02

RID = 0x13
FRAME_LEN = 20
CMD_LINK = 0x07
CMD_BATTERY = 0x4A

# A sleeping keyboard does not answer at all; give it a moment before giving up.
REPLY_TIMEOUT = 0.45
DRAIN_ROUNDS = 60


def _checksum(frame: bytes) -> int:
    return sum(frame[:FRAME_LEN - 1]) & 0xFF


def make_frame(cmd: int, sub: int = 0x01, seq: int = 0) -> bytes:
    frame = bytearray(FRAME_LEN)
    frame[0] = RID
    frame[1] = cmd
    frame[2] = sub
    frame[3] = seq
    frame[FRAME_LEN - 1] = _checksum(frame)
    return bytes(frame)


class CompxProvider(Provider):
    """Battery of a MCHOSE keyboard behind the Compx 2.4 GHz receiver."""

    name = "compx"

    def __init__(self) -> None:
        self._diag: List[str] = []
        self._last: Optional[DeviceStatus] = None

    # ------------------------------------------------------------------ helpers
    def _collection(self) -> Optional[dict]:
        for d in hidlist.enumerate(VID):
            if d.get("vendor_id") != VID or d.get("product_id") != PID:
                continue
            if (d.get("usage_page") or 0) == CONTROL_USAGE_PAGE:
                return d
        return None

    @staticmethod
    def _drain(dev) -> None:
        for _ in range(DRAIN_ROUNDS):
            try:
                chunk = dev.read(64)
            except Exception:
                return
            if not chunk or not any(chunk):
                return

    def _ask(self, dev, cmd: int) -> Optional[bytes]:
        """Send one command and return the matching reply, or None."""
        self._drain(dev)
        request = make_frame(cmd)
        try:
            written = dev.write(request)
        except Exception as e:
            self._diag.append(f"[Compx] 命令 0x{cmd:02x} 写失败: {e}")
            return None
        if not written or written <= 0:
            self._diag.append(f"[Compx] 命令 0x{cmd:02x} 被拒 (n={written})")
            return None

        deadline = time.time() + REPLY_TIMEOUT
        while time.time() < deadline:
            try:
                chunk = dev.read(64)
            except Exception:
                chunk = None
            if chunk and any(chunk):
                reply = bytes(chunk)
                if reply != request and len(reply) >= 3 \
                        and reply[0] == RID and reply[1] == cmd:
                    return reply
            time.sleep(0.005)
        return None

    # --------------------------------------------------------------------- poll
    def poll(self) -> List[DeviceStatus]:
        self._diag = []
        entry = self._collection()
        if entry is None:
            return []

        dev = hid.device()
        try:
            dev.open_path(entry["path"])
        except Exception as e:
            self._diag.append(f"[Compx] 打开接收器失败: {e}")
            return []
        try:
            dev.set_nonblocking(True)

            online = True
            link = self._ask(dev, CMD_LINK)
            if link is not None and len(link) >= 6:
                online = link[5] != 0
            else:
                self._diag.append("[Compx] 0x07 无回应，按在线处理")

            reply = self._ask(dev, CMD_BATTERY)
            if reply is None or len(reply) < 6:
                self._diag.append("[Compx] 0x4A 无回应（键盘已休眠或关机）")
                if self._last is not None:
                    self._last = replace(self._last, online=False)
                    return [self._last]
                return []

            level = min(100, max(0, reply[5]))
            status = DeviceStatus(
                key="compx:keyboard",
                name="MCHOSE 键盘（2.4G）",
                level=level,
                charging=False,
                online=online,
                source="compx",
                kind="keyboard",
                wake_on_input=True,
            )
            self._last = status
            self._diag.append(
                f"[Compx] 键盘 {level}%，在线={online}，原始帧 {hexdump(reply, 20)}")
            return [status]
        finally:
            try:
                dev.close()
            except Exception:
                pass

    def diagnostics(self) -> List[str]:
        return list(self._diag)
