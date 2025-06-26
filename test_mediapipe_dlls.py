import os
import sys
import ctypes
import traceback

print("Python EXE:", sys.executable)
print("sys.path:", sys.path)
print("PATH:", os.environ.get("PATH"))

try:
    import mediapipe
    print("mediapipe imported successfully")
    from mediapipe.python import _framework_bindings
    print("Imported _framework_bindings:", _framework_bindings)
except Exception as e:
    print("Mediapipe import error:", e)
    traceback.print_exc()
    # Try to find the DLL manually
    mp_dir = os.path.dirname(mediapipe.__file__)
    for root, dirs, files in os.walk(mp_dir):
        for file in files:
            if file.endswith(".dll"):
                dll_path = os.path.join(root, file)
                print("Trying to load DLL:", dll_path)
                try:
                    ctypes.CDLL(dll_path)
                    print("Loaded:", dll_path)
                except Exception as dll_e:
                    print("Failed to load:", dll_path)
                    print(dll_e) 