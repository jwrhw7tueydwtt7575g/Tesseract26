#!/bin/bash

"""
Continuous Log Parser - Streams logs from running pod and parses them in real-time
"""

import subprocess
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from log_parser import LogParser
from mongodb_handler import MongoDBHandler
from datetime import datetime

def stream_pod_logs(namespace="default", pod_app_label="logdemogenerator"):
    """Stream logs from running pod and parse in real-time"""
    
    print("=" * 70)
    print("🚀 CONTINUOUS LOG PARSER & SEGREGATOR")
    print("=" * 70)
    print()
    
    # Connect to MongoDB
    print("📚 Connecting to MongoDB...")
    mongodb = MongoDBHandler()
    if not mongodb.connect():
        print("⚠️  MongoDB not available, continuing without storage...")
        mongodb = None
    
    # Initialize parser (50 logs per chunk)
    print(f"📝 Initializing parser (chunk size: 50)")
    parser = LogParser(max_logs_per_chunk=50, mongodb_handler=mongodb)
    
    # Start streaming logs
    print(f"\n📡 Streaming logs from pod (label: {pod_app_label}, namespace: {namespace})")
    print("✅ Press Ctrl+C to stop\n")
    print("-" * 70)
    
    # Build kubectl command to stream logs
    cmd = f"kubectl logs -n {namespace} -l app={pod_app_label} -f --all-containers=true"
    
    try:
        # Start the subprocess
        process = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True,
            bufsize=1
        )
        
        log_count = 0
        chunk_count = 0
        
        # Read logs line by line as they arrive
        while True:
            line = process.stdout.readline()
            
            if not line:
                break
            
            # Parse the log line
            log_entry = parser.parse_log_line(line)
            
            if log_entry:
                log_count += 1
                category = log_entry['category']
                timestamp = datetime.utcnow().strftime('%H:%M:%S')
                
                # Print log as it arrives
                print(f"[{timestamp}] {log_count:4d} | {category:10s} | {line[:60]}")
                
                # Add to current chunk
                parser.current_chunk.add_log(log_entry)
                
                # Dump chunk when full
                if parser.current_chunk.is_full(parser.max_logs_per_chunk):
                    print()
                    print("=" * 70)
                    print(f"📦 CHUNK FULL - Dumping {parser.current_chunk.stats['total_logs']} logs")
                    print("=" * 70)
                    
                    # Store chunk
                    chunk_id = parser.dump_chunk()
                    chunk_count += 1
                    
                    print(f"✅ Chunk {chunk_count} stored: {chunk_id}")
                    print(f"📊 Stats so far: {log_count} logs processed, {chunk_count} chunks dumped")
                    print("-" * 70)
                    print()
    
    except KeyboardInterrupt:
        print("\n" + "=" * 70)
        print("⏹️  STOPPING LOG PARSER")
        print("=" * 70)
        
        # Dump final chunk if any
        if parser.current_chunk.stats['total_logs'] > 0:
            print(f"\n📦 Dumping final chunk with {parser.current_chunk.stats['total_logs']} logs...")
            chunk_id = parser.dump_chunk()
            chunk_count += 1
            print(f"✅ Final chunk stored: {chunk_id}")
        
        # Print summary
        print(f"\n📊 FINAL SUMMARY")
        print("=" * 70)
        print(f"Total logs processed: {log_count}")
        print(f"Total chunks created:  {chunk_count}")
        print(f"Avg logs per chunk:    {log_count/chunk_count if chunk_count > 0 else 0:.1f}")
        
        # Get MongoDB stats
        if mongodb and mongodb.connected:
            print()
            mongo_stats = mongodb.get_statistics()
            if mongo_stats:
                print(f"MongoDB Stats:")
                print(f"  Total chunks in DB: {mongo_stats.get('total_chunks', 0)}")
                print(f"  Total logs in DB:   {mongo_stats.get('total_logs', 0)}")
                print(f"    - Health:        {mongo_stats.get('total_health', 0)}")
                print(f"    - Anomaly:       {mongo_stats.get('total_anomaly', 0)}")
                print(f"    - Service:       {mongo_stats.get('total_service', 0)}")
                print(f"    - Security:      {mongo_stats.get('total_security', 0)}")
            
            mongodb.disconnect()
        
        print("\n✅ Log parser stopped successfully!")
        print("=" * 70)
    
    finally:
        # Clean up
        if process:
            process.terminate()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Continuous Log Parser - Stream logs from running pod"
    )
    
    parser.add_argument(
        "--namespace",
        default="default",
        help="Kubernetes namespace (default: default)"
    )
    
    parser.add_argument(
        "--pod-label",
        default="logdemogenerator",
        help="Pod app label (default: logdemogenerator)"
    )
    
    args = parser.parse_args()
    
    stream_pod_logs(namespace=args.namespace, pod_app_label=args.pod_label)
