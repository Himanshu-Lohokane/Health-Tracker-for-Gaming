import time
import csv
from datetime import datetime
import os

try:
    import pygetwindow as gw
except ImportError:
    gw = None

try:
    import win32gui
    import win32process
    import psutil
except ImportError:
    win32gui = None
    win32process = None
    psutil = None

def get_foreground_app():
    if gw:
        win = gw.getActiveWindow()
        if win:
            return win.title, win._hWnd
    if win32gui and win32process and psutil:
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        try:
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            proc = psutil.Process(pid)
            exe = proc.name()
        except Exception:
            exe = None
        return title, exe
    return None, None

def main():
    log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../foreground_app_log.csv'))
    print(f"Logging foreground apps to {log_file}. Press Ctrl+C to stop.")
    header = ["timestamp", "window_title", "process_name"]
    last = None
    with open(log_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if f.tell() == 0:
            writer.writerow(header)
        try:
            while True:
                title, exe = get_foreground_app()
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                if (title, exe) != last:
                    print(f"{now} | {title} | {exe}")
                    writer.writerow([now, title, exe])
                    f.flush()
                    last = (title, exe)
                time.sleep(2)
        except KeyboardInterrupt:
            print("Stopped foreground app logging.")

if __name__ == "__main__":
    main() 