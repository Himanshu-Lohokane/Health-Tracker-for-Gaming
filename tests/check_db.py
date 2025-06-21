#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../app')))

import sqlite3
import time
from datetime import datetime
from main3 import setup_database

setup_database()  # Ensure DB is initialized before checking

def check_database():
    try:
        conn = sqlite3.connect('health_tracker.db')
        c = conn.cursor()
        
        # Check total entries
        c.execute('SELECT COUNT(*) FROM detailed_logs')
        total_entries = c.fetchone()[0]
        print(f"📊 Total log entries: {total_entries}")
        
        # Check recent entries
        c.execute('SELECT timestamp, action FROM detailed_logs ORDER BY timestamp DESC LIMIT 5')
        recent_entries = c.fetchall()
        
        print("\n🕒 Recent entries:")
        for i, (timestamp, action) in enumerate(recent_entries, 1):
            print(f"  {i}. {timestamp} - {action}")
        
        # Check if application is actively logging
        c.execute('SELECT timestamp FROM detailed_logs ORDER BY timestamp DESC LIMIT 1')
        latest_entry = c.fetchone()
        
        if latest_entry:
            latest_time = datetime.strptime(latest_entry[0], '%Y-%m-%d %H:%M:%S')
            current_time = datetime.now()
            time_diff = (current_time - latest_time).total_seconds()
            
            print(f"\n⏰ Latest entry: {latest_entry[0]}")
            print(f"⏱️  Time since last entry: {time_diff:.1f} seconds")
            
            if time_diff < 60:
                print("✅ Application appears to be actively logging")
            else:
                print("⚠️  No recent activity detected")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Database check failed: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Checking Health Tracker Database Status")
    print("=" * 50)
    check_database() 