"""
MLflow experiment tracking and logging
"""

import os
import json
from datetime import datetime
from typing import Dict, List
import numpy as np
import pandas as pd
import mlflow
import mlflow.sklearn


class MLFlowExperimentTracker:
    """Track experiments, metrics, and models with MLflow"""
    
    def __init__(self, tracking_uri: str = "http://localhost:5000", 
                 experiment_name: str = "Kubernetes-Log-Anomaly-Detection"):
        """Initialize MLflow"""
        self.tracking_uri = tracking_uri
        self.experiment_name = experiment_name
        self.run = None
        
    def setup_mlflow(self):
        """Configure MLflow tracking"""
        mlflow.set_tracking_uri(self.tracking_uri)
        
        # Create or get experiment
        try:
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if experiment is None:
                mlflow.create_experiment(self.experiment_name)
            mlflow.set_experiment(self.experiment_name)
            print(f"✅ MLflow configured: {self.tracking_uri}")
            print(f"   Experiment: {self.experiment_name}")
        except Exception as e:
            print(f"⚠️  MLflow setup warning: {e}")
            print(f"   Continuing without MLflow remote tracking...")
    
    def log_training_run(self, df: pd.DataFrame, training_results: Dict, 
                        detector, run_name: str = "isolation_forest_baseline"):
        """
        Log complete training run to MLflow
        
        Args:
            df: DataFrame with all features and metadata
            training_results: Dictionary with training results
            detector: Trained detector model
            run_name: Name for this run
        """
        with mlflow.start_run(run_name=run_name) as run:
            print(f"\n📊 Logging to MLflow (Run: {run.info.run_id})...")
            print(f"{'='*70}")
            
            # Log parameters
            mlflow.log_param("model_type", "IsolationForest")
            mlflow.log_param("contamination", 0.1)
            mlflow.log_param("n_estimators", 100)
            mlflow.log_param("n_chunks", training_results['n_samples'])
            mlflow.log_param("n_features", len(detector.feature_columns))
            
            # Log metrics
            mlflow.log_metric("n_anomalies", training_results['n_anomalies'])
            mlflow.log_metric("n_normal", training_results['n_normal'])
            mlflow.log_metric("anomaly_percentage", training_results['anomaly_percentage'])
            mlflow.log_metric("anomaly_ratio", 
                            training_results['n_anomalies'] / training_results['n_samples'])
            
            # Log feature list as artifact
            features_artifact = {
                'features': detector.feature_columns,
                'n_features': len(detector.feature_columns)
            }
            mlflow.log_dict(features_artifact, "features.json")
            
            # Log model
            mlflow.sklearn.log_model(detector.model, "isolation_forest_model")
            
            # Log metadata
            metadata = {
                'timestamp': datetime.now().isoformat(),
                'data_shape': (training_results['n_samples'], len(detector.feature_columns)),
                'anomaly_detection_threshold': 'IsolationForest anomaly score < 0',
                'training_status': 'completed'
            }
            mlflow.log_dict(metadata, "metadata.json")
            
            print(f"✅ Run logged: {run.info.run_id}")
            print(f"   Artifacts: features.json, metadata.json, isolation_forest_model/")
            print(f"   Metrics: anomaly detection baseline established")
            
            return run.info.run_id
    
    def log_anomalies(self, anomalies: List[Dict], run_id: str = None):
        """Log detected anomalies"""
        with mlflow.start_run(run_id=run_id) if run_id else mlflow.active_run() as run:
            anomalies_artifact = {
                'n_anomalies': len(anomalies),
                'anomalies': anomalies
            }
            mlflow.log_dict(anomalies_artifact, "detected_anomalies.json")
