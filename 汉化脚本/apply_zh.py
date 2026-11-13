# -*- coding: utf-8 -*-
"""一次性汉化 Halo Battery 界面文案。
对目标文件做精确的整串替换；每处 old 必须存在且目标中文不应已存在（幂等保护）。
仅改面向用户的字符串，不动代码逻辑、变量名、config 键名。
"""
import io
import sys

ROOT = "."

# 每个文件一组 (old, new)
REPLACEMENTS = {
    "halo_battery.pyw": [
        # 设备类型（偏好设置 > 设备类型）
        ('8BitDo controllers', '8BitDo 手柄'),
        ('"AM Infinity 8K (Angry Miao)"', '"AM Infinity 8K（怒喵）"'),
        ('"Astro A50"', '"Astro A50"'),
        ('"ASUS ROG / TUF mice"', '"华硕 ROG / TUF 鼠标"'),
        ('"Audeze Maxwell"', '"Audeze Maxwell"'),
        ('"Razer Barracuda Pro"', '"雷蛇 Barracuda Pro"'),
        ('"Corsair headsets"', '"海盗船 耳机"'),
        ('"G-Wolves mice"', '"G-Wolves 鼠标"'),
        ('"HyperX Cloud II Wireless"', '"HyperX Cloud II 无线"'),
        ('"HyperX Cloud Alpha 2"', '"HyperX Cloud Alpha 2"'),
        ('"HyperX Cloud III Wireless, Cloud II Core Wireless"', '"HyperX Cloud III 无线、Cloud II Core 无线"'),
        ('"HyperX Cloud III S Wireless"', '"HyperX Cloud III S 无线"'),
        ('"JBL Quantum"', '"JBL Quantum"'),
        ('"Keychron"', '"Keychron"'),
        ('"LAMZU mice"', '"LAMZU 鼠标"'),
        ('"Lofree keyboards"', '"Lofree 键盘"'),
        ('"Logitech"', '"罗技"'),
        ('"Logitech G PRO X 2 LIGHTSPEED"', '"罗技 G PRO X 2 LIGHTSPEED"'),
        ('"MCHOSE mice"', '"MCHOSE 鼠标"'),
        ('"Nintendo Switch controllers"', '"任天堂 Switch 手柄"'),
        ('"NZXT mice"', '"NZXT 鼠标"'),
        ('"PlayStation controllers"', '"PlayStation 手柄"'),
        ('"Pulsar / ATK VXE mice"', '"Pulsar / ATK VXE 鼠标"'),
        ('"Razer mice and headsets"', '"雷蛇 鼠标与耳机"'),
        ('"Steam Controller (2025)"', '"Steam 手柄（2025）"'),
        ('"SteelSeries"', '"赛睿"'),
        ('"SteelSeries Arctis Nova Elite"', '"赛睿 Arctis Nova Elite"'),
        ('"WLmouse"', '"WLmouse"'),
        ('"Xbox-compatible controllers"', '"Xbox 兼容手柄"'),

        # 图标类型选项
        ('("", "Automatic")', '("", "自动")'),
        ('("mouse", "Mouse")', '("mouse", "鼠标")'),
        ('("keyboard", "Keyboard")', '("keyboard", "键盘")'),
        ('("headset", "Headset")', '("headset", "耳机")'),
        ('("gamepad", "Controller")', '("gamepad", "手柄")'),
        ('("bluetooth", "Bluetooth")', '("bluetooth", "蓝牙")'),

        # 轮询间隔 / 主题 / 低电量档位标签
        ('"15 s"', '"15 秒"'), ('"30 s"', '"30 秒"'),
        ('"1 min"', '"1 分钟"'), ('"2 min"', '"2 分钟"'), ('"5 min"', '"5 分钟"'),
        ('"Automatic"', '"自动"'), ('"White"', '"白色"'), ('"Black"', '"黑色"'),
        ('"Off"', '"关闭"'),

        # 设备子菜单 / 偏好设置菜单项
        ('"Rename\u2026"', '"重命名\u2026"'),
        ('"Reset name"', '"重置名称"'),
        ('"Icon"', '"图标"'),
        ('"Low battery alert at"', '"低电量提醒阈值"'),
        ('"Hide this device"', '"隐藏此设备"'),
        ('"Poll interval"', '"轮询间隔"'),
        ('"Low battery alert"', '"低电量提醒"'),
        ('"Alert when fully charged"', '"充满电时提醒"'),
        ('"Estimated time left"', '"剩余续航估算"'),
        ('"Quiet while gaming"', '"游戏时静默"'),
        ('"Sound with the low battery alert"', '"低电量提醒时播放声音"'),
        ('"Keep disconnected devices until restart"', '"断连设备保留到重启"'),
        ('"Windows Bluetooth devices"', '"Windows 蓝牙设备"'),
        ('"PlayStation full mode (Bluetooth)"', '"PlayStation 完整模式（蓝牙）"'),
        ('"Device types"', '"设备类型"'),
        ('"Device pictogram"', '"设备图标"'),
        ('"Percentage in the icon"', '"图标内显示百分比"'),
        ('"Charging animation"', '"充电动画"'),
        ('"Icon colour"', '"图标颜色"'),
        ('"Status file for other apps"', '"为其他应用输出状态文件"'),
        ('"Start with Windows"', '"开机自启动"'),
        ('"Check for updates"', '"检查更新"'),
        ('"Check for updates now"', '"立即检查更新"'),
        ('"Refresh now"', '"立即刷新"'),
        ('"Preferences"', '"偏好设置"'),
        ('"Hidden devices"', '"已隐藏设备"'),
        ('"Diagnostics\u2026"', '"诊断\u2026"'),
        ('f"Exit (v{VERSION})"', 'f"\u9000\u51fa\uff08v{VERSION}\uff09"'),
        ('f"Show {name}"', 'f"\u663e\u793a {name}"'),

        # 无设备标题
        ('f"No devices shown ({hidden} hidden)"', 'f"\u65e0\u8bbe\u5907\u663e\u793a\uff08\u5df2\u9690\u85cf {hidden} \u4e2a\uff09"'),
        ('"No devices found"', '"未找到设备"'),

        # 默认低电量提示文字
        ('f"Default ({low}%)" if low else "Default (off)"', 'f"\u9ed8\u8ba4\uff08{low}%\uff09" if low else "\u9ed8\u8ba4\uff08\u5173\u95ed\uff09"'),

        # 通知文案
        ('"battery is low"', '"电量偏低"'),
        ('f"{level}% left"', 'f"\u5269\u4f59 {level}%"'),
        ('f"{name}: {left}. Time to charge."', 'f"{name}\uff1a{left}\uff0c\u8bf7\u5145\u7535\u3002"'),
        ('f"{name} is fully charged."', 'f"{name} \u5df2\u5145\u6ee1\u7535\u3002"'),
        ('f"Update to v{latest}"', 'f"\u66f4\u65b0\u81f3 v{latest}"'),
        ('f"Download v{latest}\u2026"', 'f"\u4e0b\u8f7d v{latest}\u2026"'),
        ('f"Version {latest} is available. Right-click a battery icon "',
         'f"\u53d1\u73b0\u65b0\u7248\u672c {latest}\u3002\u8bf7\u53f3\u952e\u70b9\u51fb\u7535\u91cf\u56fe\u6807\uff0c"'),
        ('f"and choose \\"{action}\\"."', 'f"\u9009\u62e9\u300c{action}\u300d\u3002"'),
        ('f"Downloading v{latest}\u2026 {progress}%"', 'f"\u6b63\u5728\u4e0b\u8f7d v{latest}\u2026 {progress}%"'),

        # 设备状态（tooltip）
        ('"no link (off or asleep)"', '"无连接（已关闭或休眠）"'),
        ('", charging"', '"，充电中"'),
        ('" (last known value, device asleep)"', '"（最后已知值，设备休眠）"'),

        # 临时文件夹提示
        ('TEMP_AUTOSTART_TEXT = ("Halo Battery is running from a temporary folder (straight from the ZIP). "',
         'TEMP_AUTOSTART_TEXT = ("Halo Battery 正从临时文件夹运行（直接从 ZIP 解压）。"'),
        ('"Extract the ZIP to a folder of its own, run HaloBattery.exe from there, "',
         '"请将 ZIP 解压到独立文件夹，从该文件夹运行 HaloBattery.exe，"'),
        ('"then turn on Start with Windows."', '"再开启「开机自启动」。")'),

        # 重命名输入框
        ("'New name for this device:'", "'该设备的新名称：'"),
        ("'Halo Battery - Rename'", "'Halo Battery - 重命名'"),
    ],

    "halo/whatsnew.py": [
        ('text="What\'s new"', 'text="更新内容"'),
        ('"Got it"', '"知道了"'),
        ('"Full release notes"', '"完整更新日志"'),
        ('f"Updated from {from_version}"', 'f"\u4ece {from_version} \u66f4\u65b0"'),
        ('"The release notes could not be loaded. They are on the release page."',
         '"无法加载更新日志，请前往发布页面查看。"'),
    ],

    "halo/history.py": [
        ('"less than 1 h of use left"', '"可用不到 1 小时"'),
        ('f"about {round(hours)} h of use left"', 'f"\u7ea6\u53ef\u7528 {round(hours)} \u5c0f\u65f6"'),
        ('f"about {round(hours / 24)} days of use left"', 'f"\u7ea6\u53ef\u7528 {round(hours / 24)} \u5929"'),
    ],

    "providers/asus.py": [
        ('f"about {level}%"', 'f"\u7ea6 {level}%"'),
    ],
    "providers/steelseries.py": [
        ('f"about {level}%"', 'f"\u7ea6 {level}%"'),
    ],
    "providers/logitech.py": [
        ('(90, "full")', '(90, "满电")'),
        ('(50, "good")', '(50, "良好")'),
        ('(20, "low")', '(20, "偏低")'),
        ('(5, "critical")', '(5, "极低")'),
        ('f"about {level}% ({word})"', 'f"\u7ea6 {level}%（{word}）"'),
    ],
    "providers/nintendo.py": [
        ('{8: "full", 6: "medium", 4: "low", 2: "critical", 0: "empty"}',
         '{8: "满电", 6: "中等", 4: "偏低", 2: "极低", 0: "耗尽"}'),
        ('f"about {pct}% ({LEVEL_NAMES[level]})"', 'f"\u7ea6 {pct}%（{LEVEL_NAMES[level]}）"'),
    ],
    "providers/xinput.py": [
        ('    0: (5, "empty"),\n    1: (20, "low"),\n    2: (55, "medium"),\n    3: (100, "full"),\n',
         '    0: (5, "耗尽"),\n    1: (20, "偏低"),\n    2: (55, "中等"),\n    3: (100, "满电"),\n'),
        ('f"about {pct}% ({text})"', 'f"\u7ea6 {pct}%（{text}）"'),
        ('"connected, battery level not reported yet"', '"已连接，电量未上报"'),
    ],
    "providers/audeze.py": [
        ('"no answer from the headset - unplug the dongle and plug it back in"',
         '"耳机无响应——请拔下接收器再重新插入"'),
        ('"connected, battery level not reported yet"', '"已连接，电量未上报"'),
    ],
    "providers/playstation.py": [
        ('"connected, battery level not reported yet"', '"已连接，电量未上报"'),
    ],
    "providers/steam.py": [
        ('"connected, battery level not reported yet"', '"已连接，电量未上报"'),
    ],
}

def apply_to_file(path, pairs):
    with io.open(path, "r", encoding="utf-8") as f:
        text = f.read()
    for old, new in pairs:
        n = text.count(old)
        if n == 0:
            print(f"  [WARN] 未命中: {path}  <- {old!r}")
            continue
        if new in text:
            print(f"  [SKIP] 目标已存在（可能重复应用）: {path}  <- {old!r}")
            continue
        text = text.replace(old, new)
        print(f"  [OK ] 替换 {n} 处: {old!r}")
    with io.open(path, "w", encoding="utf-8") as f:
        f.write(text)

def main():
    for path, pairs in REPLACEMENTS.items():
        full = ROOT + "/" + path
        print(f"== {path} ==")
        try:
            apply_to_file(full, pairs)
        except FileNotFoundError:
            print(f"  [ERR ] 文件不存在: {full}")

if __name__ == "__main__":
    main()
