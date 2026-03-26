"""
Log Categorizer - Segregates logs into different categories using regex patterns
"""

import re
from datetime import datetime
from typing import Dict, List, Tuple
from config import LOG_CATEGORIES, IGNORED_PATTERNS


class LogCategorizer:
    """Categorize logs based on regex patterns"""
    
    def __init__(self):
        """Initialize categorizer with compiled regex patterns"""
        self.categories = LOG_CATEGORIES
        self.ignored_patterns = IGNORED_PATTERNS
        
        # Compile all regex patterns for performance
        self.compiled_categories = {}
        for category, config in self.categories.items():
            self.compiled_categories[category] = [
                re.compile(pattern, re.IGNORECASE)
                for pattern in config["keywords"]
            ]
        
        self.compiled_ignored = [
            re.compile(pattern, re.IGNORECASE)
            for pattern in self.ignored_patterns
        ]
    
    def is_ignored(self, log_message: str) -> bool:
        """Check if log matches ignored patterns"""
        for pattern in self.compiled_ignored:
            if pattern.search(log_message):
                return True
        return False
    
    def categorize_log(self, log_message: str) -> str:
        """
        Categorize a single log message
        
        Returns:
            - Category name (HEALTH, ANOMALY, SERVICE, SECURITY)
            - 'IGNORED' if matches ignored patterns
            - 'UNKNOWN' if no matches found
        """
        # Check ignored patterns first
        if self.is_ignored(log_message):
            return "IGNORED"
        
        # Check each category
        for category, patterns in self.compiled_categories.items():
            for pattern in patterns:
                if pattern.search(log_message):
                    return category
        
        return "UNKNOWN"
    
    def extract_keywords(self, log_message: str, category: str) -> List[str]:
        """Extract matching keywords from a log message for a given category"""
        matching_keywords = []
        
        if category not in self.compiled_categories:
            return matching_keywords
        
        for pattern in self.compiled_categories[category]:
            if pattern.search(log_message):
                matching_keywords.append(pattern.pattern)
        
        return matching_keywords


class LogChunk:
    """Represents a chunk of logs (20 consecutive logs from stream)"""
    
    def __init__(self, chunk_id: str = None):
        """Initialize a log chunk"""
        self.chunk_id = chunk_id or self._generate_chunk_id()
        self.timestamp = datetime.utcnow()
        self.logs = []  # Sequential list of categorized logs
        self.stats = {
            "total_logs": 0,
            "health_count": 0,
            "anomaly_count": 0,
            "service_count": 0,
            "security_count": 0,
            "ignored_count": 0,
            "unknown_count": 0
        }
    
    def _generate_chunk_id(self) -> str:
        """Generate unique chunk ID"""
        return f"chunk_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}"
    
    def add_log(self, log_entry: Dict) -> None:
        """Add a log entry to the chunk (in sequence)"""
        category = log_entry.get("category", "UNKNOWN")
        
        # Add to sequential logs list
        self.logs.append(log_entry)
        
        # Update stats
        self.stats["total_logs"] += 1
        if category in self.stats:
            self.stats[f"{category.lower()}_count"] += 1
    
    def is_full(self, max_logs: int = 20) -> bool:
        """Check if chunk has reached max logs (default 20)"""
        return len(self.logs) >= max_logs
    
    def to_dict(self) -> Dict:
        """Convert chunk to dictionary for MongoDB storage"""
        return {
            "chunk_id": self.chunk_id,
            "timestamp": self.timestamp,
            "logs": self.logs,
            "stats": self.stats
        }
    
    def __repr__(self) -> str:
        """String representation"""
        return (
            f"LogChunk(id={self.chunk_id}, total={self.stats['total_logs']}, "
            f"health={self.stats['health_count']}, "
            f"anomaly={self.stats['anomaly_count']}, "
            f"service={self.stats['service_count']}, "
            f"security={self.stats['security_count']})"
        )
