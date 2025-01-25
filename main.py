# prachi.py
import time
import threading
import sqlite3
import csv
import random
from tkinter import *
from tkinter import messagebox
from plyer import notification
from win10toast import ToastNotifier
import psutil
import matplotlib.pyplot as plt
from datetime import datetime
from posture_detection import PostureDetector  # Import the PostureDetector class

# Database setup
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

# Insert log into database
def log_action(action, posture_status=None, back_angle=None, water_intake=None, break_taken=None, activity=None, forward_lean=None, shoulder_alignment=None, session_status=None, game=None):
    conn = sqlite3.connect("health_tracker.db")
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

class Overlay:
    def __init__(self, root):
        self.root = root
        self.root.title("Health Tracker")
        self.root.geometry("1200x700+50+50")  # Increased window size
        self.root.configure(bg="#f0f0f0")
        self.root.resizable(False, False)
        self.last_log_time = time.time()  # Add this line

        self.theme = StringVar(value="Light")
        
        # Create left and right frames
        self.left_frame = Frame(root, bg="#f0f0f0")
        self.left_frame.pack(side=LEFT, padx=10, pady=10)
        
        self.right_frame = Frame(root, bg="#f0f0f0")
        self.right_frame.pack(side=RIGHT, padx=10, pady=10)

        # Initialize PostureDetector
        self.posture_detector = PostureDetector()
        if not self.posture_detector.initialize_camera():
            messagebox.showerror("Error", "Could not initialize camera")
            return

        # Video feed frame (in left frame)
        self.video_label = Label(self.left_frame)
        self.video_label.pack()
        
        # Posture feedback label
        self.posture_feedback = Label(self.left_frame, text="Posture Status: Analyzing...", 
                                    font=("Arial", 12), bg="#f0f0f0")
        self.posture_feedback.pack(pady=10)

        # Right frame components
        self.label = Label(self.right_frame, text="Session Timer: 0 seconds", 
                          font=("Arial", 12), bg="#f0f0f0")
        self.label.pack(pady=10)

        self.game_status = Label(self.right_frame, text="Game Status: Not Running", 
                               font=("Arial", 10), bg="#f0f0f0", fg="green")
        self.game_status.pack(pady=5)

        # Control buttons
        self.button_frame = Frame(self.right_frame, bg="#f0f0f0")
        self.button_frame.pack(pady=10)

        self.start_button = Button(self.button_frame, text="Start", command=self.start, 
                                 bg="#4caf50", fg="white")
        self.start_button.grid(row=0, column=0, padx=5)

        self.stop_button = Button(self.button_frame, text="Stop", command=self.stop, 
                                bg="#f44336", fg="white")
        self.stop_button.grid(row=0, column=1, padx=5)

        # Rest of your existing UI components in right frame
        self.setup_right_frame_components()

        self.running = False
        self.start_time = None
        
        # Start video update
        self.update_video()

    def setup_right_frame_components(self):
        # Logs Viewer
        self.logs_label = Label(self.right_frame, text="Recent Logs:", 
                              font=("Arial", 10), bg="#f0f0f0")
        self.logs_label.pack()

        self.log_list = Listbox(self.right_frame, height=8, width=50)
        self.log_list.pack(pady=5)

        self.scrollbar = Scrollbar(self.right_frame, orient=VERTICAL, 
                                 command=self.log_list.yview)
        self.log_list.config(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")

        # Add your other existing buttons and components here
        self.settings_button = Button(self.right_frame, text="Customize Settings", 
                                    command=self.open_settings, bg="#2196f3", fg="white")
        self.settings_button.pack(pady=10)

        self.progress_button = Button(self.right_frame, text="View Progress", 
                                    command=self.show_graph, bg="#ff9800", fg="white")
        self.progress_button.pack(pady=5)

        self.export_button = Button(self.right_frame, text="Export Logs", 
                                  command=self.export_logs, bg="#673ab7", fg="white")
        self.export_button.pack(pady=5)

        self.dark_mode_button = Button(self.right_frame, text="Toggle Dark Mode", 
                                     command=self.toggle_theme, bg="#9c27b0", fg="white")
        self.dark_mode_button.pack(pady=10)

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
        while self.running:
            elapsed = int(time.time() - self.start_time)
            self.label.config(text=f"Session Timer: {elapsed} seconds")
            game_running, game_name = is_game_running()
            self.game_status.config(
                text=f"Game Status: Running ({game_name})" if game_running else "Game Status: Not Running",
                fg="red" if game_running else "green"
            )
            self.update_logs()
            time.sleep(1)

    def update_logs(self):
        conn = sqlite3.connect("health_tracker.db")
        c = conn.cursor()
        c.execute("SELECT timestamp, action FROM health_logs ORDER BY id DESC LIMIT 8")
        rows = c.fetchall()
        conn.close()

        self.log_list.delete(0, END)
        for row in rows:
            self.log_list.insert(END, f"{row[0]} - {row[1]}")



    def update_video(self):
        current_time = time.time()
        photo, feedback, back_angle, forward_lean, shoulder_diff = self.posture_detector.get_frame()
        
        if photo is not None:
            self.video_label.config(image=photo)
            self.video_label.image = photo
            self.posture_feedback.config(text=f"Posture Status: {feedback}")
            
            # Log aggregated data every 30 seconds
            if current_time - self.last_log_time >= 30:  # 30 seconds interval
                aggregated_posture = self.posture_detector.get_aggregated_posture()
                game_running, game_name = is_game_running()
                log_action(f"Aggregated Posture: {aggregated_posture}", posture_status=feedback, back_angle=back_angle, forward_lean=forward_lean, shoulder_alignment=shoulder_diff, session_status="Running", game=game_name)
                self.last_log_time = current_time
                
        self.root.after(10, self.update_video)



    def open_settings(self):
        settings_window = Toplevel(self.root)
        settings_window.title("Customize Settings")
        settings_window.geometry("300x200")
        settings_window.configure(bg="#f0f0f0")
        settings_window.resizable(False, False)

        Label(settings_window, text="Hydration Reminder Interval (minutes):", bg="#f0f0f0").pack(pady=5)
        hydration_entry = Entry(settings_window)
        hydration_entry.pack(pady=5)

        Label(settings_window, text="Break Reminder Interval (minutes):", bg="#f0f0f0").pack(pady=5)
        break_entry = Entry(settings_window)
        break_entry.pack(pady=5)

        def save_settings():
            conn = sqlite3.connect("health_tracker.db")
            c = conn.cursor()
            c.execute("UPDATE user_settings SET hydration_interval = ?, break_interval = ? WHERE id = 1",
                      (hydration_entry.get() or 15, break_entry.get() or 30))
            conn.commit()
            conn.close()
            settings_window.destroy()

        Button(settings_window, text="Save", command=save_settings, bg="#4caf50", fg="white").pack(pady=10)

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
        conn = sqlite3.connect("health_tracker.db")
        c = conn.cursor()
        c.execute("SELECT * FROM detailed_logs")
        rows = c.fetchall()
        conn.close()

        with open("detailed_health_logs.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["ID", "Timestamp", "Action", "Posture Status", "Back Angle", "Water Intake", "Break Taken", "Activity", "Forward Lean", "Shoulder Alignment", "Session Status", "Game"])
            writer.writerows(rows)
        messagebox.showinfo("Export Success", "Logs exported as detailed_health_logs.csv")

    def toggle_theme(self):
        if self.theme.get() == "Light":
            self.root.configure(bg="#333")
            self.label.config(bg="#333", fg="white")
            self.game_status.config(bg="#333", fg="white")
            self.logs_label.config(bg="#333", fg="white")
            self.theme.set("Dark")
        else:
            self.root.configure(bg="#f0f0f0")
            self.label.config(bg="#f0f0f0", fg="black")
            self.game_status.config(bg="#f0f0f0", fg="black")
            self.logs_label.config(bg="#f0f0f0", fg="black")
            self.theme.set("Light")

    def cleanup(self):
        self.posture_detector.release()
        self.root.destroy()

# Reminder thread function
def reminder_thread():
    conn = sqlite3.connect("health_tracker.db")
    c = conn.cursor()
    c.execute("SELECT hydration_interval, break_interval FROM user_settings WHERE id = 1")
    hydration_interval, break_interval = c.fetchone()
    conn.close()

    hydration_interval *= 60
    break_interval *= 60

    last_hydration_reminder = time.time()
    last_break_reminder = time.time()

    toaster = ToastNotifier()

    while True:
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
                log_action("Break reminder sent", break_taken=1, game=game_name)
                add_points(10)
                last_break_reminder = current_time

        time.sleep(1)

def main():
    setup_database()
    threading.Thread(target=reminder_thread, daemon=True).start()
    
    root = Tk()
    app = Overlay(root)
    root.protocol("WM_DELETE_WINDOW", app.cleanup)  # Proper cleanup on window close
    root.mainloop()

if __name__ == "__main__":
    main()