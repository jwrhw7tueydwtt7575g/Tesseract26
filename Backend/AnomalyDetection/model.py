"""
Isolation Forest model training and prediction
"""

import numpy as np
import pandas as pd
from typing import Dict, Tuple
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler


class IsolationForestAnomalyDetector:
    """Train and evaluate Isolation Forest model for anomaly detection"""
    
    def __init__(self, contamination: float = 0.1, random_state: int = 42, n_estimators: int = 100):
        """Initialize Isolation Forest"""
        self.model = IsolationForest(
            contamination=contamination,
            random_state=random_state,
            n_estimators=n_estimators,
            max_samples='auto',
            max_features=1.0,
            bootstrap=False
        )
        self.scaler = StandardScaler()
        self.feature_columns = None
        self.X_scaled = None
        
    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare features for ML model (exclude metadata columns)
        
        Args:
            df: DataFrame with all features
            
        Returns:
            DataFrame with only ML features
        """
        # Metadata columns to exclude
        exclude_cols = ['timestamp', 'chunk_id', 'health_count', 'anomaly_count', 
                       'service_count', 'security_count', 'total_logs']
        
        self.feature_columns = [col for col in df.columns if col not in exclude_cols]
        
        print(f"\n🧠 Using {len(self.feature_columns)} features for ML model:")
        for col in self.feature_columns:
            print(f"   • {col}")
        
        return df[self.feature_columns]
    
    def train(self, df: pd.DataFrame) -> Dict:
        """
        Train Isolation Forest model
        
        Args:
            df: DataFrame with features
            
        Returns:
            Dictionary with training results
        """
        print(f"\n🔧 Training Isolation Forest...")
        print(f"{'='*70}")
        
        # Prepare features
        X = self.prepare_features(df)
        
        # Handle missing values
        X = X.fillna(0)
        
        # Scale features
        self.X_scaled = self.scaler.fit_transform(X)
        
        # Train model
        self.model.fit(self.X_scaled)
        
        # Get anomaly predictions and scores
        predictions = self.model.predict(self.X_scaled)  # -1 = anomaly, 1 = normal
        anomaly_scores = self.model.score_samples(self.X_scaled)  # Lower = more anomalous
        
        # Convert to binary labels (0 = normal, 1 = anomaly)
        y_pred = (predictions == -1).astype(int)
        
        # Calculate metrics
        n_anomalies = np.sum(y_pred)
        n_normal = len(y_pred) - n_anomalies
        anomaly_percentage = (n_anomalies / len(y_pred)) * 100
        
        results = {
            'n_samples': len(df),
            'n_anomalies': int(n_anomalies),
            'n_normal': int(n_normal),
            'anomaly_percentage': float(anomaly_percentage),
            'predictions': y_pred,
            'anomaly_scores': anomaly_scores,
            'model': self.model,
            'scaler': self.scaler
        }
        
        print(f"✅ Model trained successfully!")
        print(f"   Total samples: {results['n_samples']}")
        print(f"   Anomalies detected: {results['n_anomalies']} ({results['anomaly_percentage']:.1f}%)")
        print(f"   Normal samples: {results['n_normal']}")
        
        return results
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Predict anomalies on new data
        
        Args:
            X: Feature matrix (already scaled)
            
        Returns:
            Tuple of (predictions, anomaly_scores)
        """
        predictions = self.model.predict(X)
        anomaly_scores = self.model.score_samples(X)
        return predictions, anomaly_scores
    
    def get_feature_importances_mock(self) -> Dict[str, float]:
        """
        Return feature importance-like scores based on standard deviation
        
        Returns:
            Dictionary with feature importance scores
        """
        importances = {}
        
        if self.X_scaled is not None:
            # Use standard deviation as importance proxy
            stds = np.std(self.X_scaled, axis=0)
            for col, std in zip(self.feature_columns, stds):
                importances[col] = float(std)
        
        return importances
