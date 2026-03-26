"""
MongoDB data extraction and feature engineering
"""

import re
import numpy as np
import pandas as pd
from typing import Dict, List
from datetime import datetime
from pymongo import MongoClient
from config import MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION, FEATURE_PATTERNS


class MongoDBFeatureExtractor:
    """Extract log chunks from MongoDB and convert to ML features"""
    
    def __init__(self, uri: str = MONGODB_URI, db_name: str = MONGODB_DB, 
                 collection_name: str = MONGODB_COLLECTION):
        """Initialize MongoDB connection"""
        self.uri = uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.collection = None
        
    def connect(self) -> bool:
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')
            self.collection = self.client[self.db_name][self.collection_name]
            print("✅ Connected to MongoDB")
            return True
        except Exception as e:
            print(f"❌ MongoDB connection failed: {e}")
            return False
    
    def disconnect(self):
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            print("✅ Disconnected from MongoDB")
    
    def fetch_latest_chunks(self, limit: int = 6) -> List[Dict]:
        """
        Fetch latest N log chunks from MongoDB
        
        Args:
            limit: Number of latest chunks to fetch
            
        Returns:
            List of chunk documents
        """
        try:
            chunks = list(self.collection.find()
                         .sort("_id", -1)
                         .limit(limit))
            
            print(f"\n📦 Fetched {len(chunks)} latest chunks from MongoDB")
            print(f"{'='*70}")
            
            for i, chunk in enumerate(chunks, 1):
                total_logs = chunk.get('stats', {}).get('total_logs', 0)
                timestamp = chunk.get('timestamp', 'N/A')
                health = chunk.get('stats', {}).get('health_count', 0)
                anomaly = chunk.get('stats', {}).get('anomaly_count', 0)
                service = chunk.get('stats', {}).get('service_count', 0)
                security = chunk.get('stats', {}).get('security_count', 0)
                
                print(f"Chunk {i}: {total_logs} logs | {timestamp}")
                print(f"  Categories: HEALTH={health}, ANOMALY={anomaly}, SERVICE={service}, SECURITY={security}")
                print(f"  Logs: {len(chunk.get('logs', []))} entries")
            
            return chunks
        
        except Exception as e:
            print(f"❌ Failed to fetch chunks: {e}")
            return []
    
    def extract_features_from_logs(self, logs: List[str]) -> Dict:
        """
        Extract ML features from raw log strings or log dictionaries
        
        Args:
            logs: List of raw log strings or log dictionaries
            
        Returns:
            Dictionary of extracted features
        """
        features = {
            'latency': [],
            'db_query_time': [],
            'cpu_usage': [],
            'memory_usage': [],
            'gc_time': [],
            'queue_depth': [],
            'request_rate': [],
            'timeout_count': 0,
            'error_rate': [],
        }
        
        for log in logs:
            # Handle both string logs and dictionary logs with 'raw_message' key
            if isinstance(log, dict):
                log_text = log.get('raw_message', '')
            elif isinstance(log, str):
                log_text = log
            else:
                continue
                
            log_lower = log_text.lower()
            
            # Extract numeric features using regex
            for feature_name, pattern in FEATURE_PATTERNS.items():
                if feature_name in ['timeout_count']:
                    # Count-based feature
                    if re.search(pattern, log_lower):
                        features['timeout_count'] += 1
                else:
                    # Numeric features
                    match = re.search(pattern, log_lower)
                    if match:
                        try:
                            value = float(match.group(1))
                            features[feature_name].append(value)
                        except (ValueError, IndexError):
                            pass
        
        return features
    
    def aggregate_chunk_features(self, chunks: List[Dict]) -> pd.DataFrame:
        """
        Convert chunk logs to aggregated feature vectors
        
        Args:
            chunks: List of chunk documents from MongoDB
            
        Returns:
            DataFrame with one row per chunk containing aggregated features
        """
        feature_rows = []
        
        print(f"\n📊 Extracting features from {len(chunks)} chunks...")
        print(f"{'='*70}")
        
        for chunk_idx, chunk in enumerate(chunks, 1):
            logs = chunk.get('logs', [])
            
            # Extract features from all logs in chunk
            features = self.extract_features_from_logs(logs)
            
            # Aggregate features into statistics
            feature_vector = {
                'timestamp': chunk.get('timestamp', datetime.now().isoformat()),
                'chunk_id': chunk.get('chunk_id', f"chunk_{chunk_idx}"),
                'total_logs': len(logs),
                'health_count': chunk.get('stats', {}).get('health_count', 0),
                'anomaly_count': chunk.get('stats', {}).get('anomaly_count', 0),
                'service_count': chunk.get('stats', {}).get('service_count', 0),
                'security_count': chunk.get('stats', {}).get('security_count', 0),
                
                # Performance metrics (aggregated)
                'avg_latency': np.mean(features['latency']) if features['latency'] else 0,
                'max_latency': np.max(features['latency']) if features['latency'] else 0,
                'std_latency': np.std(features['latency']) if features['latency'] else 0,
                
                'avg_db_query_time': np.mean(features['db_query_time']) if features['db_query_time'] else 0,
                'max_db_query_time': np.max(features['db_query_time']) if features['db_query_time'] else 0,
                
                # Resource metrics
                'avg_cpu_usage': np.mean(features['cpu_usage']) if features['cpu_usage'] else 0,
                'max_cpu_usage': np.max(features['cpu_usage']) if features['cpu_usage'] else 0,
                
                'avg_memory_usage': np.mean(features['memory_usage']) if features['memory_usage'] else 0,
                'max_memory_usage': np.max(features['memory_usage']) if features['memory_usage'] else 0,
                
                'avg_gc_time': np.mean(features['gc_time']) if features['gc_time'] else 0,
                
                # Queue/Load metrics
                'avg_queue_depth': np.mean(features['queue_depth']) if features['queue_depth'] else 0,
                'max_queue_depth': np.max(features['queue_depth']) if features['queue_depth'] else 0,
                
                'avg_request_rate': np.mean(features['request_rate']) if features['request_rate'] else 0,
                'timeout_events': features['timeout_count'],
                
                # Error metrics
                'avg_error_rate': np.mean(features['error_rate']) if features['error_rate'] else 0,
            }
            
            feature_rows.append(feature_vector)
            
            print(f"✅ Chunk {chunk_idx}: {len(logs)} logs processed")
            print(f"   Latency: avg={feature_vector['avg_latency']:.0f}ms, max={feature_vector['max_latency']:.0f}ms")
            print(f"   CPU: avg={feature_vector['avg_cpu_usage']:.1f}%, max={feature_vector['max_cpu_usage']:.1f}%")
            print(f"   Memory: avg={feature_vector['avg_memory_usage']:.1f}%, max={feature_vector['max_memory_usage']:.1f}%")
            print(f"   Queue Depth: avg={feature_vector['avg_queue_depth']:.0f}, max={feature_vector['max_queue_depth']:.0f}")
        
        df = pd.DataFrame(feature_rows)
        print(f"\n✅ Extracted features for {len(df)} chunks")
        return df
