# main.py
import sys
import time
import threading
import sqlite3
from sqlite3 import connect
from threading import Lock
import csv
import random
import os
from PyQt6.QtWidgets import QApplication,QGridLayout, QMainWindow, QLabel, QPushButton, QVBoxLayout, QWidget, QListWidget, QFileDialog, QMessageBox, QDialog, QLineEdit, QHBoxLayout, QProgressBar
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt, QTimer
from posture_detection import PostureDetector
from datetime import datetime
import psutil
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
db_lock=Lock()
# Database setup
GAME_PROCESSES = ["whatsapp.exe", "valorant.exe", "leagueclient.exe", "csgo.exe", "solitaire.exe"]

def is_game_running():
    for process in psutil.process_iter(['name']):
        try:
            if process.info['name'] and process.info['name'].lower() in GAME_PROCESSES:
                return True, process.info['name']
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False, None

def setup_database():
    conn = sqlite3.connect("health_tracker.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS health_logs (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT,
                    action TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_settings (
                    id INTEGER PRIMARY KEY,
                    hydration_interval INTEGER,
                    break_interval INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS user_points (
                    id INTEGER PRIMARY KEY,
                    points INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS detailed_logs (
                    id INTEGER PRIMARY KEY,
                    timestamp TEXT,
                    action TEXT,
                    posture_status TEXT,
                    back_angle REAL,
                    water_intake INTEGER,
                    break_taken INTEGER,
                    activity TEXT,
                    forward_lean REAL,
                    shoulder_alignment REAL,
                    session_status TEXT,
                    game TEXT)''')
    c.execute('''INSERT OR IGNORE INTO user_settings (id, hydration_interval, break_interval)
                 VALUES (1, 15, 30)''')  # Default settings
    c.execute('''INSERT OR IGNORE INTO user_points (id, points)
                 VALUES (1, 0)''')  # Default points
    conn.commit()
    conn.close()
    db_lock=Lock()
# Insert log into database
def log_action(action, posture_status=None, back_angle=None, water_intake=None, break_taken=None, activity=None, forward_lean=None, shoulder_alignment=None, session_status=None, game=None):
    with db_lock:
        with connect("health_tracker.db") as conn:
            c = conn.cursor()
            c.execute('''INSERT INTO detailed_logs (timestamp, action, posture_status, back_angle, water_intake, break_taken, activity, forward_lean, shoulder_alignment, session_status, game)
                         VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (action, posture_status, back_angle, water_intake, break_taken, activity, forward_lean, shoulder_alignment, session_status, game))    
    conn.commit()
    conn.close()
# Add points for completing reminders
def add_points(points):
    conn = sqlite3.connect("health_tracker.db")
    c = conn.cursor()
    c.execute("UPDATE user_points SET points = points + ? WHERE id = 1", (points,))
    conn.commit()
    conn.close()

# Detect active game process
def is_game_running():
    game_name = None
    for process in psutil.process_iter(['name']):
        try:
            if process.info['name'] and process.info['name'].lower() in [
                'whatsapp.exe', 'valorant.exe', 'leagueclient.exe', 'csgo.exe', 'solitaire.exe']:
                game_name = process.info['name']
                return True, game_name
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False, game_name

# Health Tips
HEALTH_TIPS = [
    "Stretch your arms and legs every hour.",
    "Drink water to keep your mind sharp.",
    "Take deep breaths to relax.",
    "Avoid looking at the screen for long periods.",
    "Maintain a proper sitting posture."
]

class Overlay(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Health Tracker")
        self.setGeometry(50, 50, 1500, 740)
        self.last_log_time = time.time()

        self.theme = "Light"
        
        # Create main layout
        self.main_layout = QHBoxLayout()

        # Left frame for video feed and progress bar
        self.left_frame = QWidget()
        self.left_layout = QVBoxLayout()
        self.left_frame.setLayout(self.left_layout)

        # Video feed
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("""
            QLabel {
                border-radius: 20px;
                background-color: #333;
                padding: 10px;
            }
        """)
        self.left_layout.addWidget(self.video_label)

        # Posture feedback label
        self.posture_feedback = QLabel("Posture Status: Analyzing...")
        self.left_layout.addWidget(self.posture_feedback)
        self.posture_feedback.setStyleSheet("""
        QLabel{
                background-color: grey;
                border-radius: 20px;
                padding: 10px;
                    
                font-size: 20px;
                color: white;
                font-weight:bold;                           }
""")
        self.game_status = QLabel("Game Status: Not Running")
        self.left_layout.addWidget(self.game_status)
        self.game_status.setStyleSheet("""
        QLabel{
                /*background-color: grey ;
                border-radius: 15px;
                padding: 5px;*/
                font-size:20px;
                color: grey;
                font-weight:bold;                           }
""")

        # Right frame for logs, buttons, and controls
        self.right_frame = QWidget()
        self.right_frame.setFixedWidth(540)  # Set width to 490 pixels
        self.right_layout = QVBoxLayout()
        self.right_frame.setLayout(self.right_layout)

        # Session timer and game status
        self.label = QLabel("Session Timer: 0 seconds")
        self.right_layout.addWidget(self.label)
        self.label.setStyleSheet("""
        QLabel{
                
                padding: 5px;
                font-size:20px;
                color: Black;
                font-weight:bold;                           }
""")
        

        # self.game_status = QLabel("Game Status: Not Running")
        # self.right_layout.addWidget(self.game_status)

        # Create a horizontal layout for Start and Stop buttons
        button_layout = QHBoxLayout()

        # Start button
        self.start_button = QPushButton("Start")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 15px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #4CAF50;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        self.start_button.clicked.connect(self.start)
        button_layout.addWidget(self.start_button)

        # Stop button
        self.stop_button = QPushButton("Stop")
        self.stop_button.setStyleSheet("""
            QPushButton {
                background-color: #f44336;
                color: white;
                border-radius: 15px;
                padding: 10px;
                font-size: 14px;
                font-weight:Bold;
                border: 2px solid #f44336;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        self.stop_button.clicked.connect(self.stop)
        button_layout.addWidget(self.stop_button)

        # Add the button layout to the right layout
        self.right_layout.addLayout(button_layout)

        # Logs Viewer
        self.logs_label = QLabel("Recent Logs:")
        self.right_layout.addWidget(self.logs_label)
        self.logs_label.setStyleSheet("""
        QLabel{
                background-color: grey ;
                border-radius: 10px;
                padding: 5px;
                font-size:18px;
                color: white;
                font-weight:bold;                           }
""")

        self.log_list = QListWidget()
        self.right_layout.addWidget(self.log_list)
        self.log_list.setStyleSheet("""
        QListWidget{
                background-color:#b6d9c9 ;
                border-radius: 15px;
                padding: 3px;
                font-size:15px;
                color: white;
                font-weight:bold;                           }
""")

        # Create a horizontal layout for the bottom buttons
        # bottom_button_layout = QHBoxLayout()
        other_buttons_layout = QGridLayout()
        # Other buttons
        self.settings_button = QPushButton("Customize Settings")
        self.settings_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border-radius: 15px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #2196F3;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:pressed {
                background-color: #0D47A1;
            }
        """)
        self.settings_button.clicked.connect(self.open_settings)
        # bottom_button_layout.addWidget(self.settings_button)
        other_buttons_layout.addWidget(self.settings_button, 0, 0)

        self.progress_button = QPushButton("View Progress")
        self.progress_button.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border-radius: 15px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #9C27B0;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
            QPushButton:pressed {
                background-color: #4A148C;
            }
        """)
        self.progress_button.clicked.connect(self.show_graph)
        # bottom_button_layout.addWidget(self.progress_button)
        other_buttons_layout.addWidget(self.progress_button, 0, 1)
        
        
        self.export_button = QPushButton("Export Logs")
        self.export_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border-radius: 15px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #FF9800;
            }
            QPushButton:hover {
                background-color: #F57C00;
            }
            QPushButton:pressed {
                background-color: #E65100;
            }
        """)
        self.export_button.clicked.connect(self.export_logs)
        # bottom_button_layout.addWidget(self.export_button)
        other_buttons_layout.addWidget(self.export_button, 1, 0)

        self.dark_mode_button = QPushButton("Toggle Dark Mode")
        self.dark_mode_button.setStyleSheet("""
            QPushButton {
                background-color: #607D8B;
                color: white;
                border-radius: 15px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #607D8B;
            }
            QPushButton:hover {
                background-color: #455A64;
            }
            QPushButton:pressed {
                background-color: #37474F;
            }
        """)
        self.dark_mode_button.clicked.connect(self.toggle_theme)
        # bottom_button_layout.addWidget(self.dark_mode_button)
        other_buttons_layout.addWidget(self.dark_mode_button, 1, 1)

        # Add the bottom button layout to the right layout
        self.right_layout.addLayout(other_buttons_layout)

        # Add left and right frames to the main layout
        self.main_layout.addWidget(self.left_frame)
        self.main_layout.addWidget(self.right_frame)

        # Central widget
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)

        self.running = False
        self.start_time = None
        
        # Apply initial styles
        self.apply_styles()

        # Initialize PostureDetector
        self.posture_detector = PostureDetector()
        if not self.posture_detector.initialize_camera():
            QMessageBox.critical(self, "Error", "Could not initialize camera")
            return

        # Start video update
        self.update_video()

        # Set up a timer to export logs every 5 minutes
        self.export_timer = QTimer()
        self.export_timer.timeout.connect(self.export_logs)
        self.export_timer.start(1 * 60 * 1000)  # 5 minutes in milliseconds

    def apply_styles(self):
        if self.theme == "Light":
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f0f0f0;
                }
                QLabel {
                    font-size: 14px;
                    color: #333;
                }
                QListWidget {
                    background-color: white;
                    border-radius: 10px;
                    padding: 10px;
                    border: 1px solid #ccc;
                }
                QLineEdit {
                    border-radius: 10px;
                    padding: 5px;
                    border: 1px solid #ccc;
                }
                QProgressBar {
                    border-radius: 5px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #4CAF50;
                    border-radius: 5px;
                }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #333;
                }
                QLabel {
                    font-size: 14px;
                    color: white;
                }
                QListWidget {
                    background-color: #444;
                    color: white;
                    border-radius: 10px;
                    padding: 10px;
                    border: 1px solid #555;
                }
                QLineEdit {
                    border-radius: 10px;
                    padding: 5px;
                    border: 1px solid #555;
                }
                QProgressBar {
                    border-radius: 5px;
                    text-align: center;
                }
                QProgressBar::chunk {
                    background-color: #666;
                    border-radius: 5px;
                }
            """)

    def toggle_theme(self):
        if self.theme == "Light":
            self.theme = "Dark"
        else:
            self.theme = "Light"
        self.apply_styles()

    def start(self):
        if not self.running:
            self.running = True
            self.start_time = time.time()
            threading.Thread(target=self.update_timer, daemon=True).start()
            log_action("Session started", session_status="Started")

    def stop(self):
        if self.running:
            self.running = False
            self.posture_detector.release()
            log_action("Session stopped", session_status="Stopped")

def update_timer(self):
    self.timer = QTimer()
    self.timer.timeout.connect(self.update_timer_label)
    self.timer.start(1000)  # 1 second interval

def update_timer_label(self):
    if self.running:
        elapsed = int(time.time() - self.start_time)
        self.label.setText(f"Session Timer: {elapsed} seconds")
        game_running, game_name = is_game_running()
        self.game_status.setText(
            f"Game Status: Running ({game_name})" if game_running else "Game Status: Not Running"
        )
        self.update_logs()

    def update_logs(self):
        conn = sqlite3.connect("health_tracker.db")
        c = conn.cursor()
        c.execute("SELECT timestamp, action FROM health_logs ORDER BY id DESC LIMIT 8")
        rows = c.fetchall()
        conn.close()

        self.log_list.clear()
        for row in rows:
            self.log_list.addItem(f"{row[0]} - {row[1]}")

    def update_video(self):
        current_time = time.time()
        frame, feedback, back_angle, forward_lean, shoulder_diff = self.posture_detector.get_frame()
        
        if frame is not None:
            # Convert the frame (QImage) to QPixmap
            pixmap = QPixmap.fromImage(frame)
            self.video_label.setPixmap(pixmap)
            self.video_label.setScaledContents(True)
            self.posture_feedback.setText(f"Posture Status: {feedback}")
            
            # Log aggregated data every 30 seconds
            if current_time - self.last_log_time >= 30:  # 30 seconds interval
                aggregated_posture = self.posture_detector.get_aggregated_posture()
                game_running, game_name = is_game_running()
                log_action(f"Aggregated Posture: {aggregated_posture}", posture_status=feedback, back_angle=back_angle, forward_lean=forward_lean, shoulder_alignment=shoulder_diff, session_status="Running", game=game_name)
                self.last_log_time = current_time
                
        QTimer.singleShot(10, self.update_video)

    def open_settings(self):
        settings_dialog = QDialog(self)
        settings_dialog.setWindowTitle("Customize Settings")
        settings_dialog.setGeometry(300, 200, 300, 200)

        layout = QVBoxLayout()

        hydration_label = QLabel("Hydration Reminder Interval (minutes):")
        layout.addWidget(hydration_label)
        hydration_entry = QLineEdit()
        layout.addWidget(hydration_entry)

        break_label = QLabel("Break Reminder Interval (minutes):")
        layout.addWidget(break_label)
        break_entry = QLineEdit()
        layout.addWidget(break_entry)

        save_button = QPushButton("Save")
        save_button.clicked.connect(lambda: self.save_settings(hydration_entry.text(), break_entry.text(), settings_dialog))
        layout.addWidget(save_button)

        settings_dialog.setLayout(layout)
        settings_dialog.exec()

    def save_settings(self, hydration_interval, break_interval, dialog):
        conn = sqlite3.connect("health_tracker.db")
        c = conn.cursor()
        c.execute("UPDATE user_settings SET hydration_interval = ?, break_interval = ? WHERE id = 1",
                  (hydration_interval or 15, break_interval or 30))
        conn.commit()
        conn.close()
        dialog.accept()

    def show_graph(self):
        conn = sqlite3.connect("health_tracker.db")
        c = conn.cursor()
        c.execute("SELECT timestamp, action FROM health_logs")
        data = c.fetchall()
        conn.close()

        timestamps = [datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S") for row in data]
        actions = [row[1] for row in data]

        plt.figure(figsize=(10, 5))
        plt.plot(timestamps, [actions.count("Hydration reminder sent") for _ in timestamps], label="Hydration")
        plt.plot(timestamps, [actions.count("Break reminder sent") for _ in timestamps], label="Breaks")
        plt.legend()
        plt.show()

    def export_logs(self):
        # Create a directory for logs if it doesn't exist
        log_directory = "health_logs"
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

        # Generate a filename with the current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = os.path.join(log_directory, f"detailed_health_logs_{timestamp}.csv")

        # Export logs to the file
        conn = sqlite3.connect("health_tracker.db")
        c = conn.cursor()
        c.execute("SELECT * FROM detailed_logs")
        rows = c.fetchall()
        conn.close()

        with open(filename, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["ID", "Timestamp", "Action", "Posture Status", "Back Angle", "Water Intake", "Break Taken", "Activity", "Forward Lean", "Shoulder Alignment", "Session Status", "Game"])
            writer.writerows(rows)

        # Show a message box to confirm the export
        QMessageBox.information(self, "Export Success", f"Logs exported as {filename}")

    def cleanup(self):
        self.posture_detector.release()
        self.close()
def export_logs(self):
    log_directory = "health_logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = os.path.join(log_directory, f"detailed_health_logs_{timestamp}.csv")

    try:
        with sqlite3.connect("health_tracker.db") as conn:
            c = conn.cursor()
            c.execute("SELECT * FROM detailed_logs")
            rows = c.fetchall()

        with open(filename, "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["ID", "Timestamp", "Action", "Posture Status", "Back Angle", "Water Intake", "Break Taken", "Activity", "Forward Lean", "Shoulder Alignment", "Session Status", "Game"])
            writer.writerows(rows)

        QMessageBox.information(self, "Export Success", f"Logs exported as {filename}")
    except Exception as e:
        QMessageBox.critical(self, "Export Error", f"Failed to export logs: {e}")
# Reminder thread function
def reminder_thread(app):
    conn = sqlite3.connect("health_tracker.db")
    c = conn.cursor()
    c.execute("SELECT hydration_interval, break_interval FROM user_settings WHERE id = 1")
    hydration_interval, break_interval = c.fetchone()
    conn.close()

    hydration_interval *= 60
    break_interval *= 60

    last_hydration_reminder = time.time()
    last_break_reminder = time.time()

    while True:
        current_time = time.time()
        game_running, game_name = is_game_running()
        if game_running:
            if current_time - last_hydration_reminder >= hydration_interval:
                QMessageBox.information(app, "Hydration Reminder", f"{random.choice(HEALTH_TIPS)}\nTake a sip of water!")
                log_action("Hydration reminder sent", water_intake=1, game=game_name)
                add_points(5)
                last_hydration_reminder = current_time

            if current_time - last_break_reminder >= break_interval:
                QMessageBox.information(app, "Break Reminder", f"{random.choice(HEALTH_TIPS)}\nTake a 5-minute break!")
                log_action("Break reminder sent", break_taken=1, game=game_name)
                add_points(10)
                last_break_reminder = current_time

        time.sleep(1)

def main():
    setup_database()
    app = QApplication(sys.argv)
    main_window = Overlay()
    main_window.show()
    threading.Thread(target=reminder_thread, args=(main_window,), daemon=True).start()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()