import sys
import time
import threading
import sqlite3
import csv
import random
from datetime import datetime, timedelta, timezone
import os
import psutil
import subprocess
import webbrowser
import pytz

from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QWidget, QFrame, QListWidget, QScrollArea, QMessageBox, QDialog,
    QLineEdit, QGridLayout, QListWidgetItem
)
from PyQt6.QtCore import QTimer, Qt, pyqtSignal, QThread
from PyQt6.QtGui import QPixmap, QColor, QPalette
from plyer import notification
from win10toast import ToastNotifier
import matplotlib.pyplot as plt

try:
    from app.config import DEFAULT_HYDRATION_INTERVAL, DEFAULT_BREAK_INTERVAL
except ImportError:
    from config import DEFAULT_HYDRATION_INTERVAL, DEFAULT_BREAK_INTERVAL

from posture_detection import PostureDetector

# Remove old is_game_running and related logic
# Add foreground app detection
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
    # Try win32gui/win32process/psutil first for reliable process name
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
    # Fallback: pygetwindow for window title only
    if gw:
        win = gw.getActiveWindow()
        if win:
            return win.title, None
    return None, None

# Database setup
def setup_database():
    try:
        with sqlite3.connect("health_tracker.db") as conn:
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
                            good_posture INTEGER,
                            forward_lean_flag INTEGER,
                            uneven_shoulders_flag INTEGER,
                            back_angle REAL,
                            forward_lean REAL,
                            shoulder_alignment REAL,
                            session_status TEXT,
                            game TEXT)''')
            c.execute('''INSERT OR IGNORE INTO user_settings (id, hydration_interval, break_interval)
                         VALUES (1, ?, ?)''', (DEFAULT_HYDRATION_INTERVAL, DEFAULT_BREAK_INTERVAL))
            c.execute('''INSERT OR IGNORE INTO user_points (id, points)
                         VALUES (1, 0)''')
            conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")

# Insert log into database
def log_action(back_angle=None, forward_lean=None, shoulder_alignment=None, good_posture=None, forward_lean_flag=None, uneven_shoulders_flag=None, session_status=None, game=None):
    try:
        IST = pytz.timezone('Asia/Kolkata')
        now_ist = datetime.now(IST).strftime('%Y-%m-%d %H:%M:%S')
        with sqlite3.connect("health_tracker.db") as conn:
            c = conn.cursor()
            c.execute('''INSERT INTO detailed_logs (timestamp, good_posture, forward_lean_flag, uneven_shoulders_flag, back_angle, forward_lean, shoulder_alignment, session_status, game)
                         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (now_ist, good_posture, forward_lean_flag, uneven_shoulders_flag, back_angle, forward_lean, shoulder_alignment, session_status, game))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")

# Add points for completing reminders
def add_points(points):
    try:
        with sqlite3.connect("health_tracker.db") as conn:
            c = conn.cursor()
            c.execute("UPDATE user_points SET points = points + ? WHERE id = 1", (points,))
            conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")

# Health Tips
HEALTH_TIPS = [
    "Stretch your arms and legs every hour.",
    "Drink water to keep your mind sharp.",
    "Take deep breaths to relax.",
    "Avoid looking at the screen for long periods.",
    "Maintain a proper sitting posture."
]

# Video Feed Worker Thread
class VideoWorker(QThread):
    frame_ready = pyqtSignal(QPixmap, str, float, float, float)
    
    def __init__(self, posture_detector):
        super().__init__()
        self.posture_detector = posture_detector
        self.running = True
        
    def run(self):
        while self.running:
            pixmap, feedback, back_angle, forward_lean, shoulder_diff = self.posture_detector.get_frame()
            if pixmap is not None:
                back_angle = back_angle if back_angle is not None else 0.0
                forward_lean = forward_lean if forward_lean is not None else 0.0
                shoulder_diff = shoulder_diff if shoulder_diff is not None else 0.0
                self.frame_ready.emit(pixmap, feedback, back_angle, forward_lean, shoulder_diff)
            time.sleep(0.033)  # ~30 fps
    
    def stop(self):
        self.running = False
        print("[VideoWorker] Video thread stopped.")

# Reminder Worker Thread
class ReminderWorker(QThread):
    notification_sent = pyqtSignal(str, str, bool)  # message, type, game_running
    
    def __init__(self):
        super().__init__()
        self.running = True
        
    def run(self):
        try:
            with sqlite3.connect("health_tracker.db") as conn:
                c = conn.cursor()
                c.execute("SELECT hydration_interval, break_interval FROM user_settings WHERE id = 1")
                hydration_interval, break_interval = c.fetchone()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            hydration_interval, break_interval = DEFAULT_HYDRATION_INTERVAL, DEFAULT_BREAK_INTERVAL

        hydration_interval *= 60
        break_interval *= 60

        last_hydration_reminder = time.time()
        last_break_reminder = time.time()

        toaster = ToastNotifier()

        while self.running:
            current_time = time.time()
            title, exe = get_foreground_app()
            game_name = exe or title or "Unknown"
            if game_name and game_name != "Unknown":
                if current_time - last_hydration_reminder >= hydration_interval:
                    try:
                        notification.notify(
                            title="Hydration Reminder",
                            message=f"{random.choice(HEALTH_TIPS)}\nTake a sip of water!",
                            timeout=10
                        )
                    except:
                        toaster.show_toast("Hydration Reminder", f"{random.choice(HEALTH_TIPS)}\nTake a sip of water!",
                                        duration=10)
                    
                    self.notification_sent.emit(f"Hydration reminder sent", "hydration", True)
                    log_action(back_angle=0, forward_lean=0, shoulder_alignment=0, good_posture=1, forward_lean_flag=0, uneven_shoulders_flag=0, session_status="Running", game=game_name)
                    add_points(5)
                    last_hydration_reminder = current_time

                if current_time - last_break_reminder >= break_interval:
                    try:
                        notification.notify(
                            title="Break Reminder",
                            message=f"{random.choice(HEALTH_TIPS)}\nTake a 5-minute break!",
                            timeout=10
                        )
                    except:
                        toaster.show_toast("Break Reminder", f"{random.choice(HEALTH_TIPS)}\nTake a 5-minute break!",
                                        duration=10)
                    
                    self.notification_sent.emit(f"Break reminder sent", "break", True)
                    log_action(back_angle=0, forward_lean=0, shoulder_alignment=0, good_posture=0, forward_lean_flag=0, uneven_shoulders_flag=0, session_status="Running", game=game_name)
                    add_points(10)
                    last_break_reminder = current_time

            time.sleep(1)
    
    def stop(self):
        self.running = False

# Settings Dialog
class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Customize Settings")
        self.setFixedSize(300, 200)
        
        layout = QVBoxLayout()
        
        # Hydration settings
        layout.addWidget(QLabel("Hydration Reminder Interval (minutes):"))
        self.hydration_entry = QLineEdit()
        layout.addWidget(self.hydration_entry)
        
        # Break settings
        layout.addWidget(QLabel("Break Reminder Interval (minutes):"))
        self.break_entry = QLineEdit()
        layout.addWidget(self.break_entry)
        
        # Save button
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_settings)
        layout.addWidget(self.save_button)
        
        self.setLayout(layout)
        
        # Load current settings
        try:
            with sqlite3.connect("health_tracker.db") as conn:
                c = conn.cursor()
                c.execute("SELECT hydration_interval, break_interval FROM user_settings WHERE id = 1")
                hydration_interval, break_interval = c.fetchone()
                self.hydration_entry.setText(str(hydration_interval))
                self.break_entry.setText(str(break_interval))
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        
    def save_settings(self):
        try:
            hydration = int(self.hydration_entry.text()) if self.hydration_entry.text() else DEFAULT_HYDRATION_INTERVAL
            break_time = int(self.break_entry.text()) if self.break_entry.text() else DEFAULT_BREAK_INTERVAL
            
            try:
                with sqlite3.connect("health_tracker.db") as conn:
                    c = conn.cursor()
                    c.execute("UPDATE user_settings SET hydration_interval = ?, break_interval = ? WHERE id = 1",
                            (hydration, break_time))
                    conn.commit()
            except sqlite3.Error as e:
                print(f"Database error: {e}")
            
            self.accept()
        except ValueError:
            QMessageBox.warning(self, "Invalid Input", "Please enter valid numbers for intervals.")

# Main Window
class HealthTracker(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Health Tracker")
        self.setGeometry(50, 50, 1500, 740)
        self.last_log_time = time.time()
        self.theme = "Light"
        
        # Initialize posture detector
        self.posture_detector = PostureDetector()
        if not self.posture_detector.initialize_camera():
            QMessageBox.critical(self, "Error", "Could not initialize camera")
            sys.exit(1)
        
        # State variables
        self.running = False
        self.start_time = None
        
        # Create main layout
        self.main_layout = QHBoxLayout()
        
        # Left frame for video feed and posture feedback
        self.left_frame = QWidget()
        self.left_layout = QVBoxLayout()
        self.left_frame.setLayout(self.left_layout)
        
        # Video feed
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setScaledContents(True)
        self.video_label.setStyleSheet("""
            QLabel {
                border-radius: 20px;
                background-color: #C8E0EC;
                padding: 10px;
                border: 5px solid #C8E0EC;
            }
        """)
        self.video_label.setFixedSize(940, 560)
        self.left_layout.addWidget(self.video_label)
        
        # Posture feedback label
        self.posture_feedback = QLabel("Posture Status: Analyzing...")
        self.posture_feedback.setStyleSheet("""
            QLabel {
                background-color: grey;
                border-radius: 20px;
                padding: 10px;
                font-size: 20px;
                color: white;
                font-weight: bold;
            }
        """)
        self.left_layout.addWidget(self.posture_feedback)
        
        # Game status label
        self.game_status = QLabel("Game Status: Not Running")
        self.game_status.setStyleSheet("""
            QLabel {
                font-size: 20px;
                padding:10px;        
                color: grey;
                font-weight: bold;

            }
        """)
        # self.right_layout.addWidget(self.game_status)
        self.left_layout.addWidget(self.game_status)
        # Right frame for controls and logs
        self.right_frame = QWidget()
        self.right_frame.setFixedWidth(550)
        self.right_layout = QVBoxLayout()
        self.right_frame.setLayout(self.right_layout)
        
        # Session timer
        self.timer_label = QLabel("Session Timer: 0 seconds")
        self.timer_label.setStyleSheet("""
            QLabel {
                padding: 5px;
                font-size: 20px;
                color: Black;
                font-weight: bold;
            }
        """)
        self.right_layout.addWidget(self.timer_label)
        
        # Button layout
        button_layout = QHBoxLayout()
        
        # Start button
        self.start_button = QPushButton("Start")
        self.start_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border-radius: 15px;
                padding: 10px 30px;
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
        self.start_button.clicked.connect(self.start_session)
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
                font-weight: bold;
                border: 2px solid #f44336;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
            QPushButton:pressed {
                background-color: #b71c1c;
            }
        """)
        self.stop_button.clicked.connect(self.stop_session)
        button_layout.addWidget(self.stop_button)
        
        self.right_layout.addLayout(button_layout)
        
        # Logs Viewer
        self.logs_label = QLabel("Recent Logs:")
        self.logs_label.setFixedHeight(30)

        self.logs_label.setStyleSheet("""
            QLabel {
                background-color: grey;
                border-radius: 10px;
                padding: 5px;
                font-size: 18px;
                color: black;
                font-weight: bold;
            }
        """)
        self.right_layout.addWidget(self.logs_label)
        
        self.log_list = QListWidget()
        self.log_list.setMinimumHeight(300)
        self.right_layout.addWidget(self.log_list, stretch=1)
        self.log_list.setStyleSheet("""
            QListWidget {
                background-color: #b6d9c9;
                border-radius: 15px;
                padding: 3px;
                font-size: 15px;
                color: black;
                font-weight: bold;
                border: 2px solid #4CAF50;
            }
            QListWidget::item {
                background-color: #b6d9c9;
            }
            QListWidget::item:alternate {
                background-color: #a8c9b9;
            }
            QListWidget::item:hover {
                background-color: #4CAF50;
                color: black;
            }
                QListWidget::horizontal-scrollbar {
                background-color: #b6d9c9;
                width: 5px;
                margin: 0px;
            }
            QListWidget::vertical-scrollbar {
                background-color: #b6d9c9;
                width: 10px;
                margin: 0px;
            }
             QListWidget::vertical-scrollbar:: handle {
                background-color: #b6d9c9;
                width: 5px;
                margin: 0px;
            }
            QListWidget::vertical-scrollbar::handle {
                background-color: #4CAF50;
                border-radius: 5px;
            }
        """)
        self.right_layout.addWidget(self.log_list)
    
        
        # Other buttons layout
        other_buttons_layout = QGridLayout()
        other_buttons_layout.setVerticalSpacing(10)
        other_buttons_layout.setHorizontalSpacing(10)
        
        # Settings button
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
        other_buttons_layout.addWidget(self.settings_button, 0, 0)
        
        # Progress button
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
        other_buttons_layout.addWidget(self.progress_button, 0, 1)
        
        # Dark mode button
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
        other_buttons_layout.addWidget(self.dark_mode_button, 1, 1)
        
        # Remove Export button and add Visualize Dashboard button
        self.visualize_button = QPushButton("Visualize Dashboard")
        self.visualize_button.setStyleSheet("""
            QPushButton {
                background-color: #3498db;
                color: white;
                border-radius: 15px;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #3498db;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #2471a3;
            }
        """)
        self.visualize_button.clicked.connect(self.open_dashboard)
        other_buttons_layout.addWidget(self.visualize_button, 1, 0)

        self.right_layout.addLayout(other_buttons_layout)
        
        # Add frames to main layout
        self.main_layout.addWidget(self.left_frame)
        self.main_layout.addWidget(self.right_frame)
        
        # Central widget
        self.central_widget = QWidget()
        self.central_widget.setLayout(self.main_layout)
        self.setCentralWidget(self.central_widget)
        
        # Start video feed
        self.start_video_feed()
        
        # Start reminder thread
        self.reminder_thread = ReminderWorker()
        self.reminder_thread.notification_sent.connect(self.handle_notification)
        self.reminder_thread.start()
        
        # Timer for session updates
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)
        
        # Timer for logs update
        self.logs_timer = QTimer()
        self.logs_timer.timeout.connect(self.update_logs)
        self.logs_timer.start(5000)  # Update logs every 5 seconds
        
        # Initial logs update
        self.update_logs()
        
        # Apply initial styles
        self.apply_styles()
    
    def apply_styles(self):
        if self.theme == "Light":
            self.setStyleSheet("""
                QMainWindow { background-color: #f0f0f0; }
                QLabel { font-size: 14px; color: #333; }
                QListWidget { background-color: white; border-radius: 10px; padding: 10px; border: 1px solid #ccc; }
                QLineEdit { border-radius: 10px; padding: 5px; border: 1px solid #ccc; }
                QProgressBar { border-radius: 5px; text-align: center; }
                QProgressBar::chunk { background-color: #4CAF50; border-radius: 5px; }
            """)
        else:
            self.setStyleSheet("""
                QMainWindow { background-color: #333; }
                QLabel { font-size: 14px; color: white; }
                QListWidget { background-color: #444; color: white; border-radius: 10px; padding: 10px; border: 1px solid #555; }
                QLineEdit { border-radius: 10px; padding: 5px; border: 1px solid #555; }
                QProgressBar { border-radius: 5px; text-align: center; }
                QProgressBar::chunk { background-color: #666; border-radius: 5px; }
            """)
    
    def toggle_theme(self):
        self.theme = "Dark" if self.theme == "Light" else "Light"
        self.apply_styles()
    
    def start_video_feed(self):
        self.video_thread = VideoWorker(self.posture_detector)
        self.video_thread.frame_ready.connect(self.update_frame)
        self.video_thread.start()
    
    def update_frame(self, pixmap, feedback, back_angle, forward_lean, shoulder_diff):
        self.video_label.setPixmap(pixmap)
        self.posture_feedback.setText(f"Posture Status: {feedback}")
        # Log aggregated data every 30 seconds
        current_time = time.time()
        if current_time - self.last_log_time >= 30 and self.running:
            aggregated_posture = self.posture_detector.get_aggregated_posture()
            title, exe = get_foreground_app()
            game_name = exe or title or "Unknown"
            log_posture_data(aggregated_posture, back_angle, forward_lean, shoulder_diff, game_name)
            self.last_log_time = current_time
    
    def start_session(self):
        if not self.running:
            self.running = True
            self.start_time = time.time()
            self.timer.start(1000)  # Update every second
            log_action(back_angle=0, forward_lean=0, shoulder_alignment=0, good_posture=1, forward_lean_flag=0, uneven_shoulders_flag=0, session_status="Started")
            self.update_logs()
    
    def stop_session(self):
        if self.running:
            self.running = False
            self.timer.stop()
            log_action(back_angle=0, forward_lean=0, shoulder_alignment=0, good_posture=0, forward_lean_flag=0, uneven_shoulders_flag=0, session_status="Stopped")
            self.update_logs()
    
    def update_timer(self):
        if self.running and self.start_time is not None:
            elapsed = int(time.time() - self.start_time)
            self.timer_label.setText(f"Session Timer: {elapsed} seconds")
            
            title, exe = get_foreground_app()
            game_name = exe or title or "Unknown"
            if game_name and game_name != "Unknown":
                self.game_status.setText(f"Game Status: Running ({game_name})")
                self.game_status.setStyleSheet("color: green; font-size:20; font-weight:bold;")
            else:
                self.game_status.setText("Game Status: Not Running")
                self.game_status.setStyleSheet("color: red;font-size:20; font-weight:bold;")
    
    def update_logs(self):
        try:
            with sqlite3.connect("health_tracker.db") as conn:
                c = conn.cursor()
                c.execute("SELECT id, timestamp, good_posture, forward_lean_flag, uneven_shoulders_flag, back_angle, forward_lean, shoulder_alignment, session_status, game FROM detailed_logs ORDER BY id DESC LIMIT 8")
                rows = c.fetchall()
                self.log_list.clear()
                for row in rows:
                    # Unpack fields
                    _id, timestamp, good_posture, forward_lean_flag, uneven_shoulders_flag, back_angle, forward_lean, shoulder_alignment, session_status, game = row
                    # Parse time for display
                    try:
                        time_str = datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S").strftime("%H:%M")
                    except Exception:
                        time_str = timestamp
                    # Build friendly message (mutually exclusive)
                    if session_status == "Started":
                        msg = f"🟢 Session started at {time_str} ({game or 'Unknown app'})"
                    elif session_status == "Stopped":
                        msg = f"🔴 Session stopped at {time_str} ({game or 'Unknown app'})"
                    elif forward_lean_flag and uneven_shoulders_flag:
                        msg = f"⚠️ FL & US detected in {game or 'Unknown app'} at {time_str}"
                    elif forward_lean_flag:
                        msg = f"⚠️ Forward lean detected in {game or 'Unknown app'} at {time_str}"
                    elif uneven_shoulders_flag:
                        msg = f"⚠️ Uneven shoulders detected in {game or 'Unknown app'} at {time_str}"
                    elif good_posture:
                        msg = f"✅ Good posture in {game or 'Unknown app'} at {time_str}"
                    else:
                        msg = f"ℹ️ Posture event in {game or 'Unknown app'} at {time_str}"
                    self.log_list.addItem(msg)
        except sqlite3.Error as e:
            print(f"Database error: {e}")
    
    def handle_notification(self, message, notification_type, game_running):
        if game_running:
            item = QListWidgetItem(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}")
            if notification_type == "hydration":
                item.setForeground(QColor("blue"))
            else:  # break
                item.setForeground(QColor("purple"))
            self.log_list.insertItem(0, item)
    
    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec()
    
    def show_graph(self):
        try:
            with sqlite3.connect("health_tracker.db") as conn:
                c = conn.cursor()
                c.execute("SELECT id, timestamp, good_posture, forward_lean_flag, uneven_shoulders_flag, back_angle, forward_lean, shoulder_alignment, session_status, game FROM detailed_logs")
                data = c.fetchall()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            data = []

        if not data:
            QMessageBox.information(self, "No Data", "No data available to display.")
            return

        timestamps = [datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S") for row in data]
        back_angles = [row[5] for row in data]
        forward_leans = [row[6] for row in data]
        shoulder_alignments = [row[7] for row in data]
        good_postures = [row[2] for row in data]
        forward_lean_flags = [row[3] for row in data]
        uneven_shoulders_flags = [row[4] for row in data]
        session_statuses = [row[8] for row in data]
        games = [row[9] for row in data]

        plt.figure(figsize=(10, 5))
        plt.plot(timestamps, back_angles, label="Back Angle")
        plt.plot(timestamps, forward_leans, label="Forward Lean")
        plt.plot(timestamps, shoulder_alignments, label="Shoulder Alignment")
        plt.title("Posture Data Over Time")
        plt.xlabel("Time")
        plt.ylabel("Value")
        plt.legend()
        plt.tight_layout()
        plt.show()
    
    def closeEvent(self, event):
        self.cleanup()
        event.accept()
    
    def cleanup(self):
        # Clean up all resources and threads on app exit
        print("[HealthTracker] Cleaning up resources...")
        self.video_thread.stop()
        self.reminder_thread.stop()
        self.posture_detector.release()
        self.timer.stop()
        self.logs_timer.stop()
        print("[HealthTracker] Cleanup complete.")

    def open_dashboard(self):
        try:
            # Use sys.executable to ensure the same Python environment
            script_path = os.path.join(os.path.dirname(__file__), 'PlotlyGraphs.py')
            subprocess.run([sys.executable, script_path], check=True)
            # Open the generated HTML file in the default browser
            html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'advanced_gaming_health_insights.html'))
            if not os.path.exists(html_path):
                QMessageBox.critical(self, "Dashboard Error", "Dashboard HTML file was not generated.")
                return
            webbrowser.open(f'file://{html_path}')
        except Exception as e:
            QMessageBox.critical(self, "Dashboard Error", f"Failed to open dashboard: {e}")

# Enhanced posture logging function
def log_posture_data(feedback, back_angle, forward_lean, shoulder_diff, game_name=None):
    """
    Log posture data with new flag columns.
    """
    # Default all flags to 0
    good_posture = 0
    forward_lean_flag = 0
    uneven_shoulders_flag = 0
    if feedback:
        feedback_lower = feedback.lower()
        if "good" in feedback_lower:
            good_posture = 1
        if "forward" in feedback_lower:
            forward_lean_flag = 1
        if "uneven" in feedback_lower or "shoulder" in feedback_lower:
            uneven_shoulders_flag = 1
    # If good posture, override others
    if good_posture:
        forward_lean_flag = 0
        uneven_shoulders_flag = 0
    log_action(
        back_angle=back_angle,
        forward_lean=forward_lean,
        shoulder_alignment=shoulder_diff,
        good_posture=good_posture,
        forward_lean_flag=forward_lean_flag,
        uneven_shoulders_flag=uneven_shoulders_flag,
        session_status="Running",
        game=game_name
    )

def main():
    if getattr(sys, 'frozen', False):
        print('[DEBUG] Running in PyInstaller packaged mode')
        os.environ['MEDIAPIPE_DISABLE_GPU'] = '1'
    
    setup_database()
    
    app = QApplication(sys.argv)
    window = HealthTracker()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
