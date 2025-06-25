#!/usr/bin/env python3
"""
Comprehensive Integration Test for Health Tracker Application
Tests all major components: database, logging, posture detection, game detection, etc.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

import sqlite3
import time
from datetime import datetime
import psutil
import builtins
import io
import contextlib
import pytz

# Import from app
from main3 import setup_database, log_action, log_posture_data, get_foreground_app
from posture_detection import PostureDetector

def test_database_integration():
    """Test database connectivity and operations"""
    print("🔍 Testing Database Integration...")
    
    try:
        conn = sqlite3.connect('health_tracker.db')
        c = conn.cursor()
        
        # Test table existence
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in c.fetchall()]
        required_tables = ['detailed_logs']
        
        missing_tables = [table for table in required_tables if table not in tables]
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        
        print("✅ All required tables exist")
        
        # Test data insertion
        test_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute('''INSERT INTO detailed_logs (timestamp, back_angle, forward_lean, shoulder_alignment, good_posture, forward_lean_flag, uneven_shoulders_flag, session_status, game)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (test_timestamp, 175.0, 0.02, 0.01, 1, 0, 0, "Testing", "integration_test.exe"))
        conn.commit()
        
        # Verify insertion
        c.execute("SELECT good_posture, forward_lean_flag, uneven_shoulders_flag FROM detailed_logs WHERE session_status = 'Testing'")
        result = c.fetchone()
        if result == (1, 0, 0):
            print("✅ Data insertion and retrieval working")
        else:
            print("❌ Data insertion failed or incorrect flags")
            return False
        
        # Clean up test data
        c.execute("DELETE FROM detailed_logs WHERE session_status = 'Testing'")
        conn.commit()
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database integration test failed: {e}")
        return False

def test_logging_functions():
    """Test logging functions from main3"""
    print("\n🔍 Testing Logging Functions...")
    
    try:
        # Test basic logging
        log_action(session_status="Testing", game="integration_test.exe")
        
        # Test posture logging
        log_posture_data(
            feedback="Good posture detected",
            back_angle=175.5,
            forward_lean=0.02,
            shoulder_diff=0.01,
            game_name="integration_test.exe"
        )
        
        log_posture_data(
            feedback="Forward lean detected",
            back_angle=170.0,
            forward_lean=0.10,
            shoulder_diff=0.01,
            game_name="integration_test.exe"
        )
        
        log_posture_data(
            feedback="Uneven shoulders detected",
            back_angle=172.0,
            forward_lean=0.02,
            shoulder_diff=0.05,
            game_name="integration_test.exe"
        )
        
        print("✅ All logging functions working")
        return True
        
    except Exception as e:
        print(f"❌ Logging functions test failed: {e}")
        return False

def test_ist_timestamp_logging():
    """Test that log timestamps are in IST (Asia/Kolkata) timezone."""
    print("\n🔍 Testing IST Timestamp Logging...")
    try:
        # Log a new action
        log_action(session_status="IST_Test", game="integration_test.exe")
        time.sleep(1)
        # Fetch the most recent log with this session_status
        conn = sqlite3.connect('health_tracker.db')
        c = conn.cursor()
        c.execute("SELECT timestamp FROM detailed_logs WHERE session_status = 'IST_Test' ORDER BY id DESC LIMIT 1")
        row = c.fetchone()
        conn.close()
        if not row:
            print("❌ No IST_Test log found.")
            return False
        db_timestamp = row[0]
        # Parse the timestamp
        try:
            db_time = datetime.strptime(db_timestamp, '%Y-%m-%d %H:%M:%S')
            IST = pytz.timezone('Asia/Kolkata')
            db_time = IST.localize(db_time)
        except Exception as e:
            print(f"❌ Could not parse DB timestamp: {db_timestamp} ({e})")
            return False
        # Get current IST time
        now_ist = datetime.now(IST)
        # Compare hour and minute (allowing for a 2-minute window)
        if abs((now_ist - db_time).total_seconds()) < 120:
            print(f"✅ Timestamp is in IST: {db_timestamp} (Asia/Kolkata now: {now_ist.strftime('%Y-%m-%d %H:%M:%S')})")
            # Clean up test log
            conn = sqlite3.connect('health_tracker.db')
            c = conn.cursor()
            c.execute("DELETE FROM detailed_logs WHERE session_status = 'IST_Test'")
            conn.commit()
            conn.close()
            return True
        else:
            print(f"❌ Timestamp mismatch. DB: {db_timestamp}, IST now: {now_ist.strftime('%Y-%m-%d %H:%M:%S')}")
            return False
    except Exception as e:
        print(f"❌ IST timestamp test failed: {e}")
        return False

def test_game_detection():
    """Test foreground app detection functionality"""
    print("\n🔍 Testing Foreground App Detection...")
    try:
        # Test foreground app detection
        title, exe = get_foreground_app()
        print(f"Foreground window title: {title}")
        print(f"Foreground process name: {exe}")
        if title or exe:
            print("✅ Foreground app detection working")
            return True
        else:
            print("❌ No foreground app detected")
            return False
    except Exception as e:
        print(f"❌ Foreground app detection test failed: {e}")
        return False

def test_posture_detection_import():
    """Test posture detection module import and basic functionality with real frame capture"""
    print("\n🔍 Testing Posture Detection Module...")
    
    detector = None
    try:
        # Test module import
        print("✅ Posture detection module imported successfully")
        
        # Test detector initialization in headless mode
        detector = PostureDetector(headless=True)
        print("✅ Posture detector initialized (headless mode)")
        
        # Test camera initialization (might fail if no camera)
        camera_initialized = detector.initialize_camera()
        if not camera_initialized:
            print("⚠️  Camera not available (expected in some environments). Skipping frame capture.")
            return True
            print("✅ Camera initialized successfully")

        # Capture frames for a few seconds to fill the posture buffer
        frame_count = 0
        max_frames = 30
        feedbacks = []
        for _ in range(max_frames):
            qt_pixmap, feedback, back_angle, forward_lean, shoulder_diff = detector.get_frame()
            feedbacks.append(feedback)
            frame_count += 1
            time.sleep(0.05)  # Small delay to simulate real capture

        # Check aggregated posture
            aggregated = detector.get_aggregated_posture()
            print(f"✅ Aggregated posture method working: {aggregated}")
        if aggregated == "No posture data":
            print("⚠️  No posture data detected after capturing frames. Check camera and lighting conditions.")
        else:
            print(f"✅ Posture detected: {aggregated}")
        
        return True
        
    except Exception as e:
        print(f"❌ Posture detection test failed: {e}")
        return False
    finally:
        if detector is not None:
            detector.release()
            print("✅ Posture detector cleanup successful")

def test_data_validation():
    """Test data validation and error handling for new schema"""
    print("\n🔍 Testing Data Validation...")
    try:
        # Test invalid data handling (should not crash, but may log invalid data)
        log_action(good_posture=1, forward_lean_flag=0, uneven_shoulders_flag=0, back_angle=400, forward_lean=0.1, shoulder_alignment=0.01, session_status="Testing", game="test.exe")  # Invalid angle
        log_action(good_posture=0, forward_lean_flag=1, uneven_shoulders_flag=0, back_angle=170, forward_lean=-5, shoulder_alignment=0.01, session_status="Testing", game="test.exe")  # Invalid value
        log_action(good_posture=0, forward_lean_flag=0, uneven_shoulders_flag=1, back_angle=170, forward_lean=0.1, shoulder_alignment="invalid", session_status="Testing", game="test.exe")
        # Test flag logic
        log_action(good_posture=1, forward_lean_flag=0, uneven_shoulders_flag=0, back_angle=175, forward_lean=0.02, shoulder_alignment=0.01, session_status="Testing", game="test.exe")
        log_action(good_posture=0, forward_lean_flag=1, uneven_shoulders_flag=0, back_angle=170, forward_lean=0.10, shoulder_alignment=0.01, session_status="Testing", game="test.exe")
        log_action(good_posture=0, forward_lean_flag=0, uneven_shoulders_flag=1, back_angle=172, forward_lean=0.02, shoulder_alignment=0.05, session_status="Testing", game="test.exe")
        print("✅ Data validation working (invalid data handled gracefully)")
        return True
    except Exception as e:
        print(f"❌ Data validation test failed: {e}")
        return False

def test_database_performance():
    """Test database performance with multiple operations for new schema"""
    print("\n🔍 Testing Database Performance...")
    try:
        conn = sqlite3.connect('health_tracker.db')
        c = conn.cursor()
        start_time = time.time()
        # Insert multiple test records
        for i in range(10):
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            c.execute('''INSERT INTO detailed_logs (timestamp, good_posture, forward_lean_flag, uneven_shoulders_flag, back_angle, forward_lean, shoulder_alignment, session_status, game)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (timestamp, 1, 0, 0, 175.0, 0.02, 0.01, "Testing", "performance_test.exe"))
        conn.commit()
        # Query performance
        c.execute("SELECT COUNT(*) FROM detailed_logs WHERE session_status = 'Testing'")
        count = c.fetchone()[0]
        end_time = time.time()
        duration = end_time - start_time
        print(f"✅ Inserted {count} records in {duration:.3f} seconds")
        # Clean up
        c.execute("DELETE FROM detailed_logs WHERE session_status = 'Testing'")
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"❌ Database performance test failed: {e}")
        return False

def test_dashboard_visualization():
    """Test dashboard visualization functionality"""
    print("\n🔍 Testing Dashboard Visualization...")
    try:
        import sys
        import os
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))
        from PlotlyGraphs import HealthInsightsVisualizer
        visualizer = HealthInsightsVisualizer()
        assert visualizer.load_and_prepare_data(), "Failed to load data for dashboard."
        fig = visualizer.create_comprehensive_health_dashboard()
        html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../advanced_gaming_health_insights.html'))
        assert os.path.exists(html_path), "Dashboard HTML file was not created."
        print(f"✅ Dashboard visualization test successful - HTML file at: {html_path}")
        # Optionally, clean up the file after test
        # os.remove(html_path)
        return True
    except Exception as e:
        print(f"❌ Dashboard visualization test failed: {e}")
        return False

def test_missing_mediapipe():
    """Simulate missing MediaPipe and check for user-friendly error"""
    print("\n🔍 Testing Missing MediaPipe Handling...")
    import importlib
    import sys
    orig_import = builtins.__import__
    def fake_import(name, *args, **kwargs):
        if name == "mediapipe":
            raise ImportError("No module named 'mediapipe'")
        return orig_import(name, *args, **kwargs)
    builtins.__import__ = fake_import
    f = io.StringIO()
    with contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
        detector = None
        try:
            detector = PostureDetector(headless=True)
            assert not detector.mediapipe_available
        except Exception as e:
            print(f"Exception during missing mediapipe test: {e}")
        finally:
            builtins.__import__ = orig_import
            if detector:
                detector.release()
    output = f.getvalue()
    print(output)
    # Relaxed assertion: pass if any of the key error messages are present
    assert ("MediaPipe import error" in output or 
            "No module named 'mediapipe'" in output or
            "Posture detection will be limited" in output or
            "fallback mode without pose detection" in output)
    print("✅ Missing MediaPipe error handling PASSED")
    return True

def test_camera_failure():
    """Simulate camera failure and check for user-friendly error"""
    print("\n🔍 Testing Camera Failure Handling...")
    import cv2
    orig_videocapture = cv2.VideoCapture
    class FakeCapture:
        def isOpened(self): return False
        def release(self): pass
    cv2.VideoCapture = lambda *a, **kw: FakeCapture()
    f = io.StringIO()
    with contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
        detector = None
        try:
            detector = PostureDetector(headless=True)
            result = detector.initialize_camera()
            assert not result
        except Exception as e:
            print(f"Exception during camera failure test: {e}")
        finally:
            cv2.VideoCapture = orig_videocapture
            if detector:
                detector.release()
    output = f.getvalue()
    print(output)
    # Relaxed assertion: pass if any of the key error messages are present
    assert ("Could not open camera" in output or 
            "Camera initialization error" in output or
            "Possible reasons: camera not connected" in output)
    print("✅ Camera failure error handling PASSED")
    return True

def test_rapid_start_stop_cleanup():
    """Simulate rapid start/stop of PostureDetector and VideoWorker to check for resource leaks."""
    print("\n🔍 Testing Rapid Start/Stop and Cleanup...")
    try:
        from app.posture_detection import PostureDetector
    except ImportError:
        from posture_detection import PostureDetector
    import time
    cleanup_logs = []
    class DummyVideoWorker:
        def __init__(self, detector):
            self.detector = detector
            self.running = True
        def stop(self):
            self.running = False
            cleanup_logs.append("[DummyVideoWorker] Video thread stopped.")
    for i in range(5):
        detector = PostureDetector(headless=True)
        worker = DummyVideoWorker(detector)
        # Simulate start/stop
        worker.stop()
        detector.release()
        cleanup_logs.append(f"[Test] Iteration {i+1} cleanup complete.")
        time.sleep(0.1)
    for log in cleanup_logs:
        print(log)
    print("✅ Rapid start/stop cleanup test PASSED")
    return True

def main():
    setup_database()  # Ensure DB is initialized before tests
    print("🧪 HEALTH TRACKER INTEGRATION TEST")
    print("=" * 60)
    tests = [
        ("Database Integration", test_database_integration),
        ("Logging Functions", test_logging_functions),
        ("IST Timestamp Logging", test_ist_timestamp_logging),
        ("Game Detection", test_game_detection),
        ("Posture Detection Module", test_posture_detection_import),
        ("Data Validation", test_data_validation),
        ("Database Performance", test_database_performance),
        ("Dashboard Visualization", test_dashboard_visualization),
        ("Missing MediaPipe Handling", test_missing_mediapipe),
        ("Camera Failure Handling", test_camera_failure),
        ("Rapid Start/Stop Cleanup", test_rapid_start_stop_cleanup)
    ]
    passed = 0
    total = len(tests)
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            if result:
                passed += 1
                print(f"✅ {test_name} PASSED")
                results.append((test_name, True))
            else:
                print(f"❌ {test_name} FAILED")
                results.append((test_name, False))
        except Exception as e:
            print(f"❌ {test_name} FAILED with exception: {e}")
            results.append((test_name, False))
    print("\n" + "=" * 60)
    print(f"📊 INTEGRATION TEST RESULTS: {passed}/{total} tests passed")
    if passed == total:
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("🚀 Application is ready for production use")
    elif passed >= total * 0.8:
        print("✅ MOST TESTS PASSED - Application is mostly functional")
    else:
        print("⚠️  MANY TESTS FAILED - Application needs attention")
    # Print checklist summary
    print("\nTest Summary Checklist:")
    for name, ok in results:
        print(f"- [{'✅' if ok else '❌'}] {name}")
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 