import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import scipy.stats as stats

DB_PATH = "health_tracker.db"
TABLE = "detailed_logs"

class HealthInsightsVisualizer:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self.data = None

    def load_and_prepare_data(self):
        try:
            # Load data from SQLite DB
            conn = sqlite3.connect(self.db_path)
            self.data = pd.read_sql_query(f"SELECT * FROM {TABLE}", conn)
            conn.close()
            # Parse timestamp
            self.data['timestamp'] = pd.to_datetime(self.data['timestamp'])
            # Fill missing game names
            self.data['game'] = self.data['game'].fillna('Unspecified')
            self._engineer_health_features()
            return True
        except Exception as e:
            print(f"Data preparation error: {e}")
            return False

    def _engineer_health_features(self):
        self.data['Hour'] = self.data['timestamp'].dt.hour
        self.data['Day'] = self.data['timestamp'].dt.day_name()
        self.data['Date'] = self.data['timestamp'].dt.date
        # Posture risk scoring
        def calculate_posture_risk(row):
            risk = 0
            if row['good_posture'] == 0:
                risk += 2
            if row['forward_lean_flag'] == 1:
                risk += 1
            if row['uneven_shoulders_flag'] == 1:
                risk += 1
            if row['forward_lean'] and row['forward_lean'] > 0.1:
                risk += 1
            if row['back_angle'] and row['back_angle'] < 170:
                risk += 1
            return risk
        self.data['Posture_Risk_Score'] = self.data.apply(calculate_posture_risk, axis=1)
        self.data.sort_values('timestamp', inplace=True)
        self.data['Cumulative_Forward_Lean'] = self.data['forward_lean'].cumsum()
        self.data['Cumulative_Posture_Risk'] = self.data['Posture_Risk_Score'].cumsum()
        self.data['Game_Session'] = (self.data['game'] != self.data['game'].shift()).cumsum()

    def create_comprehensive_health_dashboard(self):
        fig = make_subplots(
            rows=4, cols=3,
            specs=[
                [{'type': 'domain'}, {'type': 'xy'}, None],
                [{'type': 'box'}, {'type': 'heatmap'}, None],
                [{'type': 'xy'}, {'type': 'xy'}, None],
                [{'type': 'xy'}, {'type': 'xy'}, None]
            ],
            subplot_titles=(
                "Posture Distribution",
                "Game Performance Intensity",
                "Forward Lean Over Time",
                "Detailed Posture Analysis",
                "Back Angle Over Time",
                "Shoulder Alignment Over Time",
                "Hourly Gaming Intensity",
                "Longest Good Posture Streak"
            )
        )
        color_palette = px.colors.qualitative.Pastel
        # 1. Posture Distribution (Pie)
        posture_counts = self.data['good_posture'].replace({1: 'Good', 0: 'Bad'}).value_counts()
        fig.add_trace(
            go.Pie(labels=posture_counts.index, values=posture_counts.values, hole=0.3, marker=dict(colors=px.colors.qualitative.Set3)),
            row=1, col=1
        )
        # 2. Game Performance Intensity (Heatmap)
        game_posture_intensity = pd.crosstab(
            self.data['game'],
            self.data['good_posture'].replace({1: 'Good', 0: 'Bad'}),
            values=self.data['Posture_Risk_Score'],
            aggfunc='mean'
        )
        fig.add_trace(
            go.Heatmap(
                z=game_posture_intensity.values,
                x=game_posture_intensity.columns,
                y=game_posture_intensity.index,
                colorscale='Viridis'
            ),
            row=1, col=2
        )
        # 3. Forward Lean Over Time (Line)
        forward_lean_rolling = self.data['forward_lean'].rolling(window=10).mean()
        fig.add_trace(
            go.Scatter(
                x=self.data['timestamp'],
                y=forward_lean_rolling,
                mode='lines',
                line=dict(color='blue', width=2),
                name='Forward Lean (Rolling Mean)'
            ),
            row=2, col=1
        )
        # 4. Detailed Posture Analysis (Box Plot for Games)
        game_forward_lean = []
        unique_games = self.data['game'].unique()
        for i, game in enumerate(unique_games):
            game_data = self.data[self.data['game'] == game]['forward_lean']
            game_forward_lean.append(
                go.Box(
                    y=game_data,
                    name=game,
                    marker_color=color_palette[i % len(color_palette)]
                )
            )
        for box in game_forward_lean:
            fig.add_trace(box, row=2, col=2)
        # 5. Back Angle Over Time (Line) - moved to (3, 1)
        back_angle_rolling = self.data['back_angle'].rolling(window=10).mean()
        fig.add_trace(
            go.Scatter(
                x=self.data['timestamp'],
                y=back_angle_rolling,
                mode='lines',
                line=dict(color='green', width=2),
                name='Back Angle (Rolling Mean)'
            ),
            row=3, col=1
        )
        # 6. Shoulder Alignment Over Time (Line) - (3, 2)
        shoulder_angle_rolling = self.data['shoulder_alignment'].rolling(window=10).mean()
        fig.add_trace(
            go.Scatter(
                x=self.data['timestamp'],
                y=shoulder_angle_rolling,
                mode='lines',
                line=dict(color='purple', width=2),
                name='Shoulder Alignment (Rolling Mean)'
            ),
            row=3, col=2
        )
        # 7. Hourly Gaming Intensity (Heatmap) - (4, 1)
        hourly_intensity = self.data.pivot_table(
            index='Day',
            columns='Hour',
            values='Posture_Risk_Score',
            aggfunc='mean'
        )
        fig.add_trace(
            go.Heatmap(
                z=hourly_intensity.values,
                x=hourly_intensity.columns,
                y=hourly_intensity.index,
                colorscale='YlOrRd'
            ),
            row=4, col=1
        )
        # 8. Longest Good Posture Streak (Bar) - (4, 2)
        streaks = []
        for game in unique_games:
            game_data = self.data[self.data['game'] == game]['good_posture']
            max_streak = 0
            current_streak = 0
            for val in game_data:
                if val == 1:
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 0
            streaks.append(max_streak)
        fig.add_trace(
            go.Bar(
                x=list(unique_games),
                y=streaks,
                marker_color=color_palette[:len(unique_games)],
                name='Longest Good Posture Streak'
            ),
            row=4, col=2
        )
        fig.update_layout(
            height=1600,
            width=1600,
            title_text="Advanced Gaming Health Insights",
            showlegend=False,
            template='plotly_white'
        )
        axis_configs = [
            (2, 1, "Time", "Forward Lean"),
            (2, 2, "Game", "Forward Lean"),
            (3, 1, "Time", "Back Angle"),
            (3, 2, "Time", "Shoulder Alignment"),
            (4, 1, "Hour", "Day"),
            (4, 2, "Game", "Longest Good Posture Streak")
        ]
        for row, col, x_title, y_title in axis_configs:
            fig.update_xaxes(title_text=x_title, row=row, col=col)
            fig.update_yaxes(title_text=y_title, row=row, col=col)
        fig.write_html("advanced_gaming_health_insights.html")
        fig.show()

    def generate_comprehensive_health_report(self):
        statistical_insights = {
            "Posture Analysis": {
                "Posture Distribution": self.data['good_posture'].replace({1: 'Good', 0: 'Bad'}).value_counts(normalize=True).to_dict(),
                "Average Posture Risk Score": self.data['Posture_Risk_Score'].mean(),
            },
            "Biomechanical Metrics": {
                "Forward Lean": {
                    "Mean": self.data['forward_lean'].mean(),
                    "Median": self.data['forward_lean'].median(),
                    "Max": self.data['forward_lean'].max(),
                    "Min": self.data['forward_lean'].min()
                },
                "Back Angle": {
                    "Mean": self.data['back_angle'].mean(),
                    "Median": self.data['back_angle'].median(),
                    "Optimal Angle %": (self.data['back_angle'] > 170).mean() * 100
                }
            },
            "Game-wise Insights": {
                game: {
                    "Total Sessions": len(self.data[self.data['game'] == game]),
                    "Average Posture Risk": self.data[self.data['game'] == game]['Posture_Risk_Score'].mean(),
                    "Dominant Posture": self.data[self.data['game'] == game]['good_posture'].replace({1: 'Good', 0: 'Bad'}).mode().iloc[0]
                } for game in self.data['game'].unique()
            }
        }
        import json
        print(json.dumps(statistical_insights, indent=2))
        return statistical_insights

def main():
    visualizer = HealthInsightsVisualizer()
    if visualizer.load_and_prepare_data():
        visualizer.create_comprehensive_health_dashboard()
        visualizer.generate_comprehensive_health_report()
    else:
        print("Failed to process health data.")

if __name__ == "__main__":
    main()