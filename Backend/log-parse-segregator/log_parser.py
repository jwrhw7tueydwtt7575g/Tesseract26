"""
Log Parser - Reads logs from streams and chunks them with categorization
"""

import sys
import json
from datetime import datetime
from typing import Optional, Dict, List
from categorizer import LogCategorizer, LogChunk
from mongodb_handler import MongoDBHandler


class LogParser:
    """Parse and process log streams"""
    
    def __init__(self, max_logs_per_chunk: int = 20, 
                 mongodb_handler: Optional[MongoDBHandler] = None):
        """
        Initialize log parser
        
        Args:
            max_logs_per_chunk: Maximum logs per chunk before dumping (default: 20)
            mongodb_handler: MongoDB handler instance
        """
        self.categorizer = LogCategorizer()
        self.max_logs_per_chunk = max_logs_per_chunk
        self.mongodb = mongodb_handler
        self.current_chunk = LogChunk()
        self.processed_logs = 0
        self.dumped_chunks = 0
    
    def parse_log_line(self, log_line: str) -> Dict:
        """
        Parse a single log line and categorize it
        
        Args:
            log_line: Raw log line from stream
        
        Returns:
            dict: Structured log entry with category and keywords
        """
        # Clean the log line
        log_line = log_line.strip()
        if not log_line:
            return None
        
        # Categorize
        category = self.categorizer.categorize_log(log_line)
        
        # Extract matching keywords
        keywords = self.categorizer.extract_keywords(log_line, category) if category != "IGNORED" else []
        
        # Create structured log entry
        log_entry = {
            "timestamp": datetime.utcnow(),
            "raw_message": log_line,
            "category": category,
            "keywords": keywords,
            "line_length": len(log_line)
        }
        
        return log_entry
    
    def process_log_stream(self, log_lines: List[str], 
                          auto_dump: bool = True) -> Dict:
        """
        Process multiple log lines from a stream
        
        Args:
            log_lines: List of log lines
            auto_dump: Whether to auto-dump chunks when full
        
        Returns:
            dict: Processing statistics
        """
        stats = {
            "total_processed": 0,
            "health": 0,
            "anomaly": 0,
            "service": 0,
            "security": 0,
            "ignored": 0,
            "unknown": 0,
            "chunks_dumped": 0
        }
        
        for log_line in log_lines:
            log_entry = self.parse_log_line(log_line)
            if not log_entry:
                continue
            
            # Add to current chunk
            self.current_chunk.add_log(log_entry)
            self.processed_logs += 1
            stats["total_processed"] += 1
            
            # Update category counts
            category = log_entry["category"]
            if category in stats:
                stats[category.lower()] += 1
            
            # Dump chunk if full
            if auto_dump and self.current_chunk.is_full(self.max_logs_per_chunk):
                self.dump_chunk()
                stats["chunks_dumped"] += 1
        
        return stats
    
    def dump_chunk(self) -> Optional[str]:
        """
        Dump current chunk to MongoDB
        
        Returns:
            str: Chunk ID if successful, None otherwise
        """
        if self.current_chunk.stats["total_logs"] == 0:
            return None
        
        chunk_data = self.current_chunk.to_dict()
        
        # Insert to MongoDB if connected
        if self.mongodb and self.mongodb.connected:
            chunk_id = self.mongodb.insert_chunk(chunk_data)
        else:
            chunk_id = chunk_data["chunk_id"]
            print(f"⚠️  MongoDB not available, logging locally: {chunk_id}")
        
        # Print chunk summary
        print(f"\n📦 {self.current_chunk}")
        
        # Reset chunk
        self.dumped_chunks += 1
        self.current_chunk = LogChunk()
        
        return chunk_id
    
    def get_statistics(self) -> Dict:
        """Get parser statistics"""
        return {
            "total_logs_processed": self.processed_logs,
            "chunks_dumped": self.dumped_chunks,
            "current_chunk_logs": self.current_chunk.stats["total_logs"],
            "current_chunk": self.current_chunk.chunk_id
        }
    
    def __repr__(self) -> str:
        """String representation"""
        return (
            f"LogParser(processed={self.processed_logs}, "
            f"dumped_chunks={self.dumped_chunks}, "
            f"current_chunk={self.current_chunk.stats['total_logs']} logs)"
        )


class LogStreamReader:
    """Read logs from various sources"""
    
    @staticmethod
    def read_from_stdin() -> List[str]:
        """Read logs from stdin (for piping)"""
        logs = []
        try:
            for line in sys.stdin:
                logs.append(line.rstrip('\n'))
        except KeyboardInterrupt:
            print("\n⏹️  Stream reading interrupted")
        return logs
    
    @staticmethod
    def read_from_file(filepath: str) -> List[str]:
        """Read logs from a file"""
        try:
            with open(filepath, 'r') as f:
                return f.readlines()
        except FileNotFoundError:
            print(f"❌ File not found: {filepath}")
            return []
        except Exception as e:
            print(f"❌ Error reading file: {e}")
            return []
    
    @staticmethod
    def read_from_kubectl_logs(pod_name: str, namespace: str = "default") -> List[str]:
        """Read logs from Kubernetes pod"""
        import subprocess
        
        try:
            cmd = f"kubectl logs -n {namespace} {pod_name} --all-containers=true"
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                print(f"❌ Error getting pod logs: {result.stderr}")
                return []
            
            return result.stdout.splitlines()
        except Exception as e:
            print(f"❌ Error: {e}")
            return []
