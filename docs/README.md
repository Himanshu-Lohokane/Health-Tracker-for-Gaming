# Health Tracker for Gaming

A modular, database-driven health tracking system for gamers, featuring posture detection, game detection, reminders, ML analysis, and advanced analytics dashboards.

## Features
- Real-time posture and session logging to SQLite database
- Modular codebase with robust schema: `id, timestamp, good_posture, forward_lean_flag, uneven_shoulders_flag, back_angle, forward_lean, shoulder_alignment, session_status, game`
- Interactive Plotly dashboard with:
  - Posture distribution
  - Game performance intensity
  - Forward lean, back angle, and shoulder alignment trends
  - Hourly gaming intensity
  - Longest good posture streak per game
- Tkinter GUI for viewing logs in a scrollable table
- Comprehensive test suite

## Setup
1. Clone the repo and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. (Optional) Delete `health_tracker.db` for a fresh start.

## Usage
- **Run the main app:**
  ```bash
  python app/main3.py
  ```
- **Generate the analytics dashboard:**
  ```bash
  python app/PlotlyGraphs.py
  ```
  This will create and open `advanced_gaming_health_insights.html`.
- **View logs in a GUI:**
  ```bash
  python display_db/gui_display.py
  ```

## Contributing
- Ensure all code and tests use the new schema.
- Run and update tests in `tests/` as needed.
- See `.gitignore` for files to exclude from version control.

## License
MIT

## 🚀 Features
- Real-time posture detection using webcam (MediaPipe)
- Foreground app detection
- Smart notifications for hydration and breaks
- Points system to gamify healthy habits
- Detailed health logs (posture, hydration, breaks, game, etc.)
- Machine learning analysis (fatigue prediction, anomaly detection)
- Visualizations (matplotlib, plotly, seaborn)
- PyQt6 GUI with light/dark themes
- Data export to CSV
- Modular, testable codebase

## 📁 Project Structure
```
app/              # Main application code (main3.py is the entry point)
data/             # Data creation scripts, test data
visualizations/   # Visualization scripts (matplotlib, plotly, etc.)
tests/            # Unit and integration tests
docs/             # Documentation (including this README)
```

## 🏁 How to Run

### 1. Install Requirements
```
pip install -r requirements.txt
```

### 2. Start the Application
```
python app/main3.py
```

### 3. Run Tests
```
python tests/test_logging.py
python tests/integration_test.py
```

### 4. Data Creation (for testing/visualization)
```
python data/data_inserter_for_testing.py
```

## 📊 Visualizations
- See `visualizations/` for scripts to generate charts and ML insights from your data.
- Export logs from the app for external analysis.

## 🛠️ Developer Notes
- All main logic is in `app/main3.py`.
- All tests import from `app/main3.py` and `app/posture_detection.py`.
- Data is stored in `health_tracker.db` (SQLite).
- To reset your data, delete the `.db` file and restart the app.
- **PostureDetector headless mode:**
    - The `PostureDetector` class has a `headless` flag (default: `False`).
    - In the main app, always use the default (`headless=False`) to enable GUI features (QImage/QPixmap for video display).
    - In tests or headless environments, use `PostureDetector(headless=True)` to skip GUI object creation and avoid errors when no `QGuiApplication` is running.
    - Only the integration test uses `headless=True`. All app code uses the default.

## 🗄️ Database Schema & Config Options

### Database Tables

**health_logs**
| Field      | Type    | Description                |
|------------|---------|----------------------------|
| id         | INTEGER | Primary key                |
| timestamp  | TEXT    | Log timestamp              |
| action     | TEXT    | Action/description         |

**user_settings**
| Field              | Type    | Description                        |
|--------------------|---------|------------------------------------|
| id                 | INTEGER | Primary key                        |
| hydration_interval | INTEGER | Hydration reminder interval (min)  |
| break_interval     | INTEGER | Break reminder interval (min)      |

**user_points**
| Field  | Type    | Description         |
|--------|---------|---------------------|
| id     | INTEGER | Primary key         |
| points | INTEGER | User's health points|

**detailed_logs**
| Field                | Type    | Description                                 |
|----------------------|---------|---------------------------------------------|
| id                   | INTEGER | Primary key                                 |
| timestamp            | TEXT    | Log timestamp                               |
| good_posture         | INTEGER | 1 if posture is good, else 0                |
| forward_lean_flag    | INTEGER | 1 if forward lean detected, else 0           |
| uneven_shoulders_flag| INTEGER | 1 if uneven shoulders detected, else 0       |
| back_angle           | REAL    | Back angle (degrees)                        |
| forward_lean         | REAL    | Forward lean value                          |
| shoulder_alignment   | REAL    | Shoulder alignment value                    |
| session_status       | TEXT    | Session status (Started/Running/Stopped)      |
| game                 | TEXT    | Foreground application/process name          |

*All logging, UI, and tests now use this schema and order. Legacy columns are removed.*

### Config Options (app/config.py)

| Name                    | Default | Description                                      |
|-------------------------|---------|--------------------------------------------------|
| DEFAULT_HYDRATION_INTERVAL | 15      | Hydration reminder interval (minutes)             |
| DEFAULT_BREAK_INTERVAL     | 30      | Break reminder interval (minutes)                 |
| POSTURE_BUFFER_SIZE        | 30      | Number of posture feedbacks to aggregate          |
| MOTION_THRESHOLD           | 50      | Fallback movement threshold for posture detection |

**To change config values:**
- Edit `app/config.py` and adjust the constants as needed.
- Restart the app for changes to take effect.

## 📚 Documentation
- See `docs/`

## Logging Schema (2025-06)

detailed_logs table columns (in order):
1. id
2. timestamp
3. good_posture (0/1)
4. forward_lean_flag (0/1)
5. uneven_shoulders_flag (0/1)
6. back_angle (float)
7. forward_lean (float)
8. shoulder_alignment (float)
9. session_status (text)
10. game (text)

- All posture logs are now structured with these flags.
- No more text-based posture status or action columns.
- All code, UI, and exports use this order.

## Posture Flag Meanings
- good_posture: 1 if posture is good, else 0
- forward_lean_flag: 1 if forward lean detected, else 0
- uneven_shoulders_flag: 1 if uneven shoulders detected, else 0

## Refactor Summary
- Database and all code now use only these columns.
- All legacy columns and logic removed.
- Integration and logging tests updated.

- The app now logs the foreground application (window/process) at each logging interval (every 30 seconds), not a hardcoded list of apps.
- All legacy logic for specific app lists has been removed.