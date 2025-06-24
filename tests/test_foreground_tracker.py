import subprocess
import sys
import os

def test_foreground_tracker():
    script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../app/trackers/foreground_tracker_test.py'))
    print(f"Running: {script_path}")
    try:
        proc = subprocess.Popen([sys.executable, script_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Switch between apps and observe the output in the console window.")
        print("Press Ctrl+C in the console to stop the test.")
        proc.wait()
    except KeyboardInterrupt:
        print("Test stopped by user.")
    except Exception as e:
        print(f"Error running foreground tracker: {e}")

if __name__ == "__main__":
    test_foreground_tracker() 