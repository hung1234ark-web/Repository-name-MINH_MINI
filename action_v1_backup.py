import subprocess
import webbrowser
from datetime import datetime
from pathlib import Path


# =========================================================
# MINH MINI - ACTION ROUTER V1
# =========================================================

def open_google():
    webbrowser.open("https://www.google.com")
    return "Minh đã mở Google."


def open_youtube():
    webbrowser.open("https://www.youtube.com")
    return "Minh đã mở YouTube."


def open_calculator():
    subprocess.Popen(["calc.exe"])
    return "Minh đã mở Calculator."


def open_notepad():
    subprocess.Popen(["notepad.exe"])
    return "Minh đã mở Notepad."


def open_desktop():
    desktop = Path.home() / "Desktop"
    subprocess.Popen(["explorer.exe", str(desktop)])
    return "Minh đã mở Desktop."


def open_downloads():
    downloads = Path.home() / "Downloads"
    subprocess.Popen(["explorer.exe", str(downloads)])
    return "Minh đã mở Downloads."


def get_time():
    now = datetime.now()
    return f"Bây giờ là {now.strftime('%H:%M:%S')}."


def get_date():
    now = datetime.now()
    return f"Hôm nay là ngày {now.strftime('%d/%m/%Y')}."


# =========================================================
# ACTION COMMAND ROUTER
# =========================================================

def handle_action_command(message):
    text = message.strip()
    lower = text.lower()

    # GOOGLE
    google_commands = (
        "mở google",
        "mo google",
        "truy cập google",
        "truy cap google",
        "vào google",
        "vao google",
    )

    if lower in google_commands:
        return True, open_google()

    # YOUTUBE
    youtube_commands = (
        "mở youtube",
        "mo youtube",
        "mở ytb",
        "mo ytb",
        "truy cập youtube",
        "truy cap youtube",
        "vào youtube",
        "vao youtube",
    )

    if lower in youtube_commands:
        return True, open_youtube()

    # CALCULATOR
    calculator_commands = (
        "mở calculator",
        "mo calculator",
        "mở máy tính",
        "mo may tinh",
        "mở calc",
        "mo calc",
    )

    if lower in calculator_commands:
        return True, open_calculator()

    # NOTEPAD
    notepad_commands = (
        "mở notepad",
        "mo notepad",
        "mở ghi chú",
        "mo ghi chu",
    )

    if lower in notepad_commands:
        return True, open_notepad()

    # DESKTOP
    desktop_commands = (
        "mở desktop",
        "mo desktop",
        "mở màn hình desktop",
        "mo man hinh desktop",
    )

    if lower in desktop_commands:
        return True, open_desktop()

    # DOWNLOADS
    downloads_commands = (
        "mở downloads",
        "mo downloads",
        "mở thư mục downloads",
        "mo thu muc downloads",
        "mở tải xuống",
        "mo tai xuong",
    )

    if lower in downloads_commands:
        return True, open_downloads()

    # TIME
    time_commands = (
        "mấy giờ rồi",
        "may gio roi",
        "bây giờ mấy giờ",
        "bay gio may gio",
        "xem giờ",
        "xem gio",
        "giờ hiện tại",
        "gio hien tai",
    )

    if lower in time_commands:
        return True, get_time()

    # DATE
    date_commands = (
        "hôm nay ngày bao nhiêu",
        "hom nay ngay bao nhieu",
        "hôm nay ngày mấy",
        "hom nay ngay may",
        "xem ngày",
        "xem ngay",
        "xem ngày hôm nay",
        "xem ngay hom nay",
    )

    if lower in date_commands:
        return True, get_date()

    return False, None