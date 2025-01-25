import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from ml_model import FatigueLevelPredictor  # Import the FatigueLevelPredictor class

class HealthDataAnalyzer:
    def __init__(self, filepath):
        """Initialize the analyzer with the CSV file path"""
        self.filepath = filepath
        self.data = None
        
    def load_data(self):
        """Load and preprocess the CSV data"""
        try:
            # Explicitly specify data types to avoid string conversion issues
            self.data = pd.read_csv(self.filepath, parse_dates=['Timestamp'], 
                                    dtype={
                                        'Action': str, 
                                        'Posture Status': str
                                    })
            self._clean_data()
        except Exception as e:
            print(f"Error loading data: {e}")
            
    def _clean_data(self):
        """Internal method to clean and preprocess data"""
        # Remove duplicates
        self.data = self.data.drop_duplicates()
        
        # Fill missing values safely
        numeric_columns = ['Back Angle', 'Forward Lean', 'Shoulder Alignment']
        for col in numeric_columns:
            if col in self.data.columns:
                self.data[col] = self.data[col].fillna(self.data[col].median())
        
        # Standardize categorical columns
        categorical_columns = ['Posture Status']
        for col in categorical_columns:
            if col in self.data.columns:
                self.data[col] = self.data[col].str.strip().str.title()
        
        # Extract additional time-based features
        if 'Timestamp' in self.data.columns:
            self.data['Hour'] = self.data['Timestamp'].dt.hour
            self.data['Day'] = self.data['Timestamp'].dt.day_name()
        
    def posture_analysis(self):
        """Comprehensive posture status analysis"""
        if 'Posture Status' not in self.data.columns:
            print("No 'Posture Status' column found")
            return {}

        posture_stats = {
            'counts': self.data['Posture Status'].value_counts(),
            'percentages': self.data['Posture Status'].value_counts(normalize=True) * 100,
        }
        return posture_stats
    
    def visualize_posture_distribution(self, ax1, ax2):
        """Create visualizations for posture distribution"""
        # Prepare color and order
        colors = ['lightgreen', 'red', 'grey']
        category_order = ["Good Posture", "Slouching", "Forward Head Posture"]
        
        # Ensure all categories exist in data
        existing_categories = [cat for cat in category_order if cat in self.data['Posture Status'].unique()]
        
        # Bar Plot
        palette = sns.color_palette(colors[:len(existing_categories)])
        
        sns.countplot(data=self.data, x="Posture Status", 
                      order=existing_categories, 
                      palette=palette, ax=ax1)
        ax1.set_title("Posture Distribution", fontsize=16, fontweight="bold")
        ax1.set_xlabel("Posture Status", fontsize=12)
        ax1.set_ylabel("Frequency", fontsize=12)
        ax1.set_xticklabels(ax1.get_xticklabels(), rotation=45)
        
        # Pie Chart
        posture_counts = self.data['Posture Status'].value_counts()
        ax2.pie(posture_counts, labels=posture_counts.index, 
                autopct="%1.1f%%", startangle=140, colors=palette)
        ax2.set_title("Posture Percentage", fontsize=16, fontweight="bold")
    
    def visualize_forward_lean(self, ax):
        """Create a line plot for forward lean over time"""
        sns.lineplot(data=self.data, x='Timestamp', y='Forward Lean', hue='Posture Status', palette='coolwarm', ax=ax)
        ax.set_title("Forward Lean Over Time", fontsize=16, fontweight="bold")
        ax.set_xlabel("Timestamp", fontsize=12)
        ax.set_ylabel("Forward Lean (cm)", fontsize=12)
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
        ax.legend(title='Posture Status')
    
    def visualize_anomalies(self, ax):
        """Visualize anomalies detected by the Isolation Forest model"""
        predictor = FatigueLevelPredictor(self.filepath)
        predictor.load_data()
        predictor.detect_anomalies()

        normal = predictor.data[predictor.data['Anomaly'] == 1]
        abnormal = predictor.data[predictor.data['Anomaly'] == -1]

        if not normal.empty and not abnormal.empty:
            ax.scatter(normal['Back Angle'], normal['Shoulder Alignment'], color='g', label='Normal', alpha=0.6)
            ax.scatter(abnormal['Back Angle'], abnormal['Shoulder Alignment'], color='r', label='Anomaly', alpha=0.6)
            ax.set_title('Posture Data Anomalies Detection', fontsize=16, fontweight='bold')
            ax.set_xlabel('Back Angle (°)', fontsize=12)
            ax.set_ylabel('Shoulder Alignment (cm)', fontsize=12)
            ax.legend()
        else:
            ax.text(0.5, 0.5, 'No data available for anomaly detection', horizontalalignment='center', verticalalignment='center', transform=ax.transAxes)
            ax.set_title('Posture Data Anomalies Detection', fontsize=16, fontweight='bold')
            ax.set_xlabel('Back Angle (°)', fontsize=12)
            ax.set_ylabel('Shoulder Alignment (cm)', fontsize=12)

    def visualize_water_frequency(self):
        """Visualize water intake frequency"""
        plt.figure(figsize=(10, 6))
        sns.countplot(data=self.data, x='Hour', hue='Water Intake', palette='Blues')
        plt.title('Water Intake Frequency by Hour', fontsize=16, fontweight='bold')
        plt.xlabel('Hour of the Day', fontsize=12)
        plt.ylabel('Frequency', fontsize=12)
        plt.legend(title='Water Intake')
        plt.show()

    def visualize_water_breaks_by_hour(self):
        """Visualize water breaks by hour"""
        plt.figure(figsize=(10, 6))
        sns.lineplot(data=self.data, x='Hour', y='Water Intake', estimator='sum', ci=None, marker='o', color='b')
        plt.title('Water Breaks by Hour', fontsize=16, fontweight='bold')
        plt.xlabel('Hour of the Day', fontsize=12)
        plt.ylabel('Total Water Breaks', fontsize=12)
        plt.show()

    def visualize_posture_metrics(self):
        """Visualize posture metrics line plot horizontally"""
        fig, axs = plt.subplots(1, 3, figsize=(18, 6))
        
        sns.lineplot(data=self.data, x='Timestamp', y='Back Angle', ax=axs[0], color='r')
        axs[0].set_title('Back Angle Over Time', fontsize=16, fontweight='bold')
        axs[0].set_xlabel('Timestamp', fontsize=12)
        axs[0].set_ylabel('Back Angle (°)', fontsize=12)
        axs[0].set_xticklabels(axs[0].get_xticklabels(), rotation=45)
        
        sns.lineplot(data=self.data, x='Timestamp', y='Forward Lean', ax=axs[1], color='g')
        axs[1].set_title('Forward Lean Over Time', fontsize=16, fontweight='bold')
        axs[1].set_xlabel('Timestamp', fontsize=12)
        axs[1].set_ylabel('Forward Lean (cm)', fontsize=12)
        axs[1].set_xticklabels(axs[1].get_xticklabels(), rotation=45)
        
        sns.lineplot(data=self.data, x='Timestamp', y='Shoulder Alignment', ax=axs[2], color='b')
        axs[2].set_title('Shoulder Alignment Over Time', fontsize=16, fontweight='bold')
        axs[2].set_xlabel('Timestamp', fontsize=12)
        axs[2].set_ylabel('Shoulder Alignment (cm)', fontsize=12)
        axs[2].set_xticklabels(axs[2].get_xticklabels(), rotation=45)
        
        plt.tight_layout()
        plt.show()

    def generate_comprehensive_report(self):
        """Generate a comprehensive health tracking report"""
        report = {
            'Posture Analysis': self.posture_analysis(),
        }
        return report

    def visualize_all(self):
        """Visualize all charts in a single page"""
        fig, axs = plt.subplots(2, 2, figsize=(24, 15))
        
        self.visualize_posture_distribution(axs[0, 0], axs[0, 1])
        self.visualize_forward_lean(axs[1, 0])
        self.visualize_anomalies(axs[1, 1])
        
        plt.subplots_adjust(hspace=0.4, wspace=0.4)
        plt.show()

    def visualize_all_separately(self):
        """Visualize all charts separately"""
        self.visualize_all()
        plt.close()
        self.visualize_water_frequency()
        plt.close()
        self.visualize_water_breaks_by_hour()
        plt.close()
        self.visualize_posture_metrics()
        plt.close()

    def predict_fatigue_levels(self):
        """Predict fatigue levels using the ML model"""
        predictor = FatigueLevelPredictor(self.filepath)
        predictor.load_data()
        predictor.train_model()

def main():
    analyzer = HealthDataAnalyzer('detailed_health_logs.csv')
    analyzer.load_data()
    
    # Visualize all charts separately
    analyzer.visualize_all_separately()
    
    # Generate report
    report = analyzer.generate_comprehensive_report()
    print(report)
    
    # Predict fatigue levels
    analyzer.predict_fatigue_levels()

if __name__ == "__main__":
    main()