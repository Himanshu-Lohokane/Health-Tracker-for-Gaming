import sqlite3
import tkinter as tk
from tkinter import ttk

COLUMNS = [
    "id", "timestamp", "good_posture", "forward_lean_flag", "uneven_shoulders_flag",
    "back_angle", "forward_lean", "shoulder_alignment", "session_status", "game"
]

class DBViewer(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Health Tracker DB Viewer")
        self.geometry("1200x500")
        self.resizable(True, True)
        self.create_widgets()
        self.load_data()

    def create_widgets(self):
        frame = ttk.Frame(self)
        frame.pack(fill=tk.BOTH, expand=True)
        self.tree = ttk.Treeview(frame, columns=COLUMNS, show="headings")
        for col in COLUMNS:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="center")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscroll=vsb.set, xscroll=hsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        refresh_btn = ttk.Button(self, text="Refresh", command=self.load_data)
        refresh_btn.pack(pady=5)

    def load_data(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        conn = sqlite3.connect("health_tracker.db")
        c = conn.cursor()
        c.execute(f'''SELECT {', '.join(COLUMNS)} FROM detailed_logs ORDER BY id DESC LIMIT 50''')
        rows = c.fetchall()
        conn.close()
        for row in rows:
            self.tree.insert("", tk.END, values=row)

if __name__ == "__main__":
    app = DBViewer()
    app.mainloop() 