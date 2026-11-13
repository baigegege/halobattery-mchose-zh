# -*- coding: utf-8 -*-
"""不启动托盘程序，直接读一次键盘 + 鼠标的当前电量。

用途：装好 provider 之后快速核对读数，或排查「图标不出现」时确认设备层是否正常。

用法：
    python 快速核对电量.py
    python 快速核对电量.py "D:\\某个目录\\_internal"     # 手工指定 hid 模块所在目录

优先用本机 site-packages 里的 hidapi；找不到时，会依次尝试命令行参数、
环境变量 HALOBATTERY_INTERNAL、以及几个常见的打包目录。
"""
import os
import sys
import time

try:
    import hid
except ImportError:
    candidates = [
        sys.argv[1] if len(sys.argv) > 1 else "",
        os.environ.get("HALOBATTERY_INTERNAL", ""),
        r"E:\HaloBattery-zh\_internal",
    ]
    for path in candidates:
        if path and os.path.isdir(path):
            sys.path.insert(0, path)
            try:
                import hid
                break
            except ImportError:
                sys.path.pop(0)
    else:
        raise SystemExit(
            "找不到 hid 模块。请先 pip install hidapi，"
            "或把打包目录的 _internal 路径作为参数传进来。"
        )


def find(vid, pid, usage_page=0xFF02):
    for d in hid.enumerate():
        if (d["vendor_id"], d["product_id"]) == (vid, pid) \
                and (d.get("usage_page") or 0) == usage_page:
            return d
    return None


def read_keyboard():
    """3554:fa09 -> output report 0x13 -> 命令 0x4A -> 响应 byte5 = 电量%"""
    info = find(0x3554, 0xFA09)
    if not info:
        return "接收器 3554 ff02 不在"
    dev = hid.device()
    dev.open_path(info["path"])
    dev.set_nonblocking(True)

    frame = bytearray(20)
    frame[0], frame[1], frame[2], frame[3] = 0x13, 0x4A, 0x01, 0x00
    frame[19] = sum(frame[:19]) & 0xFF

    values = []
    for _ in range(3):
        for _ in range(60):                 # 排空残留 input
            if not dev.read(64):
                break
        if dev.write(frame) <= 0:
            values.append("写入被拒")
            continue
        reply = None
        deadline = time.time() + 1.2
        while time.time() < deadline:
            chunk = dev.read(64)
            if chunk and any(chunk):
                b = bytes(chunk)
                if len(b) >= 7 and b[0] == 0x13 and b[1] == 0x4A \
                        and b != bytes(frame):
                    reply = b
                    break
            time.sleep(0.005)
        values.append(f"{reply[5]}%" if reply else "无回应")
        time.sleep(0.3)
    dev.close()
    return "  ".join(values)


def read_mouse():
    """258a:0138 -> feature 0x09 -> 先发 09 0C 09 00 再读 -> byte8 = 电量%"""
    info = find(0x258A, 0x0138)
    if not info:
        return "接收器 258a ff02 不在"
    dev = hid.device()
    dev.open_path(info["path"])
    dev.set_nonblocking(True)

    cmd = bytearray(520)
    cmd[:4] = bytes([0x09, 0x0C, 0x09, 0x00])
    values = []
    for _ in range(3):
        try:
            dev.send_feature_report(cmd)
            time.sleep(0.2)
            res = dev.get_feature_report(0x09, 520)
            b = bytes(res) if res else b""
            values.append(f"{b[8]}%" if len(b) >= 9 else "无回应")
        except OSError:
            values.append("读取失败")
        time.sleep(0.4)
    dev.close()
    return "  ".join(values)


if __name__ == "__main__":
    print("时间:", time.strftime("%Y-%m-%d %H:%M:%S"))
    print("键盘 G75 (0x4A):", read_keyboard())
    print("鼠标 G3  (0x09):", read_mouse())
