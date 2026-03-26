# Log Parse & Segregator

## Overview

A comprehensive log parsing and categorization system that:
- **Reads** continuous log streams from Kubernetes pods
- **Categorizes** logs into 4 critical categories:
  - **HEALTH** - Pod crashes, memory issues, probe failures
  - **ANOMALY** - Performance degradation, latency, timeouts
  - **SERVICE** - Connectivity errors, HTTP errors, endpoints
  - **SECURITY** - Authentication failures, permission denied
- **Chunks** logs into manageable units (1000 logs per chunk)
- **Stores** in MongoDB with full categorization and statistics
- **Aggregates** metrics for monitoring and analytics

## Architecture

```
Log Stream
    ↓
Log Parser (main.py)
    ↓
Log Categorizer (categorizer.py)
    ├─ HEALTH       ← Regex patterns match
    ├─ ANOMALY      ← for each category
    ├─ SERVICE      ↑
    ├─ SECURITY     
    └─ IGNORED
    ↓
Log Chunker (creates 1000-log chunks)
    ↓
MongoDB Handler (mongodb_handler.py)
    ↓
MongoDB Database (k8s_logs collection)
```

## File Structure

```
log-parse-segregator/
├── config.py              # Configuration & regex patterns
├── categorizer.py         # Log categorization & chunking
├── mongodb_handler.py     # MongoDB connection & storage
├── log_parser.py          # Main parsing logic & stream readers
├── main.py               # CLI application entry point
├── requirements.txt      # Python dependencies
├── USAGE.md             # Usage guide & examples
├── test.sh              # Test script
└── README.md            # This file
```

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Test with Sample Logs

```bash
bash test.sh
```

### 3. Process Real Kubernetes Logs

```bash
# From log generator pod
kubectl logs -n default deployment/log-generator | python main.py

# From specific pod
python main.py --source kubectl --pod log-generator-xyz --namespace default

# From log file
python main.py --source file --file /path/to/logs.txt
```

## Usage Examples

### From stdin (pipe)
```bash
kubectl logs -n default deployment/log-generator | python main.py
```

### From file
```bash
python main.py --source file --file logs.txt --chunk-size 500
```

### From Kubernetes pod
```bash
python main.py --source kubectl --pod my-pod --namespace default
```

### Without MongoDB (local only)
```bash
python main.py --no-mongodb --source file --file logs.txt
```

### Custom MongoDB URI
```bash
python main.py --mongodb-uri "mongodb+srv://user:pass@cluster.mongodb.net/" --source file --file logs.txt
```

## Log Categories

### HEALTH Issues
Keywords that trigger categorization:
- OOMKill
- CrashLoopBackOff
- Liveness probe failed
- Readiness probe
- Back-off, pod restarting
- Memory limit exceeded

### ANOMALY Issues
Keywords:
- CPU throttling
- Memory pressure
- High latency / spike
- Slow response / timeout
- Deadline exceeded
- Performance degradation

### SERVICE Issues
Keywords:
- Connection refused
- 503, 502, 504 (HTTP errors)
- Upstream / no endpoints
- Service unavailable
- DNS resolution failed
- Network error

### SECURITY Issues
Keywords:
- Unauthorized / 401
- Forbidden / 403
- RBAC violation
- Permission denied
- Invalid token
- Brute force

### IGNORED
- INFO logs
- GET 200 OK responses
- Startup messages
- Health check responses
- DEBUG/TRACE logs

## MongoDB Schema

Each chunk stored in MongoDB contains:

```json
{
  "_id": "ObjectId",
  "chunk_id": "chunk_20260323_235959_123456",
  "timestamp": "2026-03-23T23:59:59.123456Z",
  "logs": {
    "HEALTH": [
      {
        "timestamp": "2026-03-23T23:59:59.123Z",
        "raw_message": "OOMKill detected in pod",
        "category": "HEALTH",
        "keywords": ["OOMKill"],
        "line_length": 28
      }
    ],
    "ANOMALY": [...],
    "SERVICE": [...],
    "SECURITY": [...]
  },
  "stats": {
    "total_logs": 1000,
    "health_count": 150,
    "anomaly_count": 250,
    "service_count": 300,
    "security_count": 200,
    "ignored_count": 100
  }
}
```

## MongoDB Queries

### Get all health issues
```javascript
db.log_streams.find({"logs.HEALTH": {$exists: true, $ne: []}})
```

### Get chunks with security issues
```javascript
db.log_streams.find({"stats.security_count": {$gt: 0}})
```

### Aggregate all categories
```javascript
db.log_streams.aggregate([
  {
    $group: {
      _id: null,
      total_chunks: {$sum: 1},
      total_logs: {$sum: "$stats.total_logs"},
      total_health: {$sum: "$stats.health_count"},
      total_anomaly: {$sum: "$stats.anomaly_count"},
      total_service: {$sum: "$stats.service_count"},
      total_security: {$sum: "$stats.security_count"}
    }
  }
])
```

### Find recent chunks with anomalies
```javascript
db.log_streams.find({"stats.anomaly_count": {$gt: 0}})
  .sort({"timestamp": -1})
  .limit(10)
```

### Export chunks to CSV (via aggregation)
```javascript
db.log_streams.aggregate([
  {$match: {"stats.health_count": {$gt: 0}}},
  {
    $project: {
      chunk_id: 1,
      timestamp: 1,
      total_logs: "$stats.total_logs",
      health: "$stats.health_count"
    }
  }
])
```

## Configuration

Edit `config.py` to:
- Add/modify regex patterns for categories
- Change MongoDB connection details
- Adjust ignored patterns
- Add custom categories

## Performance

- **Processing Speed**: ~1000-5000 logs/second
- **Memory Usage**: ~50MB for parser + current chunk
- **Chunk Size**: 1000 logs per chunk (configurable)
- **MongoDB Indexes**: Optimized for common queries

## Troubleshooting

### MongoDB Connection Failed
```bash
python main.py --no-mongodb --source file --file logs.txt
```

### High Memory Usage
Reduce chunk size:
```bash
python main.py --chunk-size 100
```

### No MongoDB installed locally?
Use cloud MongoDB (Atlas):
```bash
python main.py --mongodb-uri "mongodb+srv://user:pass@cluster.mongodb.net/"
```

## API Reference

### LogCategorizer

```python
from categorizer import LogCategorizer

categorizer = LogCategorizer()
category = categorizer.categorize_log("OOMKill detected")
# Returns: "HEALTH"

keywords = categorizer.extract_keywords("OOMKill detected", "HEALTH")
# Returns: ["OOMKill"]
```

### LogParser

```python
from log_parser import LogParser

parser = LogParser(max_logs_per_chunk=1000)
stats = parser.process_log_stream(log_lines)
parser.dump_chunk()
```

### MongoDBHandler

```python
from mongodb_handler import MongoDBHandler

handler = MongoDBHandler()
handler.connect()
handler.insert_chunk(chunk_data)
stats = handler.get_statistics()
handler.disconnect()
```

## Integration with Kubernetes

### Deploy log collector sidecar
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: log-collector
spec:
  containers:
  - name: log-collector
    image: python:3.11
    command:
      - bash
      - -c
      - |
        pip install -r requirements.txt
        kubectl logs -n default deployment/log-generator | python main.py
    volumeMounts:
    - name: parser
      mountPath: /app
  volumes:
  - name: parser
    configMap:
      name: log-parser-code
```

## Contributing

To add new categories or patterns:

1. Edit `config.py`
2. Add keywords to the appropriate category
3. Test with `bash test.sh`
4. Redeploy

## License

MIT License - Use freely for monitoring and logging

## Support

For issues or questions:
1. Check USAGE.md for examples
2. Review test.sh output
3. Enable debug mode in MongoDB handler
4. Check logs at `/tmp/mongodb.log`
