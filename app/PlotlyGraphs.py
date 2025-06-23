import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import scipy.stats as stats
from itertools import groupby

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
        # --- Compute Top 3 Insights ---
        insights = []
        good_pct = self.data['good_posture'].mean() * 100
        worst_game = self.data.groupby('game')['Posture_Risk_Score'].mean().idxmax()
        best_streak = max([sum(1 for _ in g) for k, g in groupby(self.data['good_posture']) if k == 1])
        insights.append(f"Good posture rate: {good_pct:.1f}%")
        insights.append(f"Game with most posture risk: {worst_game}")
        insights.append(f"Longest good posture streak: {best_streak} sessions")

        fig = make_subplots(
            rows=5, cols=3,
            specs=[
                [{'colspan': 3}, None, None],  # Top 3 Insights annotation
                [{'type': 'domain'}, {'type': 'xy'}, None],
                [{'type': 'box'}, {'type': 'heatmap'}, None],
                [{'type': 'xy'}, {'type': 'xy'}, None],
                [{'type': 'xy'}, {'type': 'xy'}, None]
            ],
            subplot_titles=(
                "Top 3 Insights",
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
        # Top 3 Insights annotation
        fig.add_annotation(
            text="<b>Top 3 Insights</b><br>" + "<br>".join(insights),
            xref="paper", yref="paper",
            x=0.5, y=1.15, showarrow=False, font=dict(size=18, color="black"),
            align="center", bordercolor="black", borderwidth=1, bgcolor="#f0f8ff"
        )
        # 1. Posture Distribution (Pie)
        posture_counts = self.data['good_posture'].replace({1: 'Good', 0: 'Bad'}).value_counts()
        fig.add_trace(
            go.Pie(labels=posture_counts.index, values=posture_counts.values, hole=0.3, marker=dict(colors=["#90ee90" if l=="Good" else "#ff7f7f" for l in posture_counts.index])),
            row=2, col=1
        )
        fig.add_annotation(text="Green = Good posture, Red = Bad posture", x=0.15, y=0.85, xref="paper", yref="paper", showarrow=False, font=dict(size=12, color="gray"))
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
                colorscale='Viridis',
                colorbar=dict(title="Avg. Risk Score")
            ),
            row=2, col=2
        )
        fig.add_annotation(text="Darker = higher posture risk for that game", x=0.55, y=0.85, xref="paper", yref="paper", showarrow=False, font=dict(size=12, color="gray"))
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
            row=3, col=1
        )
        fig.add_annotation(text="Lower is better. Spikes = slouching.", x=0.15, y=0.65, xref="paper", yref="paper", showarrow=False, font=dict(size=12, color="gray"))
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
            fig.add_trace(box, row=3, col=2)
        # 5. Back Angle Over Time (Line)
        back_angle_rolling = self.data['back_angle'].rolling(window=10).mean()
        fig.add_trace(
            go.Scatter(
                x=self.data['timestamp'],
                y=back_angle_rolling,
                mode='lines',
                line=dict(color='green', width=2),
                name='Back Angle (Rolling Mean)'
            ),
            row=4, col=1
        )
        fig.add_annotation(text="Aim for >170°. Lower = slouching.", x=0.15, y=0.45, xref="paper", yref="paper", showarrow=False, font=dict(size=12, color="gray"))
        # 6. Shoulder Alignment Over Time (Line)
        shoulder_angle_rolling = self.data['shoulder_alignment'].rolling(window=10).mean()
        fig.add_trace(
            go.Scatter(
                x=self.data['timestamp'],
                y=shoulder_angle_rolling,
                mode='lines',
                line=dict(color='purple', width=2),
                name='Shoulder Alignment (Rolling Mean)'
            ),
            row=4, col=2
        )
        fig.add_annotation(text="Fluctuations = uneven shoulders.", x=0.55, y=0.45, xref="paper", yref="paper", showarrow=False, font=dict(size=12, color="gray"))
        # 7. Hourly Gaming Intensity (Heatmap)
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
                colorscale='YlOrRd',
                colorbar=dict(title="Avg. Risk Score")
            ),
            row=5, col=1
        )
        fig.add_annotation(text="Red = higher risk. See which hours are worst.", x=0.15, y=0.25, xref="paper", yref="paper", showarrow=False, font=dict(size=12, color="gray"))
        # 8. Longest Good Posture Streak (Bar)
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
            row=5, col=2
        )
        fig.add_annotation(text="Higher = better. Shows consistency.", x=0.55, y=0.25, xref="paper", yref="paper", showarrow=False, font=dict(size=12, color="gray"))
        fig.update_layout(
            height=2000,
            width=1800,
            title_text="Advanced Gaming Health Insights",
            showlegend=False,
            template='plotly_white'
        )
        axis_configs = [
            (3, 1, "Time", "Forward Lean"),
            (3, 2, "Game", "Forward Lean"),
            (4, 1, "Time", "Back Angle"),
            (4, 2, "Time", "Shoulder Alignment"),
            (5, 1, "Hour", "Day"),
            (5, 2, "Game", "Longest Good Posture Streak")
        ]
        for row, col, x_title, y_title in axis_configs:
            fig.update_xaxes(title_text=x_title, row=row, col=col)
            fig.update_yaxes(title_text=y_title, row=row, col=col)
        fig.write_html("advanced_gaming_health_insights.html")
        fig.show()

    def generate_comprehensive_health_report(self):
        # --- User-friendly, actionable report ---
        good_pct = self.data['good_posture'].mean() * 100
        avg_risk = self.data['Posture_Risk_Score'].mean()
        worst_game = self.data.groupby('game')['Posture_Risk_Score'].mean().idxmax()
        best_game = self.data.groupby('game')['Posture_Risk_Score'].mean().idxmin()
        best_streak = max([sum(1 for _ in g) for k, g in groupby(self.data['good_posture']) if k == 1])
        hour_worst = self.data.groupby('Hour')['Posture_Risk_Score'].mean().idxmax()
        hour_best = self.data.groupby('Hour')['Posture_Risk_Score'].mean().idxmin()
        print("\n===== Personalized Health Report =====\n")
        print(f"Your good posture rate: {good_pct:.1f}%. {'Great job!' if good_pct > 80 else 'Aim for 80%+ for best health.'}")
        print(f"Average posture risk score: {avg_risk:.2f} (lower is better).")
        print(f"Game with highest posture risk: {worst_game}. Try to be more mindful during this game.")
        print(f"Game with best posture: {best_game}. Keep it up!")
        print(f"Longest streak of good posture: {best_streak} sessions. Consistency is key!")
        print(f"Your worst posture hour: {hour_worst}:00. Consider taking breaks or adjusting your setup then.")
        print(f"Your best posture hour: {hour_best}:00. Try to model other hours after this.")
        print("\n--- Recommendations ---")
        if good_pct < 80:
            print("- Try to keep your good posture above 80%. Set reminders or adjust your chair/monitor.")
        if avg_risk > 2:
            print("- Your average risk is high. Take more frequent breaks and stretch.")
        if best_streak < 10:
            print("- Work on building longer streaks of good posture. Consistency matters!")
        print("- Review the dashboard for your most problematic games and times, and focus on improving there.")
        print("- Remember: Small, consistent improvements beat big, unsustainable changes.")
        print("\nFor more details, see the interactive dashboard (advanced_gaming_health_insights.html).\n")

def main():
    visualizer = HealthInsightsVisualizer()
    if visualizer.load_and_prepare_data():
        visualizer.create_comprehensive_health_dashboard()
        visualizer.generate_comprehensive_health_report()
    else:
        print("Failed to process health data.")

if __name__ == "__main__":
    main()