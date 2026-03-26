# 🔍 Kubernetes Log Anomaly Detection - Technical Documentation

## File-by-File Implementation Guide

---

## 📄 **1. config.py** - Configuration & Feature Extraction Rules

### Purpose
Centralized configuration for database connections, feature extraction patterns, and model hyperparameters.

### Key Components

```python
# MongoDB Configuration
MONGODB_URI = "mongodb+srv://..."
MONGODB_DB = "logdatabase"
MONGODB_COLLECTION = "logs"

# Feature Extraction Patterns (Regex for log parsing)
FEATURE_PATTERNS = {
    'latency': r'latency[=:\s]+(\d+)\s*(?:ms)?',
    'db_query_time': r'(?:query_time|took|took\s+|query\s+took)\s*(\d+)',
    'cpu_usage': r'(?:cpu.*?(?:usage|spike|:).*?current|cpu)\s*[:=]?\s*(\d+)\s*%',
    'memory_usage': r'(?:memory.*?(?:at|usage)|heap\s+memory\s+(?:usage\s+)?at)\s+(\d+)%',
    'gc_time': r'(?:garbage\s+collection\s+pause|gc\s+time|gc_time)\s*[:=\s]+(\d+)',
    'queue_depth': r'(?:queue\s+depth|pending\s+requests)\s*[:=\s]+(\d+)',
    'request_rate': r'(?:request.*?rate|rpm|rps)\s*[:=\s]+(\d+)',
    'timeout_count': r'(?:timeout|connection.*?timeout)\s*[:=]?\s*(\d+)?',
    'error_rate': r'(?:error.*?rate|errors?)\s*[:=\s]+(\d+)'
}

# Model Configuration
CONTAMINATION_RATIO = 0.1  # Expect 10% anomalies
N_ESTIMATORS = 100         # Number of trees
RANDOM_STATE = 42          # Reproducibility
```

---

## 📄 **2. data_extractor.py** - Feature Extraction from MongoDB

### Purpose
Connect to MongoDB, fetch log chunks, extract 16 features using regex patterns, return structured DataFrame.

### Class: `MongoDBFeatureExtractor`

```python
class MongoDBFeatureExtractor:
    """Extract features from MongoDB log chunks"""
    
    def __init__(self):
        self.client = None
        self.db = None
        self.collection = None
        self.feature_columns = []
    
    def connect(self) -> bool:
        """Connect to MongoDB Atlas"""
        # Returns: True if connected, False if failed
    
    def fetch_latest_chunks(self, limit=20) -> List[Dict]:
        """Fetch N latest chunks from MongoDB"""
        # Returns: List of chunk documents
    
    def aggregate_chunk_features(self, chunks) -> pd.DataFrame:
        """Extract 16 features from chunks"""
        # Feature extraction logic:
        # 1. Loop through each chunk
        # 2. Parse each log with regex patterns
        # 3. Calculate aggregate statistics
        # 4. Return DataFrame with 16 columns
```

### Features Extracted

```
1. avg_latency          - Mean latency across logs in chunk
2. max_latency          - Peak latency
3. std_latency          - Latency variance
4. avg_db_query_time    - Average database query time
5. avg_cpu_usage        - Mean CPU utilization
6. max_cpu_usage        - Peak CPU usage
7. avg_memory_usage     - Mean memory allocation
8. max_memory_usage     - Peak memory usage
9. avg_gc_time          - Garbage collection pause duration
10. avg_queue_depth     - Average pending requests
11. max_queue_depth     - Peak queue depth
12. timeout_events      - Count of timeout errors
13. error_count         - Total errors in chunk
14. request_rate        - Requests processed per chunk
15. cache_hit_rate      - Cache efficiency percentage
16. throughput          - Total throughput
```

### Example Usage

```python
extractor = MongoDBFeatureExtractor()
extractor.connect()
chunks = extractor.fetch_latest_chunks(limit=12)
df = extractor.aggregate_chunk_features(chunks)
print(df.shape)  # (12, 16) - 12 chunks, 16 features
```

---

## 📄 **3. model.py** - Isolation Forest Anomaly Detection

### Purpose
Train ML model to detect anomalous chunks using Isolation Forest algorithm.

### Class: `IsolationForestAnomalyDetector`

```python
class IsolationForestAnomalyDetector:
    """Isolation Forest for anomaly detection"""
    
    def __init__(self, contamination=0.1, n_estimators=100):
        self.model = IsolationForest(
            contamination=contamination,
            n_estimators=n_estimators,
            random_state=42
        )
        self.scaler = StandardScaler()
        self.feature_columns = [...]
    
    def train(self, df: pd.DataFrame) -> Dict:
        """Train model on chunk features"""
        # 1. Prepare features (drop timestamp, chunk_id)
        # 2. Handle missing values (fillna with 0)
        # 3. Scale features (StandardScaler)
        # 4. Train Isolation Forest
        # 5. Get predictions (-1=anomaly, 1=normal)
        # 6. Get anomaly scores (lower = more anomalous)
        # 7. Return results dictionary
        
        # Returns:
        # {
        #     'n_samples': 12,
        #     'n_anomalies': 2,
        #     'n_normal': 10,
        #     'anomaly_percentage': 16.7,
        #     'predictions': [1,1,1,1,1,1,-1,1,1,1,1,-1],
        #     'anomaly_scores': [-0.35, -0.40, ..., -0.58],
        #     'model': <trained model>,
        #     'scaler': <fitted scaler>
        # }
    
    def predict(self, X: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """Predict anomalies on new data"""
        # Returns: (predictions, anomaly_scores)
```

### Algorithm Overview

**Isolation Forest** works by:
1. Randomly selecting features
2. Randomly selecting split values
3. Building trees that isolate anomalies
4. Scoring based on path length to isolation

**Key Insight**: Anomalies are isolated faster (shorter paths), so they get lower scores.

---

## 📄 **4. main.py** - Complete ML Pipeline Orchestrator

### Purpose
Orchestrate the entire pipeline: load data → extract features → train model → detect anomalies → generate visualizations.

### Execution Flow

```
main.py
├─ 1. Load chunk data from MongoDB
├─ 2. Extract 16 features using regex patterns
├─ 3. Train Isolation Forest model
├─ 4. Get anomaly predictions and scores
├─ 5. Analyze results
│   ├─ Total chunks analyzed
│   ├─ Anomalies detected
│   ├─ Anomaly percentage
│   └─ Per-chunk details
├─ 6. Generate visualizations
│   ├─ Anomaly heatmap (PNG)
│   ├─ Feature comparison (PNG)
│   └─ Time series with markers (PNG)
└─ 7. Save results to JSON
```

### Main Function

```python
def run_pipeline():
    """Execute complete ML pipeline"""
    # Step 1: Load data
    extractor = MongoDBFeatureExtractor()
    extractor.connect()
    chunks = extractor.fetch_latest_chunks(limit=20)
    df = extractor.aggregate_chunk_features(chunks)
    
    # Step 2: Train model
    detector = IsolationForestAnomalyDetector()
    results = detector.train(df)
    
    # Step 3: Generate report
    print(f"✅ Chunks: {results['n_samples']}")
    print(f"🔴 Anomalies: {results['n_anomalies']}")
    
    # Step 4: Save results
    save_results(results)
```

---

## 📄 **5. dash_dashboard.py** - Interactive Monitoring Dashboard

### Purpose
Real-time interactive dashboard with 5 monitoring tabs, auto-refreshing every 30 seconds.

### Architecture

```
Dash App
├─ Layout (5 Tabs)
├─ Callbacks (Auto-refresh)
└─ Data Store (MongoDB cache)
```

### 5 Dashboard Tabs

#### **Tab 1: Overview 📊**
- 4 KPI Cards:
  - Total Chunks
  - Anomaly Count
  - Average Latency
  - Average Memory
- 4 Charts:
  - Latency Trend (line with anomaly markers)
  - Memory Trend (line with anomaly markers)
  - CPU vs Memory Scatter (color-coded)
  - Anomaly Score Distribution (histogram)

#### **Tab 2: Model Drift 📉**
- Drift Summary Card (status badge)
- 3 Distribution Charts:
  - Latency: Early vs Late
  - Memory: Early vs Late
  - CPU: Early vs Late
- Feature Stats Bar Chart (comparison)

#### **Tab 3: Anomalies 🔴**
- Anomaly Count & Rate
- Feature Heatmap
- Detailed Anomaly Table:
  - Chunk ID
  - Latency (ms)
  - Memory (%)
  - Timeout Events
  - Anomaly Score

#### **Tab 4: Features 🔍**
- Latency Distribution (histogram)
- Memory Distribution (histogram)
- Correlation Matrix (heatmap)

#### **Tab 5: Time Series 📈**
- Prophet Latency Forecast:
  - Historical latency (cyan line)
  - 5-step forecast (orange dashed)
  - 95% confidence interval (shaded)
- Trend Component (green line)
- Forecast Error (MAPE bar chart)

### Auto-Refresh Mechanism

```python
@app.callback(
    [Output('kpi-cards', 'children'),
     Output('latency-trend', 'figure'),
     ...],
    [Input('interval-component', 'n_intervals')]  # Triggers every 30 seconds
)
def update_overview(n):
    """Refresh all data from MongoDB"""
    df, chunks, _ = load_data()          # Fetch latest chunks
    detector, predictions, scores = train_model(df)  # Retrain model
    # Generate all visualizations
    return kpi_children, fig_latency, ...
```

### Color Scheme

```
Background: #0a0e1a (Deep dark)
Accent 1:   #00d9ff (Cyan - primary)
Accent 2:   #00ff88 (Green - success)
Accent 3:   #ffaa00 (Orange - warning)
Accent 4:   #ff3333 (Red - anomaly)
Text:       #ffffff (White)
Grid:       #1a1f2e (Dark gray)
```

---

## 📄 **6. prophet_forecaster.py** - Time Series Forecasting

### Purpose
Train Facebook Prophet models for time series forecasting and anomaly detection.

### Class: `ProphetForecaster`

```python
class ProphetForecaster:
    """Time series forecasting with Prophet"""
    
    def train_prophet(self, prophet_df, metric_name) -> Prophet:
        """Train Prophet model"""
        model = Prophet(
            yearly_seasonality=False,
            daily_seasonality=False,
            interval_width=0.95,
            growth='linear'
        )
        model.fit(prophet_df)
        return model
    
    def generate_forecast(self, model, periods=5) -> pd.DataFrame:
        """Generate N-step ahead forecast"""
        future = model.make_future_dataframe(periods=periods, freq='min')
        forecast = model.predict(future)
        return forecast  # Contains yhat, yhat_upper, yhat_lower, trend
```

### Prophet Features

- **Automatic Seasonality Detection**: Learns recurring patterns
- **Trend Extraction**: Separates long-term trends
- **Confidence Intervals**: 95% prediction bounds
- **Robust to Missing Data**: Handles gaps in time series
- **Holiday Effects**: Accounts for calendar anomalies

### Forecast Structure

```json
{
  "ds": "2026-03-26 00:35:00",
  "yhat": 3725.5,              // Forecast value
  "yhat_upper": 4684.3,        // Upper 95% bound
  "yhat_lower": 2684.5,        // Lower 95% bound
  "trend": 3725.5,             // Trend component
  "yearly": 0.0,               // Yearly seasonality
  "yearly_upper": 0.0,
  "yearly_lower": 0.0
}
```

---

## 📄 **7. stream_parser.py** - Log Streaming & Chunking

### Purpose
Real-time collection of logs from Kubernetes pod, chunk into 50-log groups, send to MongoDB.

### Implementation

```python
def stream_and_chunk_logs(pod_name, namespace='default', chunk_size=50):
    """Stream logs from pod and chunk them"""
    # 1. Connect to Kubernetes pod
    # 2. Stream logs in real-time
    # 3. Categorize each log
    # 4. Accumulate 50 logs per chunk
    # 5. Send chunk to MongoDB
    # 6. Create new chunk
```

### Log Categorization

- **HEALTH**: Normal operations, low latency, normal resources
- **ANOMALY**: High latency, CPU spikes, memory pressure
- **SERVICE**: API calls, database queries, cache operations
- **SECURITY**: Timeouts, auth failures, security events

---

## 🔗 Data Flow Diagram

```
┌──────────────────────────┐
│ Kubernetes Pod           │
│ (log_generator.py)       │
│ 500+ logs/min            │
└────────────┬─────────────┘
             │
             ↓
┌──────────────────────────┐
│ Stream Parser            │
│ (stream_parser.py)       │
│ Chunk: 50 logs           │
│ Categorize: 4 types      │
└────────────┬─────────────┘
             │
             ↓
┌──────────────────────────┐
│ MongoDB Atlas            │
│ (Cloud Storage)          │
│ 300+ logs in 12 chunks   │
└────────────┬─────────────┘
             │
             ↓
┌──────────────────────────┐
│ Feature Extraction       │
│ (data_extractor.py)      │
│ 16 features extracted    │
└────────────┬─────────────┘
             │
        ┌────┴────┐
        ↓         ↓
    ┌──────┐  ┌────────┐
    │ ML   │  │Prophet │
    │Model │  │Model   │
    └──┬───┘  └────┬───┘
       │            │
       └────┬───────┘
            ↓
    ┌──────────────────────┐
    │ Plotly Dash          │
    │ (5 Monitoring Tabs)  │
    │ Auto-refresh: 30s    │
    │ URL: localhost:8050  │
    └──────────────────────┘
```

---

## 🧪 Testing the System

### **Test 1: Feature Extraction**

```python
from data_extractor import MongoDBFeatureExtractor

extractor = MongoDBFeatureExtractor()
extractor.connect()
chunks = extractor.fetch_latest_chunks(limit=5)
df = extractor.aggregate_chunk_features(chunks)

print(f"Shape: {df.shape}")  # Should be (5, 16)
print(f"Columns: {df.columns.tolist()}")
print(f"Sample: {df.iloc[0]}")
```

### **Test 2: Anomaly Detection**

```python
from model import IsolationForestAnomalyDetector

detector = IsolationForestAnomalyDetector()
results = detector.train(df)

print(f"Anomalies: {results['n_anomalies']}")
print(f"Rate: {results['anomaly_percentage']:.1f}%")
print(f"Anomalous chunks: {df[df['anomaly']==1].index.tolist()}")
```

### **Test 3: Prophet Forecasting**

```python
from prophet_forecaster import ProphetForecaster

forecaster = ProphetForecaster()
df_result = forecaster.run_full_pipeline()

print(f"Models trained: {list(forecaster.models.keys())}")
print(f"Forecasts generated: {len(forecaster.forecasts)}")
```

### **Test 4: Dashboard Access**

```bash
# Start dashboard
cd /home/vivek/Desktop/Ai-Agent/Backend/AnomalyDetection
python3 dash_dashboard.py &

# Wait 5 seconds
sleep 5

# Test endpoint
curl http://localhost:8050
```

---

## 📊 Expected Output Examples

### **Feature Extraction Output**

```
✅ Connected to MongoDB
✅ Fetched 12 chunks (300 logs)
✅ Extracted features for 12 chunks:
   - avg_latency: 4823ms
   - avg_cpu_usage: 71.3%
   - avg_memory_usage: 88.2%
   - avg_queue_depth: 396
```

### **Anomaly Detection Output**

```
🔧 Training Isolation Forest...
✅ Model trained successfully!
   Total samples: 12
   Anomalies detected: 2 (16.7%)
   Normal samples: 10

🔴 Anomalous Chunk 1:
   ID: chunk_20260325_183457_776032
   Latency: 6493ms (anomaly_score=-0.58)
   Queue Depth: 711 (CRITICAL)
```

### **Prophet Output**

```
✅ Prophet model trained for avg_latency
   Next Forecast: 3725ms
   Upper Bound: 4684ms
   Lower Bound: 2684ms
   Trend: Downward ↓
```

---

## 🚨 Common Issues & Solutions

### Issue 1: MongoDB Connection Timeout
```python
# Solution: Check MONGODB_URI in config.py
# Add to config.py:
MONGODB_URI = "mongodb+srv://<user>:<pass>@<cluster>.mongodb.net/?retryWrites=true&w=majority"
```

### Issue 2: Feature Extraction Returns NaN
```python
# Solution: Check regex patterns in config.py
# Verify log format matches pattern
import re
pattern = FEATURE_PATTERNS['latency']
log = "latency=4988ms"
match = re.search(pattern, log)
print(match.group(1))  # Should print: 4988
```

### Issue 3: Dashboard Not Refreshing
```bash
# Solution: Check interval component
# Verify MongoDB connection in callback
tail -50 /path/to/dashboard.log
```

---

## 📈 Performance Metrics

```
Feature Extraction Time: ~500ms for 12 chunks
Model Training Time: ~200ms
Prediction Time: ~50ms
Dashboard Refresh: ~1-2 seconds
MongoDB Query Time: ~100ms
Prophet Forecast Time: ~2-3 seconds
```

---

## ✅ Validation Checklist

- [x] Kubernetes pod running continuously
- [x] Logs generating with real metrics
- [x] MongoDB connected and storing logs
- [x] Feature extraction working (16 features)
- [x] Anomaly detection finding anomalies
- [x] Prophet models training
- [x] Dashboard displaying data
- [x] Auto-refresh working every 30 seconds
- [x] All visualizations rendering
- [x] Dark mode styling applied

---

**Last Updated**: Mar 26, 2026  
**System Status**: ✅ OPERATIONAL

