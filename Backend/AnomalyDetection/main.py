"""
Main ML Anomaly Detection Pipeline
Orchestrates: Data Fetching -> Feature Extraction -> Model Training -> MLflow Logging -> Visualization
"""

import os
import json
from datetime import datetime
import numpy as np
from config import ISOLATION_FOREST_PARAMS
from data_extractor import MongoDBFeatureExtractor
from model import IsolationForestAnomalyDetector
from visualizer import AnomalyAnalyzer

# MLflow is optional
try:
    from mlflow_tracker import MLFlowExperimentTracker
    from config import MLFLOW_TRACKING_URI, MLFLOW_EXPERIMENT_NAME
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False


def run_anomaly_detection_pipeline():
    """Run complete ML anomaly detection pipeline"""
    
    print(f"\n{'='*70}")
    print(f"🚀 KUBERNETES LOG ANOMALY DETECTION - ML PIPELINE")
    print(f"{'='*70}\n")
    
    # ========================================================================
    # STEP 1: Connect to MongoDB and Fetch Latest Chunks
    # ========================================================================
    print("STEP 1: Fetching data from MongoDB")
    print(f"{'-'*70}")
    
    extractor = MongoDBFeatureExtractor()
    if not extractor.connect():
        print("❌ Failed to connect to MongoDB. Exiting.")
        return
    
    chunks = extractor.fetch_latest_chunks(limit=6)
    
    if not chunks:
        print("❌ No chunks found in MongoDB. Exiting.")
        extractor.disconnect()
        return
    
    # ========================================================================
    # STEP 2: Extract Features from Logs
    # ========================================================================
    print("\nSTEP 2: Extracting ML features from logs")
    print(f"{'-'*70}")
    
    df = extractor.aggregate_chunk_features(chunks)
    
    print("\n📊 Feature Dataset Summary:")
    print(df.to_string())
    
    extractor.disconnect()
    
    # ========================================================================
    # STEP 3: Train Isolation Forest Model
    # ========================================================================
    print("\nSTEP 3: Training Isolation Forest Model")
    print(f"{'-'*70}")
    
    detector = IsolationForestAnomalyDetector(
        contamination=ISOLATION_FOREST_PARAMS['contamination'],
        random_state=ISOLATION_FOREST_PARAMS['random_state'],
        n_estimators=ISOLATION_FOREST_PARAMS['n_estimators']
    )
    training_results = detector.train(df)
    
    # ========================================================================
    # STEP 4: Setup MLflow and Log Experiment (Optional)
    # ========================================================================
    print("\nSTEP 4: Logging to MLflow (Optional)")
    print(f"{'-'*70}")
    
    run_id = "no_mlflow"
    if MLFLOW_AVAILABLE:
        try:
            tracker = MLFlowExperimentTracker(
                tracking_uri=MLFLOW_TRACKING_URI,
                experiment_name=MLFLOW_EXPERIMENT_NAME
            )
            tracker.setup_mlflow()
            run_id = tracker.log_training_run(df, training_results, detector)
        except Exception as e:
            print(f"⚠️  MLflow logging error: {e}")
            print(f"   Continuing without MLflow...")
    else:
        print("ℹ️  MLflow not installed (optional feature)")
        print(f"   To enable: pip install --break-system-packages mlflow")
    
    # ========================================================================
    # STEP 5: Analyze and Visualize Results
    # ========================================================================
    print("\nSTEP 5: Analyzing Anomalies & Generating Visualizations")
    print(f"{'-'*70}")
    
    analyzer = AnomalyAnalyzer(df, training_results)
    analyzer.display_anomalies()
    analyzer.generate_visualizations()
    
    # ========================================================================
    # STEP 6: Save Complete Results JSON
    # ========================================================================
    print("\nSTEP 6: Saving Results")
    print(f"{'-'*70}")
    
    anomaly_mask = training_results['predictions'] == 1
    
    results_json = {
        'timestamp': datetime.now().isoformat(),
        'mlflow_run_id': run_id,
        'model_type': 'IsolationForest',
        'parameters': ISOLATION_FOREST_PARAMS,
        'dataset': {
            'n_chunks': len(df),
            'n_features': len(detector.feature_columns),
            'features': detector.feature_columns
        },
        'results': {
            'n_samples': training_results['n_samples'],
            'n_anomalies': training_results['n_anomalies'],
            'n_normal': training_results['n_normal'],
            'anomaly_percentage': training_results['anomaly_percentage']
        },
        'anomalies': []
    }
    
    # Add anomaly details
    for idx in np.where(anomaly_mask)[0]:
        results_json['anomalies'].append({
            'chunk_id': str(df.iloc[idx]['chunk_id']),
            'timestamp': str(df.iloc[idx]['timestamp']),
            'anomaly_score': float(training_results['anomaly_scores'][idx]),
            'metrics': {
                'avg_latency': float(df.iloc[idx]['avg_latency']),
                'max_latency': float(df.iloc[idx]['max_latency']),
                'avg_cpu_usage': float(df.iloc[idx]['avg_cpu_usage']),
                'max_cpu_usage': float(df.iloc[idx]['max_cpu_usage']),
                'avg_memory_usage': float(df.iloc[idx]['avg_memory_usage']),
                'max_memory_usage': float(df.iloc[idx]['max_memory_usage']),
                'avg_queue_depth': float(df.iloc[idx]['avg_queue_depth']),
                'max_queue_depth': float(df.iloc[idx]['max_queue_depth']),
                'timeout_events': int(df.iloc[idx]['timeout_events']),
                'health_count': int(df.iloc[idx]['health_count']),
                'anomaly_count': int(df.iloc[idx]['anomaly_count']),
                'service_count': int(df.iloc[idx]['service_count']),
                'security_count': int(df.iloc[idx]['security_count']),
            }
        })
    
    output_dir = "./ml_results"
    os.makedirs(output_dir, exist_ok=True)
    
    results_path = os.path.join(output_dir, 'anomaly_detection_results.json')
    with open(results_path, 'w') as f:
        json.dump(results_json, f, indent=2, default=str)
    
    print(f"✅ Results saved to: {results_path}")
    
    # ========================================================================
    # PRINT FINAL SUMMARY
    # ========================================================================
    print(f"\n{'='*70}")
    print(f"✅ PIPELINE COMPLETED SUCCESSFULLY")
    print(f"{'='*70}")
    print(f"📊 Summary:")
    print(f"   • Chunks analyzed: {training_results['n_samples']}")
    print(f"   • Features extracted: {len(detector.feature_columns)}")
    print(f"   • Anomalies detected: {training_results['n_anomalies']} ({training_results['anomaly_percentage']:.1f}%)")
    print(f"   • MLflow Run ID: {run_id}")
    print(f"   • Results JSON: {results_path}")
    print(f"   • Visualizations: {output_dir}/")
    if MLFLOW_AVAILABLE:
        print(f"\n🎯 MLflow Dashboard: http://localhost:5000")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    run_anomaly_detection_pipeline()
