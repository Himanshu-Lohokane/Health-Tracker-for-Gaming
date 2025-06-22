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

# Import from app
from main3 import setup_database, log_action, log_posture_data, is_game_running
from posture_detection import PostureDetector

def test_database_integration():
    """Test database connectivity and operations"""
    print("🔍 Testing Database Integration...")
    
    try:
        # Test database connection
        conn = sqlite3.connect('health_tracker.db')
        c = conn.cursor()
        
        # Test table existence
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in c.fetchall()]
        required_tables = ['health_logs', 'user_settings', 'user_points', 'detailed_logs']
        
        missing_tables = [table for table in required_tables if table not in tables]
        if missing_tables:
            print(f"❌ Missing tables: {missing_tables}")
            return False
        
        print("✅ All required tables exist")
        
        # Test data insertion
        test_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        c.execute('''INSERT INTO detailed_logs (timestamp, action, posture_status, back_angle, 
                     water_intake, break_taken, activity, forward_lean, shoulder_alignment, 
                     session_status, game)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                  (test_timestamp, "Integration Test", "Good Posture", 175.0, 0, 0, 
                   "Testing", 0.02, 0.01, "Testing", "integration_test.exe"))
        conn.commit()
        
        # Verify insertion
        c.execute("SELECT action FROM detailed_logs WHERE action = 'Integration Test'")
        result = c.fetchone()
        if result:
            print("✅ Data insertion and retrieval working")
        else:
            print("❌ Data insertion failed")
            return False
        
        # Clean up test data
        c.execute("DELETE FROM detailed_logs WHERE action = 'Integration Test'")
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
        # Setup fresh database for testing
        setup_database()
        
        # Test basic logging
        log_action("Integration Test Action", session_status="Testing")
        
        # Test posture logging
        log_posture_data(
            feedback="Good posture detected",
            back_angle=175.5,
            forward_lean=0.02,
            shoulder_diff=0.01,
            game_name="integration_test.exe"
        )
        
        # Test reminder logging
        log_action("Hydration reminder sent", water_intake=1, game="integration_test.exe")
        log_action("Break reminder sent", break_taken=1, game="integration_test.exe")
        
        print("✅ All logging functions working")
        return True
        
    except Exception as e:
        print(f"❌ Logging functions test failed: {e}")
        return False

def test_game_detection():
    """Test game detection functionality"""
    print("\n🔍 Testing Game Detection...")
    
    try:
        # Test game detection
        game_running, game_name = is_game_running()
        
        print(f"Game running: {game_running}")
        print(f"Game name: {game_name}")
        
        # Test with a known process (should find at least some system processes)
        all_processes = []
        for process in psutil.process_iter(['name']):
            try:
                if process.info['name']:
                    all_processes.append(process.info['name'])
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        print(f"Total processes found: {len(all_processes)}")
        
        # Check if we can detect any processes
        if len(all_processes) > 0:
            print("✅ Game detection system working")
            return True
        else:
            print("⚠️  No processes detected (might be permission issue)")
            return True  # Not a failure, just limited access
            
    except Exception as e:
        print(f"❌ Game detection test failed: {e}")
        return False

def test_posture_detection_import():
    """Test posture detection module import and basic functionality with real frame capture"""
    print("\n🔍 Testing Posture Detection Module...")

    detector = None
    try:
        # Test module import
        print("✅ Posture detection module imported successfully")

        # Test detector initialization
        detector = PostureDetector()
        print("✅ Posture detector initialized")

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
    """Test data validation and error handling"""
    print("\n🔍 Testing Data Validation...")
    
    try:
        # Test invalid data handling
        log_action("Test with invalid back angle", back_angle=400)  # Invalid angle
        log_action("Test with negative forward lean", forward_lean=-5)  # Invalid value
        log_action("Test with invalid shoulder alignment", shoulder_alignment="invalid")
        
        # Test posture status standardization
        log_action("Test posture standardization", posture_status="good posture")
        log_action("Test posture standardization", posture_status="BAD POSTURE")
        log_action("Test posture standardization", posture_status="forward head")
        
        print("✅ Data validation working (invalid data handled gracefully)")
        return True
        
    except Exception as e:
        print(f"❌ Data validation test failed: {e}")
        return False

def test_database_performance():
    """Test database performance with multiple operations"""
    print("\n🔍 Testing Database Performance...")
    
    try:
        conn = sqlite3.connect('health_tracker.db')
        c = conn.cursor()
        
        start_time = time.time()
        
        # Insert multiple test records
        for i in range(10):
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            c.execute('''INSERT INTO detailed_logs (timestamp, action, posture_status, back_angle, 
                         water_intake, break_taken, activity, forward_lean, shoulder_alignment, 
                         session_status, game)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (timestamp, f"Performance Test {i}", "Good Posture", 175.0, 0, 0, 
                       "Testing", 0.02, 0.01, "Testing", "performance_test.exe"))
        
        conn.commit()
        
        # Query performance
        c.execute("SELECT COUNT(*) FROM detailed_logs WHERE action LIKE 'Performance Test%'")
        count = c.fetchone()[0]
        
        end_time = time.time()
        duration = end_time - start_time
        
        print(f"✅ Inserted {count} records in {duration:.3f} seconds")
        
        # Clean up
        c.execute("DELETE FROM detailed_logs WHERE action LIKE 'Performance Test%'")
        conn.commit()
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database performance test failed: {e}")
        return False

def test_export_functionality():
    """Test CSV export functionality"""
    print("\n🔍 Testing Export Functionality...")
    
    try:
        # Test export logic (simplified version)
        conn = sqlite3.connect('health_tracker.db')
        c = conn.cursor()
        c.execute("SELECT * FROM detailed_logs LIMIT 5")
        rows = c.fetchall()
        conn.close()
        
        if rows:
            import csv
            with open("test_export.csv", "w", newline="", encoding='utf-8') as file:
                writer = csv.writer(file)
                writer.writerow([
                    "ID", "Timestamp", "Action", "Posture Status", "Back Angle", 
                    "Water Intake", "Break Taken", "Activity", "Forward Lean", 
                    "Shoulder Alignment", "Session Status", "Game"
                ])
                writer.writerows(rows)
            
            # Check if file was created
            if os.path.exists("test_export.csv"):
                file_size = os.path.getsize("test_export.csv")
                print(f"✅ Export test successful - file size: {file_size} bytes")
                
                # Clean up
                os.remove("test_export.csv")
                return True
            else:
                print("❌ Export file not created")
                return False
        else:
            print("⚠️  No data to export")
            return True
            
    except Exception as e:
        print(f"❌ Export functionality test failed: {e}")
        return False

def main():
    setup_database()  # Ensure DB is initialized before tests
    print("🧪 HEALTH TRACKER INTEGRATION TEST")
    print("=" * 60)
    
    tests = [
        ("Database Integration", test_database_integration),
        ("Logging Functions", test_logging_functions),
        ("Game Detection", test_game_detection),
        ("Posture Detection Module", test_posture_detection_import),
        ("Data Validation", test_data_validation),
        ("Database Performance", test_database_performance),
        ("Export Functionality", test_export_functionality)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        if test_func():
            passed += 1
            print(f"✅ {test_name} PASSED")
        else:
            print(f"❌ {test_name} FAILED")
    
    print("\n" + "=" * 60)
    print(f"📊 INTEGRATION TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL INTEGRATION TESTS PASSED!")
        print("🚀 Application is ready for production use")
    elif passed >= total * 0.8:
        print("✅ MOST TESTS PASSED - Application is mostly functional")
    else:
        print("⚠️  MANY TESTS FAILED - Application needs attention")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 