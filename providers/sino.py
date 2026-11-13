"""MCHOSE G3 and other SINO WEALTH (258a) 2.4 GHz mice — battery over feature 0x09.

Where the protocol came from
----------------------------
MCHOSE's own driver, MCHOSE HUB (a Qt5 application), keeps two artefacts we could read:
its log (`C:\\MCHOSE\\Log.txt`, every HID send/receive it performs) and its per-model
configuration templates (`C:\\MCHOSE\\Products\\G3\\G3_data.ini`). Those gave the frame
shape for this chip family:

    Keys = 09 6c 01 00 ...     0x6c = read key mapping
    Base = 09 6e 44 00 ...     0x6e = read lighting configuration

So the mouse speaks over report id 0x09, 520-byte *feature* reports, with the command
byte in position 1 — a different world from the Compx keyboard on 3554:fa09, which uses
a 20-byte output report with the command in position 1 of a 0x13 frame.

The battery command is not in either template, so it was found by probing read-shaped
candidates against the live device. The one that answers:

    send : 09 0C 09 00 + 516 zero bytes          (520 bytes total)
    read : 09 0C 09 00 00 00 00 00 <level>       (9 bytes returned)

`<level>` sits at byte 8 and is the battery percentage.

Two things this device forces
-----------------------------
* **The command must be sent before every read.** Feature 0x09 is a shared
  command/data buffer, not a register the host can just read. A plain
  get_feature_report() with no preceding command returns ``read error`` on a healthy,
  awake mouse — that is what made this look unsupported for so long. Any other command
  (e.g. reading the lighting config) overwrites the buffer, so each poll re-sends.
* **The mouse only answers while it is awake and on the 2.4 GHz link.** In Bluetooth
  mode its 2.4 GHz radio is off and the read fails; asleep, the same.

How the level was confirmed
---------------------------
    22:10  leftover buffer after the driver ran ... 0x54 = 84 %
    22:22  active query .......................... 0x55 = 85 %
    user's own Bluetooth reading .................       86 %
    22:39  active query, unplugged ............... 0x54 = 84 %

Eight rounds of "send + read three times" produced 24 samples, all 85 - stable within
a poll. The mouse was *not* charging; the 86 -> 85 -> 84 drift is discharge, and that
direction is the proof that byte 8 is live rather than a fixed placeholder.

Long-term check (2026-11-12, two weeks later): 100 %, consistent with the mouse having
been charged in between. The value moves in both directions, so it is not a one-way
counter either.
"""
from __future__ import annotations

import time
from dataclasses import replace
from typing import List, Optional

import hid

from . import hidlist
from .base import DeviceStatus, Provider, hexdump, log

VID = 0x258A
PID = 0x0138
USAGE_PAGE = 0xFF02

REPORT_ID = 0x09
REPORT_LEN = 520
LEVEL_INDEX = 8

# 09 0C 09 00 -> "report a status frame", then the rest is zero padding.
CMD_BATTERY = bytes([0x09, 0x0C, 0x09, 0x00])

REPLY_TIMEOUT = 0.35
ATTEMPTS = 3


class SinoProvider(Provider):
    """Battery of a MCHOSE mouse behind a SINO WEALTH 258a 2.4 GHz receiver."""

    name = "sino"

    def __init__(self) -> None:
        self._diag: List[str] = []
        self._last: Optional[DeviceStatus] = None

    # ------------------------------------------------------------------ helpers
    def _collection(self) -> Optional[dict]:
        for d in hidlist.enumerate(VID):
            if d.get("vendor_id") != VID:
                continue
            if (d.get("usage_page") or 0) == USAGE_PAGE:
                return d
        return None

    def _query(self, dev) -> Optional[int]:
        """Send the battery command and return the level, or None."""
        frame = bytearray(REPORT_LEN)
        frame[:len(CMD_BATTERY)] = CMD_BATTERY
        for attempt in range(ATTEMPTS):
            try:
                written = dev.send_feature_report(bytes(frame))
            except Exception as e:
                self._diag.append(f"[Sino] 第 {attempt + 1} 次写失败: {e}")
                time.sleep(0.05)
                continue
            if not written or written <= 0:
                self._diag.append(f"[Sino] 写被拒 (n={written})")
                continue
            time.sleep(0.12)
            try:
                reply = dev.get_feature_report(REPORT_ID, REPORT_LEN)
            except Exception as e:
                self._diag.append(f"[Sino] 第 {attempt + 1} 次读失败: {e}")
                continue
            if reply and len(reply) > LEVEL_INDEX:
                body = bytes(reply)
                self._diag.append(f"[Sino] 响应 {hexdump(body, 9)}")
                return min(100, max(0, body[LEVEL_INDEX]))
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
            self._diag.append(f"[Sino] 打开失败: {e}")
            return []
        try:
            try:
                dev.set_nonblocking(True)
            except Exception:
                pass

            level = self._query(dev)
            if level is None:
                self._diag.append("[Sino] 读不到电量（鼠标休眠、或在蓝牙模式）")
                if self._last is not None:
                    self._last = replace(self._last, online=False)
                    return [self._last]
                return []

            status = DeviceStatus(
                key="sino:mouse",
                name="MCHOSE 鼠标（2.4G）",
                level=level,
                charging=False,
                online=True,
                source="sino",
                kind="mouse",
                wake_on_input=True,
            )
            self._last = status
            return [status]
        finally:
            try:
                dev.close()
            except Exception:
                pass

    def diagnostics(self) -> List[str]:
        return list(self._diag)
