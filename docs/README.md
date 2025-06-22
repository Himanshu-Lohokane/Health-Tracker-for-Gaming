# Health Tracker for Gaming

A modern desktop application to help gamers maintain healthy habits by tracking posture, hydration, and break reminders, with real-time posture detection, game awareness, and insightful visualizations.

## 🚀 Features
- Real-time posture detection using webcam (MediaPipe)
- Game detection (Valorant, CS:GO, League, etc.)
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

## 📚 Documentation
- See `docs/`