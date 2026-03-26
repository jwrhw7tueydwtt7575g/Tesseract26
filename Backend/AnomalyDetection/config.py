"""
Configuration for ML Anomaly Detection Pipeline
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ============================================================================
# MONGODB CONFIGURATION
# ============================================================================

MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://vivekchaudhari3718:vivekchaudhari3718@cluster1.9qlun5j.mongodb.net/")
MONGODB_DB = os.getenv("MONGODB_DB", "k8s_logs")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "log_streams")

# ============================================================================
# MLFLOW CONFIGURATION
# ============================================================================

MLFLOW_TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://localhost:5000")
MLFLOW_EXPERIMENT_NAME = "Kubernetes-Log-Anomaly-Detection"
MLFLOW_BACKEND_STORE_URI = os.getenv("MLFLOW_BACKEND_STORE_URI", "./mlruns")

# ============================================================================
# ISOLATION FOREST PARAMETERS
# ============================================================================

ISOLATION_FOREST_PARAMS = {
    'contamination': 0.1,          # Expected % of anomalies
    'random_state': 42,
    'n_estimators': 100,
    'max_samples': 'auto',
    'max_features': 1.0,
    'bootstrap': False
}

# ============================================================================
# FEATURE EXTRACTION PATTERNS
# ============================================================================

FEATURE_PATTERNS = {
    'latency': r'latency[=:\s]+(\d+)\s*(?:ms)?',
    'db_query_time': r'(?:query_time|took|took\s+|query\s+took)\s*(\d+)\s*(?:ms)?',
    'cpu_usage': r'(?:cpu.*?(?:usage|spike|:).*?current|cpu)\s*[:=]?\s*(\d+)\s*%',
    'memory_usage': r'(?:memory.*?(?:at|usage)|heap\s+memory\s+(?:usage\s+)?at)\s+(\d+)%',
    'gc_time': r'(?:garbage\s+collection\s+pause|gc\s+time|gc_time)\s*[:=\s]+(\d+)\s*(?:ms)?',
    'queue_depth': r'(?:queue\s+depth|pending\s+requests)\s*[:=\s]+(\d+)',
    'request_rate': r'(?:rps|requests.*?sec|request.*?rate)\s*[:=\s]+(\d+)',
    'timeout_count': r'(?:timeout|connection.*?timeout)',
    'error_rate': r'(?:error.*?rate)\s*[:=]\s*([\d.]+)',
}

# ============================================================================
# VISUALIZATION CONFIGURATION
# ============================================================================

OUTPUT_DIR = "./ml_results"
VISUALIZATION_DPI = 300
VISUALIZATION_FIGSIZE_DEFAULT = (14, 10)

# ============================================================================
# LOGGING CONFIGURATION
# ============================================================================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
