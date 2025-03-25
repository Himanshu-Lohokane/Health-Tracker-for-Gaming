import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import scipy.stats as stats
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import classification_report, accuracy_score
import matplotlib.pyplot as plt

class HealthInsightsVisualizer:
    def __init__(self, filepath):
        """Initialize the visualizer with comprehensive health tracking"""
        self.filepath = filepath
        self.data = None
        self.fatigue_model = None
        self.anomaly_detector = None
    
    def load_and_prepare_data(self):
        """Load and comprehensively prepare health tracking data"""
        try:
            # Load data with enhanced parsing
            self.data = pd.read_csv(self.filepath, parse_dates=['Timestamp'])
            
            # Remove duplicate timestamps
            self.data.drop_duplicates(subset=['Timestamp'], keep='first', inplace=True)
            
            # Create derived features for deeper insights
            self._engineer_health_features()
            
            # Train ML models
            self._train_fatigue_model()
            self._detect_anomalies()
            
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
        
        # Fatigue Level Calculation
        self.data['Fatigue_Level'] = self.data.apply(self._get_fatigue_label, axis=1)
        
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

    def _get_fatigue_label(self, row):
        """Comprehensive fatigue level mapping"""
        if row['Back Angle'] < 170 and row['Shoulder Alignment'] > 0.05:
            return 3  # High fatigue (likely slouching)
        elif row['Forward Lean'] > 0.1:
            return 2  # Medium fatigue (leaning forward)
        else:
            return 1  # Low fatigue (good posture)

    def _train_fatigue_model(self):
        """Train a Random Forest Classifier for Fatigue Prediction"""
        # Features: Back Angle, Shoulder Alignment, Forward Lean
        X = self.data[['Back Angle', 'Shoulder Alignment', 'Forward Lean']]
        y = self.data['Fatigue_Level']

        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train a Random Forest Classifier
        self.fatigue_model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.fatigue_model.fit(X_train, y_train)

        # Predictions and evaluation
        y_pred = self.fatigue_model.predict(X_test)
        print("Fatigue Prediction Accuracy: ", accuracy_score(y_test, y_pred))
        print("\nFatigue Classification Report:\n", classification_report(y_test, y_pred))

    def _detect_anomalies(self):
        """Detect anomalies in posture data using Isolation Forest"""
        X = self.data[['Back Angle', 'Shoulder Alignment', 'Forward Lean']]

        # Train an Isolation Forest model to detect abnormal postures
        self.anomaly_detector = IsolationForest(contamination=0.05, random_state=42)
        self.anomaly_detector.fit(X)

        # Predict anomalies (1 = normal, -1 = anomaly)
        self.data['Anomaly'] = self.anomaly_detector.predict(X)

    def create_comprehensive_health_dashboard(self):
        """Create an advanced multi-dimensional health insights dashboard"""
        # Create 12 subplots for maximum insights
        fig = make_subplots(
            rows=4, cols=3, 
            specs=[
                [{'type': 'domain'}, {'type': 'xy'}, {'type': 'scatter'}],
                [{'type': 'box'}, {'type': 'heatmap'}, {'type': 'xy'}],
                [{'type': 'xy'}, {'type': 'xy'}, {'type': 'xy'}],
                [{'type': 'xy'}, {'type': 'box'}, {'type': 'scatter'}]
            ],
            subplot_titles=(
                "Posture Distribution", 
                "Game Performance Intensity", 
                "Anomaly Detection",
                "Forward Lean by Game", 
                "Hourly Fatigue Intensity", 
                "Fatigue Level Prediction",
                "Cumulative Physical Strain", 
                "Fatigue Score Distribution", 
                "Feature Importance",
                "Recommended Breaks", 
                "Fatigue Level Analysis", 
                "Posture Risk vs Fatigue"
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
                marker=dict(colors=px.colors.qualitative.Set3)
            ),
            row=1, col=1
        )

        # 2. Game Performance Intensity (Heatmap)
        game_fatigue_intensity = pd.crosstab(
            self.data['Game'], 
            self.data['Fatigue_Level'], 
            values=self.data['Posture_Risk_Score'], 
            aggfunc='mean'
        )
        
        fig.add_trace(
            go.Heatmap(
                z=game_fatigue_intensity.values,
                x=game_fatigue_intensity.columns,
                y=game_fatigue_intensity.index,
                colorscale='Viridis'
            ),
            row=1, col=2
        )

        # 3. Anomaly Detection (Scatter)
        normal = self.data[self.data['Anomaly'] == 1]
        abnormal = self.data[self.data['Anomaly'] == -1]
        
        fig.add_trace(
            go.Scatter(
                x=normal['Back Angle'], 
                y=normal['Shoulder Alignment'],
                mode='markers',
                name='Normal Postures',
                marker=dict(color='green', size=8)
            ),
            row=1, col=3
        )
        
        fig.add_trace(
            go.Scatter(
                x=abnormal['Back Angle'], 
                y=abnormal['Shoulder Alignment'],
                mode='markers',
                name='Anomalous Postures',
                marker=dict(color='red', size=8)
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

        # 5. Hourly Fatigue Intensity (Heatmap)
        hourly_fatigue = self.data.pivot_table(
            index='Day', 
            columns='Hour', 
            values='Fatigue_Level', 
            aggfunc='mean'
        )
        
        fig.add_trace(
            go.Heatmap(
                z=hourly_fatigue.values,
                x=hourly_fatigue.columns,
                y=hourly_fatigue.index,
                colorscale='YlOrRd'
            ),
            row=2, col=2
        )

        # 6. Fatigue Level Prediction (Scatter)
        # Visualize predicted vs actual fatigue levels
        fig.add_trace(
            go.Scatter(
                x=self.data['Fatigue_Level'], 
                y=self.fatigue_model.predict(self.data[['Back Angle', 'Shoulder Alignment', 'Forward Lean']]),
                mode='markers',
                marker=dict(color='purple', size=8)
            ),
            row=2, col=3
        )

        # 7. Cumulative Physical Strain (Line Chart)
        strain_rolling = self.data['Cumulative_Forward_Lean'].rolling(window=10).mean()
        fig.add_trace(
            go.Scatter(
                x=self.data['Timestamp'], 
                y=strain_rolling,
                mode='lines',
                line=dict(color='blue', width=2),
                name='Cumulative Strain (Rolling Mean)'
            ),
            row=3, col=1
        )

        # 8. Fatigue Score Distribution (Box Plot)
        fig.add_trace(
            go.Box(
                y=self.data['Fatigue_Level'],
                name='Fatigue Levels',
                marker_color=color_palette[5]
            ),
            row=3, col=2
        )

        # 9. Feature Importance (Bar Chart)
        if hasattr(self.fatigue_model, 'feature_importances_'):
            feature_names = ['Back Angle', 'Shoulder Alignment', 'Forward Lean']
            feature_importances = self.fatigue_model.feature_importances_
            
            fig.add_trace(
                go.Bar(
                    x=feature_names,
                    y=feature_importances,
                    marker_color=color_palette[:3],
                    name='Feature Importance'
                ),
                row=3, col=3
            )

        # 10. Recommended Breaks (Bar Chart)
        fig.add_trace(
            go.Bar(
                x=['Short Break', 'Stretch', 'Eye Rest', 'Posture Correction'],
                y=[15, 10, 20, 5],
                marker_color=color_palette[:4],
                text=[15, 10, 20, 5],
                textposition='auto'
            ),
            row=4, col=1
        )

        # 11. Fatigue Level Analysis (Box Plot)
        game_fatigue = []
        for i, game in enumerate(unique_games):
            game_data = self.data[self.data['Game'] == game]['Fatigue_Level']
            game_fatigue.append(
                go.Box(
                    y=game_data,
                    name=game,
                    marker_color=color_palette[i % len(color_palette)]
                )
            )
        
        for box in game_fatigue:
            fig.add_trace(box, row=4, col=2)

        # 12. Posture Risk vs Fatigue (Scatter)
        fig.add_trace(
            go.Scatter(
                x=self.data['Posture_Risk_Score'], 
                y=self.data['Fatigue_Level'],
                mode='markers',
                marker=dict(
                    color=self.data['Fatigue_Level'], 
                    colorscale='Viridis',
                    showscale=True
                ),
                name='Posture Risk vs Fatigue'
            ),
            row=4, col=3
        )

        # Update layout for professional appearance
        fig.update_layout(
            height=2400, 
            width=2400,
            title_text="Advanced Gaming Health Insights with ML Analysis",
            showlegend=False,
            template='plotly_white'
        )

        # Save and show the dashboard
        fig.write_html("advanced_gaming_health_insights_ml.html")
        fig.show()

    def generate_comprehensive_health_report(self):
        """Generate an in-depth health analysis report with ML insights"""
        ml_insights = {
            "Fatigue Prediction": {
                "Model Accuracy": accuracy_score(
                    self.data['Fatigue_Level'], 
                    self.fatigue_model.predict(self.data[['Back Angle', 'Shoulder Alignment', 'Forward Lean']])
                ),
                "Feature Importances": dict(zip(
                    ['Back Angle', 'Shoulder Alignment', 'Forward Lean'],
                    self.fatigue_model.feature_importances_
                ))
            },
            "Anomaly Detection": {
                "Total Anomalies": len(self.data[self.data['Anomaly'] == -1]),
                "Anomaly Percentage": (self.data['Anomaly'] == -1).mean() * 100
            },
            "Fatigue Level Insights": {
                level: {
                    "Count": len(self.data[self.data['Fatigue_Level'] == level]),
                    "Percentage": (self.data['Fatigue_Level'] == level).mean() * 100,
                    "Avg Posture Risk": self.data[self.data['Fatigue_Level'] == level]['Posture_Risk_Score'].mean()
                } for level in [1, 2, 3]
            }
        }
        
        # Print and return the report
        import json
        print(json.dumps(ml_insights, indent=2))
        return ml_insights

def main():
    visualizer = HealthInsightsVisualizer('Improvised-Project\detailed_health_logs.csv')
    
    if visualizer.load_and_prepare_data():
        # Create advanced interactive dashboard with ML insights
        visualizer.create_comprehensive_health_dashboard()
        
        # Generate comprehensive health report with ML insights
        visualizer.generate_comprehensive_health_report()
    else:
        print("Failed to process health data.")

if __name__ == "__main__":
    main()