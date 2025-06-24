import time

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
    print("Tracking foreground window. Press Ctrl+C to stop.")
    last = None
    try:
        while True:
            title, exe = get_foreground_app()
            if (title, exe) != last:
                print(f"Foreground: {title} | Process: {exe}")
                last = (title, exe)
            time.sleep(1)
    except KeyboardInterrupt:
        print("Stopped foreground tracking.")

if __name__ == "__main__":
    main() 