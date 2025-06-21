import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.metrics import classification_report, accuracy_score
import matplotlib.pyplot as plt

class FatigueLevelPredictor:
    def __init__(self, filepath):
        self.filepath = filepath
        self.data = None
        self.model = None

    def load_data(self):
        """Load and preprocess the CSV data"""
        try:
            self.data = pd.read_csv(self.filepath, parse_dates=['Timestamp'])
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

        # Create the label 'Fatigue Level' column based on user input
        self.data['Fatigue Level'] = self.data.apply(self.get_fatigue_label, axis=1)

    def get_fatigue_label(self, row):
        """Example mapping of fatigue levels (you can modify this as per your data)"""
        if row['Back Angle'] < 170 and row['Shoulder Alignment'] > 0.05:
            return 3  # High fatigue (likely slouching)
        elif row['Forward Lean'] > 0.1:
            return 2  # Medium fatigue (leaning forward)
        else:
            return 1  # Low fatigue (good posture)

    def train_model(self):
        """Train a Random Forest Classifier"""
        # Features: Back Angle, Shoulder Alignment, Forward Lean
        X = self.data[['Back Angle', 'Shoulder Alignment', 'Forward Lean']]
        y = self.data['Fatigue Level']

        # Train-test split
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Train a Random Forest Classifier
        self.model = RandomForestClassifier(n_estimators=100, random_state=42)
        self.model.fit(X_train, y_train)

        # Predictions
        y_pred = self.model.predict(X_test)

        # Evaluate the model
        print("Accuracy: ", accuracy_score(y_test, y_pred))
        print("\nClassification Report:\n", classification_report(y_test, y_pred))

        # Visualize the actual vs predicted fatigue levels
        plt.figure(figsize=(8, 6))
        plt.scatter(X_test['Back Angle'], X_test['Shoulder Alignment'], c=y_pred, cmap='coolwarm', s=100, edgecolors='k')
        plt.title('Actual vs Predicted Fatigue Level')
        plt.xlabel('Back Angle (°)')
        plt.ylabel('Shoulder Alignment (cm)')
        plt.colorbar(label='Predicted Fatigue Level')
        plt.show()

    def detect_anomalies(self):
        """Detect anomalies in posture data using Isolation Forest"""
        X = self.data[['Back Angle', 'Shoulder Alignment', 'Forward Lean']]

        # Train an Isolation Forest model to detect abnormal postures
        model = IsolationForest(contamination=0.05, random_state=42)  # 5% contamination assumed
        model.fit(X)

        # Predict anomalies (1 = normal, -1 = anomaly)
        self.data['Anomaly'] = model.predict(X)

        # Visualize the anomalies
        normal = self.data[self.data['Anomaly'] == 1]
        abnormal = self.data[self.data['Anomaly'] == -1]

        plt.figure(figsize=(10, 6))

        # Plot normal data
        plt.scatter(normal['Back Angle'], normal['Shoulder Alignment'], color='g', label='Normal', alpha=0.6)

        # Plot abnormal data
        plt.scatter(abnormal['Back Angle'], abnormal['Shoulder Alignment'], color='r', label='Anomaly', alpha=0.6)

        plt.title('Posture Data Anomalies Detection')
        plt.xlabel('Back Angle (°)')
        plt.ylabel('Shoulder Alignment (cm)')
        plt.legend()
        plt.show()

def main():
    predictor = FatigueLevelPredictor('detailed_health_logs.csv')
    predictor.load_data()
    predictor.train_model()
    predictor.detect_anomalies()

if __name__ == "__main__":
    main()
