import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import scipy.stats as stats

class HealthInsightsVisualizer:
    def __init__(self, filepath):
        """Initialize the visualizer with comprehensive health tracking"""
        self.filepath = filepath
        self.data = None
        
    def load_and_prepare_data(self):
        """Load and comprehensively prepare health tracking data"""
        try:
            # Load data with enhanced parsing
            self.data = pd.read_csv(self.filepath, parse_dates=['Timestamp'])
            
            # Remove duplicate timestamps
            self.data.drop_duplicates(subset=['Timestamp'], keep='first', inplace=True)
            
            # Create derived features for deeper insights
            self._engineer_health_features()
            
            return True
        except Exception as e:
            print(f"Data preparation error: {e}")
            return False
    
    def _engineer_health_features(self):
        """Create advanced derived features for health insights"""
        # Time-based features
        self.data['Hour'] = self.data['Timestamp'].dt.hour
        self.data['Day'] = self.data['Timestamp'].dt.day_name()
        self.data['Date'] = self.data['Timestamp'].dt.date
        
        # Game categorization
        self.data['Game'] = self.data['Game'].fillna('Unspecified')
        
        # Posture risk scoring
        def calculate_posture_risk(row):
            risk = 0
            if row['Posture Status'] == 'Slouching':
                risk += 3
            elif row['Posture Status'] == 'Forward Head Posture':
                risk += 2
            
            # Additional risk factors
            if row['Forward Lean'] > 0.1:  # Significant forward lean
                risk += 1
            if row['Back Angle'] < 170:  # Bad back angle
                risk += 1
            
            return risk
        
        self.data['Posture_Risk_Score'] = self.data.apply(calculate_posture_risk, axis=1)
        
        # Cumulative metrics
        self.data.sort_values('Timestamp', inplace=True)
        
        # Strain accumulation
        self.data['Cumulative_Forward_Lean'] = self.data['Forward Lean'].cumsum()
        self.data['Cumulative_Posture_Risk'] = self.data['Posture_Risk_Score'].cumsum()
        
        # Game session tracking
        self.data['Game_Session'] = (self.data['Game'] != self.data['Game'].shift()).cumsum()

    def create_comprehensive_health_dashboard(self):
        """Create an advanced multi-dimensional health insights dashboard"""
        # Create 12 subplots for maximum insights
        fig = make_subplots(
            rows=4, cols=3, 
            specs=[
                [{'type': 'domain'}, {'type': 'xy'}, {'type': 'xy'}],
                [{'type': 'box'}, {'type': 'heatmap'}, {'type': 'box'}],
                [{'type': 'xy'}, {'type': 'xy'}, {'type': 'box'}],
                [{'type': 'scatter'}, {'type': 'box'}, {'type': 'box'}]
            ],
            subplot_titles=(
                "Posture Distribution", 
                "Posture Risk Over Time", 
                "Forward Lean Trend",
                "Forward Lean by Game", 
                "Posture Distribution Heatmap", 
                "Back Angle Variation",
                "Water Intake Pattern", 
                "Break Frequency", 
                "Shoulder Alignment",
                "Cumulative Physical Strain", 
                "Posture Risk Score Distribution",
                "Game-wise Posture Risk"
            )
        )

        # Color palette
        color_palette = px.colors.qualitative.Pastel

        # 1. Posture Distribution (Pie Chart)
        posture_counts = self.data['Posture Status'].value_counts()
        fig.add_trace(
            go.Pie(
                labels=posture_counts.index, 
                values=posture_counts.values,
                hole=0.3,
                marker=dict(colors=color_palette[:len(posture_counts)])
            ),
            row=1, col=1
        )

        # 2. Posture Risk Over Time (Line Chart)
        fig.add_trace(
            go.Scatter(
                x=self.data['Timestamp'], 
                y=self.data['Posture_Risk_Score'],
                mode='lines',
                line=dict(color='red', width=2),
                name='Posture Risk'
            ),
            row=1, col=2
        )

        # 3. Forward Lean Trend (Line Chart)
        fig.add_trace(
            go.Scatter(
                x=self.data['Timestamp'], 
                y=self.data['Forward Lean'],
                mode='lines',
                line=dict(color='blue', width=2),
                name='Forward Lean'
            ),
            row=1, col=3
        )

        # 4. Forward Lean by Game (Box Plot)
        game_forward_lean = []
        unique_games = self.data['Game'].unique()
        for i, game in enumerate(unique_games):
            game_data = self.data[self.data['Game'] == game]['Forward Lean']
            game_forward_lean.append(
                go.Box(
                    y=game_data,
                    name=game,
                    marker_color=color_palette[i % len(color_palette)]
                )
            )
        
        for box in game_forward_lean:
            fig.add_trace(box, row=2, col=1)

        # 5. Posture Distribution by Game (Heatmap)
        posture_game_counts = pd.crosstab(
            self.data['Game'], 
            self.data['Posture Status'], 
            normalize='index'
        ) * 100
        
        fig.add_trace(
            go.Heatmap(
                z=posture_game_counts.values,
                x=posture_game_counts.columns,
                y=posture_game_counts.index,
                colorscale='YlGnBu'
            ),
            row=2, col=2
        )

        # 6. Back Angle Variation (Box Plot)
        fig.add_trace(
            go.Box(
                y=self.data['Back Angle'],
                name='Back Angle',
                marker_color=color_palette[5]
            ),
            row=2, col=3
        )

        # 7. Water Intake Pattern (Bar Chart)
        water_intake_pattern = self.data.groupby('Hour')['Water Intake'].sum()
        fig.add_trace(
            go.Bar(
                x=water_intake_pattern.index,
                y=water_intake_pattern.values,
                marker_color=color_palette[3],
                name='Water Intake'
            ),
            row=3, col=1
        )

        # 8. Break Frequency Analysis (Bar Chart)
        break_frequency = self.data.groupby('Hour')['Break Taken'].sum()
        fig.add_trace(
            go.Bar(
                x=break_frequency.index,
                y=break_frequency.values,
                marker_color=color_palette[4],
                name='Breaks Taken'
            ),
            row=3, col=2
        )

        # 9. Shoulder Alignment (Box Plot)
        fig.add_trace(
            go.Box(
                y=self.data['Shoulder Alignment'],
                name='Shoulder Alignment',
                marker_color=color_palette[6]
            ),
            row=3, col=3
        )

        # 10. Cumulative Physical Strain (Line Chart)
        fig.add_trace(
            go.Scatter(
                x=self.data['Timestamp'], 
                y=self.data['Cumulative_Forward_Lean'],
                mode='lines',
                line=dict(color='green', width=2),
                name='Cumulative Forward Lean'
            ),
            row=4, col=1
        )

        # 11. Posture Risk Score Distribution (Box Plot)
        fig.add_trace(
            go.Box(
                y=self.data['Posture_Risk_Score'],
                name='Posture Risk Score',
                marker_color=color_palette[7]
            ),
            row=4, col=2
        )

        # 12. Game-wise Posture Risk (Box Plot)
        game_posture_risk = []
        for i, game in enumerate(unique_games):
            game_data = self.data[self.data['Game'] == game]['Posture_Risk_Score']
            game_posture_risk.append(
                go.Box(
                    y=game_data,
                    name=game,
                    marker_color=color_palette[i % len(color_palette)]
                )
            )
        
        for box in game_posture_risk:
            fig.add_trace(box, row=4, col=3)

        # Update layout for professional appearance
        fig.update_layout(
            height=2000, 
            width=2000,
            title_text="Advanced Gaming Health Insights",
            showlegend=False,
            template='plotly_white'
        )

        # Adjust axis labels and titles
        axis_configs = [
            (1, 2, "Time", "Posture Risk Score"),
            (1, 3, "Time", "Forward Lean"),
            (3, 1, "Hour", "Water Intake"),
            (3, 2, "Hour", "Breaks Taken"),
            (4, 1, "Time", "Cumulative Forward Lean")
        ]
        
        for row, col, x_title, y_title in axis_configs:
            fig.update_xaxes(title_text=x_title, row=row, col=col)
            fig.update_yaxes(title_text=y_title, row=row, col=col)

        # Save and show the dashboard
        fig.write_html("advanced_gaming_health_insights.html")
        fig.show()
    
    def generate_comprehensive_health_report(self):
        """Generate an in-depth health analysis report"""
        # Statistical Analysis
        statistical_insights = {
            "Posture Analysis": {
                "Posture Distribution": self.data['Posture Status'].value_counts(normalize=True).to_dict(),
                "Average Posture Risk Score": self.data['Posture_Risk_Score'].mean(),
                "Max Posture Risk Score": self.data['Posture_Risk_Score'].max(),
                "Posture Risk Score Std Dev": self.data['Posture_Risk_Score'].std()
            },
            "Biomechanical Metrics": {
                "Forward Lean": {
                    "Mean": self.data['Forward Lean'].mean(),
                    "Median": self.data['Forward Lean'].median(),
                    "Max": self.data['Forward Lean'].max(),
                    "Min": self.data['Forward Lean'].min()
                },
                "Back Angle": {
                    "Mean": self.data['Back Angle'].mean(),
                    "Median": self.data['Back Angle'].median(),
                    "Optimal Angle %": (self.data['Back Angle'] > 170).mean() * 100
                }
            },
            "Behavioral Patterns": {
                "Water Intake": {
                    "Total Water Intake Events": self.data['Water Intake'].sum(),
                    "Water Intake Frequency": self.data['Water Intake'].mean()
                },
                "Breaks": {
                    "Total Breaks": self.data['Break Taken'].sum(),
                    "Break Frequency": self.data['Break Taken'].mean()
                }
            },
            "Game-wise Insights": {
                game: {
                    "Total Sessions": len(self.data[self.data['Game'] == game]),
                    "Average Posture Risk": self.data[self.data['Game'] == game]['Posture_Risk_Score'].mean(),
                    "Dominant Posture": self.data[self.data['Game'] == game]['Posture Status'].mode().iloc[0]
                } for game in self.data['Game'].unique()
            },
            "Correlation Analysis": {
                "Forward Lean vs Back Angle": stats.pearsonr(self.data['Forward Lean'], self.data['Back Angle'])[0],
                "Posture Risk vs Shoulder Alignment": stats.pearsonr(self.data['Posture_Risk_Score'], self.data['Shoulder Alignment'])[0]
            }
        }
        
        # Print and return the report
        import json
        print(json.dumps(statistical_insights, indent=2))
        return statistical_insights

def main():
    visualizer = HealthInsightsVisualizer('Improvised-Project\detailed_health_logs.csv')
    
    if visualizer.load_and_prepare_data():
        # Create advanced interactive dashboard
        visualizer.create_comprehensive_health_dashboard()
        
        # Generate comprehensive health report
        visualizer.generate_comprehensive_health_report()
    else:
        print("Failed to process health data.")

if __name__ == "__main__":
    main()