import sqlite3
import random
from datetime import datetime, timedelta
import csv

def generate_random_data(num_entries):
    actions = ['Aggregated Posture: Slouching', 'Aggregated Posture: Good Posture', 'Aggregated Posture: Forward Head Posture']
    postures = ['Slouching', 'Good Posture', 'Forward Head Posture']
    games = ['WhatsApp.exe', 'Valorant.exe', 'LeagueClient.exe', 'CSGO.exe', 'Solitaire.exe']
    data = []
    start_time = datetime(2025, 1, 23, 13, 0, 0)

    for i in range(1, num_entries + 1):
        timestamp = start_time + timedelta(seconds=i * 30)
        action = random.choice(actions)
        posture_status = action.split(': ')[1]
        back_angle = round(random.uniform(160, 180), 2)
        water_intake = random.choice([0, 1])
        break_taken = random.choice([0, 1])
        forward_lean = round(random.uniform(0.05, 0.15), 2)
        shoulder_alignment = round(random.uniform(0.0, 0.03), 2)
        session_status = 'Running'
        game = random.choice(games)
        data.append((i, timestamp.strftime('%Y-%m-%d %H:%M:%S'), action, posture_status, back_angle, water_intake, break_taken, None, forward_lean, shoulder_alignment, session_status, game))

    return data

def insert_test_data(num_entries=1000):
    conn = sqlite3.connect("health_tracker.db")
    c = conn.cursor()

    # Generate random data
    additional_data = generate_random_data(num_entries)

    # Insert additional data into detailed_logs
    c.executemany('''INSERT OR IGNORE INTO detailed_logs (id, timestamp, action, posture_status, back_angle, water_intake, break_taken, activity, forward_lean, shoulder_alignment, session_status, game)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', additional_data)
    conn.commit()

    # Export data to CSV
    c.execute("SELECT * FROM detailed_logs")
    rows = c.fetchall()
    conn.close()

    with open("detailed_health_logs.csv", "w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["ID", "Timestamp", "Action", "Posture Status", "Back Angle", "Water Intake", "Break Taken", "Activity", "Forward Lean", "Shoulder Alignment", "Session Status", "Game"])
        writer.writerows(rows)

if __name__ == "__main__":
    insert_test_data(1000)
