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
        good_pct = self.data['good_posture'].mean() * 100
        worst_game = self.data.groupby('game')['Posture_Risk_Score'].mean().idxmax()
        best_streak = max([sum(1 for _ in g) for k, g in groupby(self.data['good_posture']) if k == 1])
        
        # Create a SIMPLE subplot structure that works
        fig = make_subplots(
            rows=4, cols=2,
            specs=[
                [{'type': 'domain'}, {'type': 'heatmap'}],  # Posture pie + Game intensity heatmap
                [{'type': 'xy'}, {'type': 'box'}],         # Forward lean line + Game box plots
                [{'type': 'xy'}, {'type': 'xy'}],          # Back angle + Shoulder alignment
                [{'type': 'heatmap'}, {'type': 'xy'}]      # Hourly heatmap + Streak bars
            ],
            subplot_titles=(
                "🎯 Posture Distribution",
                "🎮 Game Risk Intensity",
                "📈 Forward Lean Trend", 
                "📊 Game Comparison",
                "📐 Back Angle Trend",
                "👤 Shoulder Alignment",
                "⏰ Hourly Risk Pattern",
                "🏆 Good Posture Streaks"
            ),
            vertical_spacing=0.15,
            horizontal_spacing=0.15
        )
        
        # Modern color palette
        colors = {
            'good': '#2ecc71',
            'bad': '#e74c3c', 
            'primary': '#3498db',
            'secondary': '#9b59b6',
            'accent': '#f39c12'
        }
        
        # 1. Posture Distribution (Pie Chart) - Row 1, Col 1
        posture_counts = self.data['good_posture'].replace({1: 'Good Posture', 0: 'Poor Posture'}).value_counts()
        fig.add_trace(
            go.Pie(
                labels=posture_counts.index,
                values=posture_counts.values,
                hole=0.4,
                marker=dict(
                    colors=[colors['good'], colors['bad']],
                    line=dict(color='white', width=3)
                ),
                textfont=dict(size=14, color='white'),
                hovertemplate="<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>"
            ),
            row=1, col=1
        )
        
        # 2. Game Performance Intensity (Heatmap) - Row 1, Col 2
        game_posture_intensity = pd.crosstab(
            self.data['game'],
            self.data['good_posture'].replace({1: 'Good', 0: 'Poor'}),
            values=self.data['Posture_Risk_Score'],
            aggfunc='mean'
        )
        
        fig.add_trace(
            go.Heatmap(
                z=game_posture_intensity.values,
                x=game_posture_intensity.columns,
                y=game_posture_intensity.index,
                colorscale='RdYlBu_r',
                hovertemplate="<b>%{y}</b><br>Posture: %{x}<br>Risk Score: %{z:.2f}<extra></extra>"
            ),
            row=1, col=2
        )
        
        # 3. Forward Lean Over Time (Line Chart) - Row 2, Col 1
        forward_lean_rolling = self.data['forward_lean'].rolling(window=10).mean()
        if forward_lean_rolling.notna().sum() > 0:
            fig.add_trace(
                go.Scatter(
                    x=self.data['timestamp'],
                    y=forward_lean_rolling,
                    mode='lines+markers',
                    line=dict(color=colors['primary'], width=3),
                    marker=dict(size=5),
                    name='Forward Lean',
                    hovertemplate="<b>%{x}</b><br>Forward Lean: %{y:.3f}<extra></extra>"
                ),
                row=2, col=1
            )
            print('DEBUG: Adding hline to row=2, col=1 (Forward Lean subplot)')
            # Only add hline to cartesian subplot, never to pie chart
            # fig.add_hline(
            #     y=0.1,
            #     line_dash="dash",
            #     line_color=colors['bad'],
            #     annotation_text="Risk Threshold",
            #     row=2, col=1
            # )
        
        # 4. Game Box Plots - Row 2, Col 2
        unique_games = self.data['game'].unique()
        plot_colors = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe']
        
        for i, game in enumerate(unique_games):
            game_data = self.data[self.data['game'] == game]['forward_lean']
            fig.add_trace(
                go.Box(
                    y=game_data,
                    name=game,
                    marker_color=plot_colors[i % len(plot_colors)],
                    showlegend=False,
                    hovertemplate="<b>%{x}</b><br>Forward Lean: %{y:.3f}<extra></extra>"
                ),
                row=2, col=2
            )
        
        # 5. Back Angle Over Time - Row 3, Col 1
        back_angle_rolling = self.data['back_angle'].rolling(window=10).mean()
        if back_angle_rolling.notna().sum() > 0:
            fig.add_trace(
                go.Scatter(
                    x=self.data['timestamp'],
                    y=back_angle_rolling,
                    mode='lines+markers',
                    line=dict(color=colors['good'], width=3),
                    marker=dict(size=5),
                    name='Back Angle',
                    hovertemplate="<b>%{x}</b><br>Back Angle: %{y:.1f}°<extra></extra>"
                ),
                row=3, col=1
            )
            print('DEBUG: Adding hline to row=3, col=1 (Back Angle subplot)')
            # Only add hline to cartesian subplot, never to pie chart
            # fig.add_hline(
            #     y=170,
            #     line_dash="dash",
            #     line_color=colors['accent'],
            #     annotation_text="Good Posture (170°+)",
            #     row=3, col=1
            # )
        
        # 6. Shoulder Alignment - Row 3, Col 2
        shoulder_rolling = self.data['shoulder_alignment'].rolling(window=10).mean()
        fig.add_trace(
            go.Scatter(
                x=self.data['timestamp'],
                y=shoulder_rolling,
                mode='lines+markers',
                line=dict(color=colors['secondary'], width=3),
                marker=dict(size=5),
                name='Shoulder Alignment',
                hovertemplate="<b>%{x}</b><br>Shoulder Alignment: %{y:.3f}<extra></extra>"
            ),
            row=3, col=2
        )
        
        # 7. Hourly Risk Heatmap - Row 4, Col 1
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
                colorscale='Plasma',
                hovertemplate="<b>%{y}</b><br>Hour: %{x}:00<br>Risk Score: %{z:.2f}<extra></extra>"
            ),
            row=4, col=1
        )
        
        # 8. Posture Streaks by Game - Row 4, Col 2
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
                marker=dict(
                    color=streaks,
                    colorscale='Viridis',
                    line=dict(color='white', width=2)
                ),
                showlegend=False,
                hovertemplate="<b>%{x}</b><br>Longest Streak: %{y} sessions<extra></extra>"
            ),
            row=4, col=2
        )
        
        # Update layout with proper spacing
        fig.update_layout(
            height=1800,
            width=1400,
            title_text=f"<b>🎮 Gaming Health Dashboard</b><br><sub>📊 Good Posture: {good_pct:.1f}% | ⚠️ Risk Game: {worst_game} | 🏆 Best Streak: {best_streak}</sub>",
            title_x=0.5,
            title_font_size=20,
            showlegend=False,
            template='plotly_white',
            font=dict(size=12),
            margin=dict(t=200, b=60, l=60, r=60)
        )
        
        # Update axis labels
        fig.update_xaxes(title_text="Time", row=2, col=1)
        fig.update_yaxes(title_text="Forward Lean", row=2, col=1)
        fig.update_xaxes(title_text="Game", row=2, col=2)
        fig.update_yaxes(title_text="Forward Lean", row=2, col=2)
        fig.update_xaxes(title_text="Time", row=3, col=1)
        fig.update_yaxes(title_text="Back Angle (°)", row=3, col=1)
        fig.update_xaxes(title_text="Time", row=3, col=2)
        fig.update_yaxes(title_text="Shoulder Alignment", row=3, col=2)
        fig.update_xaxes(title_text="Hour", row=4, col=1)
        fig.update_yaxes(title_text="Day", row=4, col=1)
        fig.update_xaxes(title_text="Game", row=4, col=2)
        fig.update_yaxes(title_text="Longest Streak", row=4, col=2)
        
        # Add simple, clear annotations that won't overlap
        fig.add_annotation(
            text="🟢 Green = Good Posture | 🔴 Red = Poor Posture",
            x=0.25, y=0.88,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=11, color="gray"),
            bgcolor="rgba(255,255,255,0.8)"
        )
        
        fig.add_annotation(
            text="🔥 Darker Colors = Higher Risk",
            x=0.75, y=0.88,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=11, color="gray"),
            bgcolor="rgba(255,255,255,0.8)"
        )
        
        fig.add_annotation(
            text="📈 Lower Values = Better Posture",
            x=0.25, y=0.65,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=11, color="gray"),
            bgcolor="rgba(255,255,255,0.8)"
        )
        
        fig.add_annotation(
            text="📊 Compare Games Side by Side",
            x=0.75, y=0.65,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=11, color="gray"),
            bgcolor="rgba(255,255,255,0.8)"
        )
        
        fig.add_annotation(
            text="📐 Higher Angle = Better Posture",
            x=0.25, y=0.42,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=11, color="gray"),
            bgcolor="rgba(255,255,255,0.8)"
        )
        
        fig.add_annotation(
            text="⚖️ Steady Line = Good Balance",
            x=0.75, y=0.42,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=11, color="gray"),
            bgcolor="rgba(255,255,255,0.8)"
        )
        
        fig.add_annotation(
            text="🕐 Red Hours = High Risk Times",
            x=0.25, y=0.19,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=11, color="gray"),
            bgcolor="rgba(255,255,255,0.8)"
        )
        
        fig.add_annotation(
            text="🏆 Taller Bars = Better Consistency",
            x=0.75, y=0.19,
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=11, color="gray"),
            bgcolor="rgba(255,255,255,0.8)"
        )
        
        # Save and show
        fig.write_html("advanced_gaming_health_insights.html")
        fig.show()
        
        return fig
    
    def generate_comprehensive_health_report(self):
        # --- User-friendly, actionable report ---
        good_pct = self.data['good_posture'].mean() * 100
        avg_risk = self.data['Posture_Risk_Score'].mean()
        worst_game = self.data.groupby('game')['Posture_Risk_Score'].mean().idxmax()
        best_game = self.data.groupby('game')['Posture_Risk_Score'].mean().idxmin()
        best_streak = max([sum(1 for _ in g) for k, g in groupby(self.data['good_posture']) if k == 1])
        hour_worst = self.data.groupby('Hour')['Posture_Risk_Score'].mean().idxmax()
        hour_best = self.data.groupby('Hour')['Posture_Risk_Score'].mean().idxmin()
        
        print("\n" + "="*60)
        print("🎮 GAMING HEALTH REPORT 🎮")
        print("="*60)
        
        print(f"\n📊 OVERVIEW:")
        print(f"   Good posture rate: {good_pct:.1f}% {'🎉 Great!' if good_pct > 80 else '⚠️ Needs improvement'}")
        print(f"   Average risk score: {avg_risk:.2f}/5")
        
        print(f"\n🎮 GAME ANALYSIS:")
        print(f"   Highest risk: {worst_game} ⚠️")
        print(f"   Best posture: {best_game} ✅")
        
        print(f"\n🏆 ACHIEVEMENTS:")
        print(f"   Best streak: {best_streak} sessions")
        
        print(f"\n⏰ TIME PATTERNS:")
        print(f"   Worst hour: {hour_worst}:00")
        print(f"   Best hour: {hour_best}:00")
        
        print(f"\n💡 TIPS:")
        if good_pct < 80:
            print("   • Set hourly posture reminders")
        if avg_risk > 2:
            print("   • Take more breaks between games")
        print("   • Adjust monitor to eye level")
        print("   • Keep feet flat on floor")
        print("   • Shoulders back and relaxed")
        
        print(f"\n📄 Dashboard saved: advanced_gaming_health_insights.html")
        print("="*60 + "\n")

def main():
    visualizer = HealthInsightsVisualizer()
    if visualizer.load_and_prepare_data():
        visualizer.create_comprehensive_health_dashboard()
        visualizer.generate_comprehensive_health_report()
    else:
        print("Failed to process health data.")

if __name__ == "__main__":
    main()