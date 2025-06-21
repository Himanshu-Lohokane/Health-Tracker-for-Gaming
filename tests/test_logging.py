#!/usr/bin/env python3
"""
Test script to verify the improved logging system works correctly.
This script will test the database setup and logging functions.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

import sqlite3
import time
from datetime import datetime

# Import from app
from main3 import setup_database, log_action, log_posture_data

def test_database_setup():
    """Test database setup and table creation"""
    print("Testing database setup...")
    
    # Setup database
    setup_database()
    
    # Verify tables exist
    try:
        with sqlite3.connect("health_tracker.db") as conn:
            c = conn.cursor()
            
            # Check if tables exist
            c.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in c.fetchall()]
            
            required_tables = ['health_logs', 'user_settings', 'user_points', 'detailed_logs']
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                print(f"❌ Missing tables: {missing_tables}")
                return False
            else:
                print("✅ All required tables created successfully")
                
            # Check detailed_logs schema
            c.execute("PRAGMA table_info(detailed_logs)")
            columns = {row[1] for row in c.fetchall()}
            required_columns = {
                'id', 'timestamp', 'action', 'posture_status', 'back_angle',
                'water_intake', 'break_taken', 'activity', 'forward_lean',
                'shoulder_alignment', 'session_status', 'game'
            }
            
            missing_columns = required_columns - columns
            if missing_columns:
                print(f"❌ Missing columns in detailed_logs: {missing_columns}")
                return False
            else:
                print("✅ All required columns present in detailed_logs")
                
            return True
            
    except Exception as e:
        print(f"❌ Database setup test failed: {e}")
        return False

def test_logging_functions():
    """Test the logging functions with various data types"""
    print("\nTesting logging functions...")
    
    try:
        # Test 1: Basic action logging
        print("Testing basic action logging...")
        log_action("Test action", session_status="Testing")
        
        # Test 2: Aggregated posture data logging (30-second mode)
        print("Testing aggregated posture data logging...")
        log_posture_data(
            feedback="Good posture",  # This would be the mode over 30 seconds
            back_angle=175.5,
            forward_lean=0.02,
            shoulder_diff=0.01,
            game_name="test_game.exe"
        )
        
        # Test 3: Hydration reminder logging
        print("Testing hydration reminder logging...")
        log_action("Hydration reminder sent", water_intake=1, game="test_game.exe")
        
        # Test 4: Break reminder logging
        print("Testing break reminder logging...")
        log_action("Break reminder sent", break_taken=1, game="test_game.exe")
        
        # Test 5: Session logging
        print("Testing session logging...")
        log_action("Session started", session_status="Started", game="test_game.exe")
        
        # Test 6: Invalid data handling
        print("Testing invalid data handling...")
        log_action("Test with invalid data", back_angle="invalid", forward_lean=-5)
        
        print("✅ All logging tests completed")
        return True
        
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False

def verify_logged_data():
    """Verify that the logged data is correct and consistent"""
    print("\nVerifying logged data...")
    
    try:
        with sqlite3.connect("health_tracker.db") as conn:
            c = conn.cursor()
            
            # Get all logged data
            c.execute("SELECT * FROM detailed_logs ORDER BY timestamp DESC LIMIT 10")
            rows = c.fetchall()
            
            if not rows:
                print("❌ No data found in database")
                return False
            
            print(f"✅ Found {len(rows)} log entries")
            
            # Check data consistency
            for i, row in enumerate(rows):
                print(f"\nEntry {i+1}:")
                print(f"  Timestamp: {row[1]}")
                print(f"  Action: {row[2]}")
                print(f"  Posture Status: {row[3]}")
                print(f"  Back Angle: {row[4]}")
                print(f"  Water Intake: {row[5]}")
                print(f"  Break Taken: {row[6]}")
                print(f"  Forward Lean: {row[8]}")
                print(f"  Shoulder Alignment: {row[9]}")
                print(f"  Session Status: {row[10]}")
                print(f"  Game: {row[11]}")
            
            # Check for data validation
            c.execute("SELECT COUNT(*) FROM detailed_logs WHERE back_angle < 0 OR back_angle > 360")
            invalid_angles = c.fetchone()[0]
            
            if invalid_angles > 0:
                print(f"⚠️  Found {invalid_angles} entries with invalid back angles")
            else:
                print("✅ All back angles are within valid range")
            
            return True
            
    except Exception as e:
        print(f"❌ Data verification failed: {e}")
        return False

def main():
    setup_database()  # Ensure DB is initialized before tests
    print("🧪 Testing Health Tracker Logging System")
    print("=" * 50)
    
    # Run tests
    tests = [
        ("Database Setup", test_database_setup),
        ("Logging Functions", test_logging_functions),
        ("Data Verification", verify_logged_data)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        if test_func():
            passed += 1
            print(f"✅ {test_name} test PASSED")
        else:
            print(f"❌ {test_name} test FAILED")
    
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The logging system is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 