import sys
import time
import threading
import sqlite3
import csv
import random
from datetime import datetime
import os
import psutil

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

from posture_detection import PostureDetector

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
                         VALUES (1, 15, 30)''')
            c.execute('''INSERT OR IGNORE INTO user_points (id, points)
                         VALUES (1, 0)''')
            conn.commit()
    except sqlite3.Error as e:
        print(f"Database error: {e}")

# Insert log into database
def log_action(action, posture_status=None, back_angle=None, water_intake=None, break_taken=None, 
               activity=None, forward_lean=None, shoulder_alignment=None, session_status=None, game=None):
    try:
        with sqlite3.connect("health_tracker.db") as conn:
            c = conn.cursor()
            c.execute('''INSERT INTO detailed_logs (timestamp, action, posture_status, back_angle, 
                         water_intake, break_taken, activity, forward_lean, shoulder_alignment, 
                         session_status, game)
                         VALUES (datetime('now'), ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                      (action, posture_status, back_angle, water_intake, break_taken, activity, 
                       forward_lean, shoulder_alignment, session_status, game))
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
            hydration_interval, break_interval = 15, 30

        hydration_interval *= 60
        break_interval *= 60

        last_hydration_reminder = time.time()
        last_break_reminder = time.time()

        toaster = ToastNotifier()

        while self.running:
            current_time = time.time()
            game_running, game_name = is_game_running()
            
            if game_running:
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
                    
                    self.notification_sent.emit(f"Hydration reminder sent", "hydration", game_running)
                    log_action("Hydration reminder sent", water_intake=1, game=game_name)
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
                    
                    self.notification_sent.emit(f"Break reminder sent", "break", game_running)
                    log_action("Break reminder sent", break_taken=1, game=game_name)
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
            hydration = int(self.hydration_entry.text()) if self.hydration_entry.text() else 15
            break_time = int(self.break_entry.text()) if self.break_entry.text() else 30
            
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
        
        # Comment out the Export button from the other_buttons_layout
        # Export button
        # self.export_button = QPushButton("Export Logs")
        # self.export_button.setStyleSheet("""
        #     QPushButton {
        #         background-color: #FF9800;
        #         color: white;
        #         border-radius: 15px;
        #         padding: 10px;
        #         font-size: 14px;
        #         font-weight: bold;
        #         border: 2px solid #FF9800;
        #     }
        #     QPushButton:hover {
        #         background-color: #F57C00;
        #     }
        #     QPushButton:pressed {
        #         background-color: #E65100;
        #     }
        # """)
        # self.export_button.clicked.connect(self.export_logs)
        # other_buttons_layout.addWidget(self.export_button, 1, 0)

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
            game_running, game_name = is_game_running()
            log_action(f"Aggregated Posture: {aggregated_posture}", 
                      posture_status=feedback, 
                      back_angle=back_angle, 
                      forward_lean=forward_lean, 
                      shoulder_alignment=shoulder_diff, 
                      session_status="Running", 
                      game=game_name)
            self.last_log_time = current_time
    
    def start_session(self):
        if not self.running:
            self.running = True
            self.start_time = time.time()
            self.timer.start(1000)  # Update every second
            log_action("Session started", session_status="Started")
            self.update_logs()
    
    def stop_session(self):
        if self.running:
            self.running = False
            self.timer.stop()
            log_action("Session stopped", session_status="Stopped")
            self.update_logs()
    
    def update_timer(self):
        if self.running and self.start_time is not None:
            elapsed = int(time.time() - self.start_time)
            self.timer_label.setText(f"Session Timer: {elapsed} seconds")
            
            game_running, game_name = is_game_running()
            if game_running:
                self.game_status.setText(f"Game Status: Running ({game_name})")
                self.game_status.setStyleSheet("color: green; font-size:20; font-weight:bold;")
            else:
                self.game_status.setText("Game Status: Not Running")
                self.game_status.setStyleSheet("color: red;font-size:20; font-weight:bold;")
    
    def update_logs(self):
        try:
            with sqlite3.connect("health_tracker.db") as conn:
                c = conn.cursor()
                c.execute("SELECT timestamp, action FROM detailed_logs ORDER BY id DESC LIMIT 8")
                rows = c.fetchall()
                self.log_list.clear()
                for row in rows:
                    self.log_list.addItem(f"{row[0]} - {row[1]}")
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
                c.execute("SELECT timestamp, action FROM detailed_logs")
                data = c.fetchall()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            data = []

        if not data:
            QMessageBox.information(self, "No Data", "No data available to display.")
            return

        timestamps = [datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S") for row in data]
        actions = [row[1] for row in data]

        plt.figure(figsize=(10, 5))
        plt.plot(timestamps, [actions.count("Hydration reminder sent") for _ in range(len(timestamps))], label="Hydration")
        plt.plot(timestamps, [actions.count("Break reminder sent") for _ in range(len(timestamps))], label="Breaks")
        plt.title("Health Reminders Over Time")
        plt.xlabel("Time")
        plt.ylabel("Count")
        plt.legend()
        plt.tight_layout()
        plt.show()
    
    def closeEvent(self, event):
        self.cleanup()
        event.accept()
    
    def cleanup(self):
        self.video_thread.stop()
        self.reminder_thread.stop()
        self.posture_detector.release()
        self.timer.stop()
        self.logs_timer.stop()

    # Comment out the export_logs method since it is no longer used
    # def export_logs(self):
    #     try:
    #         with sqlite3.connect("health_tracker.db") as conn:
    #             c = conn.cursor()
    #             c.execute("SELECT * FROM detailed_logs")
    #             rows = c.fetchall()
    #     except sqlite3.Error as e:
    #         print(f"Database error: {e}")
    #         rows = []

    #     if not rows:
    #         QMessageBox.information(self, "No Data", "No data available to export.")
    #         return

    #     log_directory = "health_logs"
    #     if not os.path.exists(log_directory):
    #         os.makedirs(log_directory)

    #     timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    #     filename = os.path.join(log_directory, f"detailed_health_logs_{timestamp}.csv")

    #     try:
    #         with open(filename, "w", newline="") as file:
    #             writer = csv.writer(file)
    #             writer.writerow(["ID", "Timestamp", "Action", "Posture Status", "Back Angle", 
    #                            "Water Intake", "Break Taken", "Activity", "Forward Lean", 
    #                            "Shoulder Alignment", "Session Status", "Game"])
    #             writer.writerows(rows)
    #         QMessageBox.information(self, "Export Success", f"Logs exported as {filename}")
    #     except Exception as e:
    #         QMessageBox.critical(self, "Export Error", f"An error occurred while exporting logs: {str(e)}")

def main():
    setup_database()
    
    app = QApplication(sys.argv)
    window = HealthTracker()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
