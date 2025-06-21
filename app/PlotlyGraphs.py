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
                [{'type': 'box'}, {'type': 'heatmap'}, {'type': 'xy'}],
                [{'type': 'xy'}, {'type': 'xy'}, {'type': 'xy'}],
                [{'type': 'xy'}, {'type': 'xy'}, {'type': 'xy'}]
            ],
            subplot_titles=(
                "Posture Distribution", 
                "Game Performance Intensity", 
                "Posture Status Correlation",
                "Forward Lean Over Time", 
                "Detailed Posture Analysis", 
                "Back Angle Over Time",
                "Shoulder Angle Over Time", 
                "Hourly Gaming Intensity", 
                "Recommended Breaks Duration"
            )
        )

        # Color palette
        color_palette = px.colors.qualitative.Pastel
        water_blue = 'rgba(0, 119, 182, 0.8)'  # Water blue color

        # 1. Posture Distribution (Pie Chart)
        posture_counts = self.data['Posture Status'].value_counts()
        fig.add_trace(
            go.Pie(
                labels=posture_counts.index, 
                values=posture_counts.values,
                hole=0.3,
                marker=dict(colors=px.colors.qualitative.Set3)
            ),
            row=1, col=1
        )

        # 2. Game Performance Intensity (Heatmap)
        # Preprocess data for more informative heatmap
        game_posture_intensity = pd.crosstab(
            self.data['Game'], 
            self.data['Posture Status'], 
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

        # 3. Posture Status Correlation (Scatter)
        # Show relationship between Forward Lean and Posture Risk
        fig.add_trace(
            go.Scatter(
                x=self.data['Forward Lean'], 
                y=self.data['Posture_Risk_Score'],
                mode='markers',
                marker=dict(
                    color=self.data['Posture_Risk_Score'], 
                    colorscale='Viridis',
                    showscale=True
                ),
                name='Posture Risk Correlation'
            ),
            row=1, col=3
        )

        # 4. Forward Lean Over Time (Line Chart)
        # Use rolling mean to smooth out fluctuations
        forward_lean_rolling = self.data['Forward Lean'].rolling(window=10).mean()
        fig.add_trace(
            go.Scatter(
                x=self.data['Timestamp'], 
                y=forward_lean_rolling,
                mode='lines',
                line=dict(color='blue', width=2),
                name='Forward Lean (Rolling Mean)'
            ),
            row=2, col=1
        )

        # 5. Detailed Posture Analysis (Box Plot for Games)
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
            fig.add_trace(box, row=2, col=2)

        # 6. Back Angle Over Time (Line Chart)
        back_angle_rolling = self.data['Back Angle'].rolling(window=10).mean()
        fig.add_trace(
            go.Scatter(
                x=self.data['Timestamp'], 
                y=back_angle_rolling,
                mode='lines',
                line=dict(color='green', width=2),
                name='Back Angle (Rolling Mean)'
            ),
            row=2, col=3
        )

        # 7. Shoulder Angle Over Time (Line Chart)
        shoulder_angle_rolling = self.data['Shoulder Alignment'].rolling(window=10).mean()
        fig.add_trace(
            go.Scatter(
                x=self.data['Timestamp'], 
                y=shoulder_angle_rolling,
                mode='lines',
                line=dict(color='purple', width=2),
                name='Shoulder Angle (Rolling Mean)'
            ),
            row=3, col=1
        )

        # 8. Hourly Gaming Intensity (Heatmap)
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
            row=3, col=2
        )

        # 9. Recommended Breaks Duration (Bar Chart)
        fig.add_trace(
            go.Bar(
                x=['Short Break', 'Stretch', 'Eye Rest', 'Posture Correction'],
                y=[15, 10, 20, 5],
                marker_color=color_palette[:4],
                text=[15, 10, 20, 5],
                textposition='auto'
            ),
            row=3, col=3
        )

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
            (1, 3, "Forward Lean", "Posture Risk Score"),
            (2, 1, "Time", "Forward Lean"),
            (2, 3, "Time", "Back Angle"),
            (3, 1, "Time", "Shoulder Angle"),
            (3, 2, "Hour", "Day")
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
            "Game-wise Insights": {
                game: {
                    "Total Sessions": len(self.data[self.data['Game'] == game]),
                    "Average Posture Risk": self.data[self.data['Game'] == game]['Posture_Risk_Score'].mean(),
                    "Dominant Posture": self.data[self.data['Game'] == game]['Posture Status'].mode().iloc[0]
                } for game in self.data['Game'].unique()
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