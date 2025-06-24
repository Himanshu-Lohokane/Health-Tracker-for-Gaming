import subprocess
import sys
import os
import time

def test_foreground_tracker_logger():
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../app/trackers/foreground_tracker_logger.py'))
    log_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '../foreground_app_log.csv'))
    print(f"Running: {script_path}")
    print(f"Log file: {log_file}")
    try:
        proc = subprocess.Popen([sys.executable, script_path])
        print("Switch between apps for 10 seconds. Then press Ctrl+C in the logger window to stop.")
        time.sleep(10)
        print("Check that foreground_app_log.csv contains the correct logs.")
        print("You can open the CSV file in Excel or a text editor.")
    except Exception as e:
        print(f"Error running foreground tracker logger: {e}")

if __name__ == "__main__":
    test_foreground_tracker_logger() 