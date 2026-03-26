"""
Main application - Orchestrates log parsing and storage
"""

import argparse
import sys
from log_parser import LogParser, LogStreamReader
from mongodb_handler import MongoDBHandler
from config import MONGODB_URI, MONGODB_DB


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Log Stream Parser & Segregator - Categorize logs and store in MongoDB"
    )
    
    parser.add_argument(
        "--source",
        choices=["stdin", "file", "kubectl"],
        default="stdin",
        help="Log source (default: stdin)"
    )
    
    parser.add_argument(
        "--file",
        help="File path (for --source file)"
    )
    
    parser.add_argument(
        "--pod",
        help="Pod name (for --source kubectl)"
    )
    
    parser.add_argument(
        "--namespace",
        default="default",
        help="Kubernetes namespace (for --source kubectl)"
    )
    
    parser.add_argument(
        "--chunk-size",
        type=int,
        default=20,
        help="Maximum logs per chunk (default: 20)"
    )
    
    parser.add_argument(
        "--mongodb-uri",
        default=MONGODB_URI,
        help="MongoDB connection URI"
    )
    
    parser.add_argument(
        "--mongodb-db",
        default=MONGODB_DB,
        help="MongoDB database name"
    )
    
    parser.add_argument(
        "--no-mongodb",
        action="store_true",
        help="Disable MongoDB storage (logs to console only)"
    )
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🚀 Log Stream Parser & Segregator")
    print("=" * 60)
    
    # Initialize MongoDB handler
    mongodb = None
    if not args.no_mongodb:
        print(f"\n📚 Connecting to MongoDB...")
        mongodb = MongoDBHandler(
            uri=args.mongodb_uri,
            db_name=args.mongodb_db
        )
        if not mongodb.connect():
            print("⚠️  Continuing without MongoDB...")
            mongodb = None
    else:
        print("\n⚠️  MongoDB disabled - logs will be stored locally only")
    
    # Initialize parser
    print(f"\n📝 Initializing parser (chunk size: {args.chunk_size})")
    log_parser = LogParser(
        max_logs_per_chunk=args.chunk_size,
        mongodb_handler=mongodb
    )
    
    # Read logs from source
    print(f"\n📥 Reading logs from {args.source}...")
    logs = []
    
    if args.source == "stdin":
        print("📡 Waiting for logs from stdin (Ctrl+C to stop)...")
        logs = LogStreamReader.read_from_stdin()
    
    elif args.source == "file":
        if not args.file:
            print("❌ Error: --file argument required for file source")
            return
        logs = LogStreamReader.read_from_file(args.file)
    
    elif args.source == "kubectl":
        if not args.pod:
            print("❌ Error: --pod argument required for kubectl source")
            return
        print(f"📦 Fetching logs from pod: {args.pod} (namespace: {args.namespace})")
        logs = LogStreamReader.read_from_kubectl_logs(args.pod, args.namespace)
    
    if not logs:
        print("❌ No logs found")
        return
    
    print(f"✅ Loaded {len(logs)} log lines")
    
    # Process logs
    print(f"\n⚙️  Processing logs...\n")
    stats = log_parser.process_log_stream(logs, auto_dump=True)
    
    # Dump any remaining logs
    if log_parser.current_chunk.stats["total_logs"] > 0:
        print(f"\n📦 Dumping final chunk...")
        log_parser.dump_chunk()
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 PROCESSING SUMMARY")
    print("=" * 60)
    print(f"Total logs processed:  {stats['total_processed']}")
    print(f"  ├─ Health issues:    {stats['health']}")
    print(f"  ├─ Anomalies:        {stats['anomaly']}")
    print(f"  ├─ Service errors:   {stats['service']}")
    print(f"  ├─ Security issues:  {stats['security']}")
    print(f"  └─ Ignored/Unknown:  {stats['ignored'] + stats['unknown']}")
    print(f"\nChunks dumped:         {stats['chunks_dumped'] + (1 if log_parser.current_chunk.stats['total_logs'] == 0 else 1)}")
    
    # Get MongoDB statistics if available
    if mongodb and mongodb.connected:
        print("\n" + "=" * 60)
        print("📈 MONGODB STATISTICS")
        print("=" * 60)
        
        mongo_stats = mongodb.get_statistics()
        if mongo_stats:
            print(f"Total chunks stored:   {mongo_stats.get('total_chunks', 0)}")
            print(f"Total logs stored:     {mongo_stats.get('total_logs', 0)}")
            print(f"  ├─ Health:          {mongo_stats.get('total_health', 0)}")
            print(f"  ├─ Anomaly:         {mongo_stats.get('total_anomaly', 0)}")
            print(f"  ├─ Service:         {mongo_stats.get('total_service', 0)}")
            print(f"  ├─ Security:        {mongo_stats.get('total_security', 0)}")
            print(f"  └─ Ignored:         {mongo_stats.get('total_ignored', 0)}")
        
        mongodb.disconnect()
    
    print("\n" + "=" * 60)
    print("✅ Log processing completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
