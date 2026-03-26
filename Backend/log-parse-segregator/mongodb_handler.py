"""
MongoDB handler for storing categorized logs
"""

from typing import Dict, Optional, List
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from config import MONGODB_URI, MONGODB_DB, MONGODB_COLLECTION


class MongoDBHandler:
    """Handle MongoDB operations for log storage"""
    
    def __init__(self, uri: str = MONGODB_URI, db_name: str = MONGODB_DB, 
                 collection_name: str = MONGODB_COLLECTION, timeout: int = 5):
        """
        Initialize MongoDB connection
        
        Args:
            uri: MongoDB connection URI
            db_name: Database name
            collection_name: Collection name
            timeout: Connection timeout in seconds
        """
        self.uri = uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.client = None
        self.db = None
        self.collection = None
        self.timeout = timeout
        self.connected = False
    
    def connect(self) -> bool:
        """
        Connect to MongoDB
        
        Returns:
            bool: True if connection successful, False otherwise
        """
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=self.timeout*1000)
            # Verify connection
            self.client.admin.command('ping')
            
            self.db = self.client[self.db_name]
            self.collection = self.db[self.collection_name]
            
            # Create indexes for better query performance
            self._create_indexes()
            
            self.connected = True
            print(f"✅ Connected to MongoDB: {self.db_name}.{self.collection_name}")
            return True
        
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"❌ Failed to connect to MongoDB: {e}")
            self.connected = False
            return False
    
    def disconnect(self) -> None:
        """Disconnect from MongoDB"""
        if self.client:
            self.client.close()
            self.connected = False
            print("✅ Disconnected from MongoDB")
    
    def _create_indexes(self) -> None:
        """Create indexes for better query performance"""
        try:
            # Index on chunk_id for quick lookups
            self.collection.create_index("chunk_id")
            # Index on timestamp for time-based queries
            self.collection.create_index("timestamp")
            # Index on categories for aggregations
            self.collection.create_index("stats.health_count")
            self.collection.create_index("stats.anomaly_count")
            self.collection.create_index("stats.service_count")
            self.collection.create_index("stats.security_count")
        except Exception as e:
            print(f"⚠️  Warning: Could not create indexes: {e}")
    
    def insert_chunk(self, chunk_data: Dict) -> Optional[str]:
        """
        Insert a log chunk into MongoDB
        
        Args:
            chunk_data: Dictionary containing chunk data
        
        Returns:
            str: Inserted document ID, or None if failed
        """
        if not self.connected:
            print("❌ Not connected to MongoDB")
            return None
        
        try:
            result = self.collection.insert_one(chunk_data)
            print(f"✅ Inserted chunk: {chunk_data['chunk_id']} (ID: {result.inserted_id})")
            return str(result.inserted_id)
        
        except Exception as e:
            print(f"❌ Error inserting chunk: {e}")
            return None
    
    def find_chunk(self, chunk_id: str) -> Optional[Dict]:
        """
        Find a chunk by ID
        
        Args:
            chunk_id: Chunk ID to search for
        
        Returns:
            dict: Chunk data or None if not found
        """
        if not self.connected:
            return None
        
        try:
            return self.collection.find_one({"chunk_id": chunk_id})
        except Exception as e:
            print(f"❌ Error finding chunk: {e}")
            return None
    
    def get_chunks_by_category(self, category: str, limit: int = 10) -> List[Dict]:
        """
        Get chunks filtered by a category count > 0
        
        Args:
            category: Category name (HEALTH, ANOMALY, SERVICE, SECURITY)
            limit: Maximum number of results
        
        Returns:
            list: List of matching chunks
        """
        if not self.connected:
            return []
        
        try:
            query = {f"stats.{category.lower()}_count": {"$gt": 0}}
            results = list(self.collection.find(query).limit(limit).sort("timestamp", -1))
            return results
        except Exception as e:
            print(f"❌ Error querying chunks: {e}")
            return []
    
    def get_statistics(self) -> Optional[Dict]:
        """
        Get aggregate statistics from all chunks
        
        Returns:
            dict: Statistics or None if failed
        """
        if not self.connected:
            return None
        
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "total_chunks": {"$sum": 1},
                        "total_logs": {"$sum": "$stats.total_logs"},
                        "total_health": {"$sum": "$stats.health_count"},
                        "total_anomaly": {"$sum": "$stats.anomaly_count"},
                        "total_service": {"$sum": "$stats.service_count"},
                        "total_security": {"$sum": "$stats.security_count"},
                        "total_ignored": {"$sum": "$stats.ignored_count"},
                    }
                }
            ]
            result = list(self.collection.aggregate(pipeline))
            return result[0] if result else None
        except Exception as e:
            print(f"❌ Error getting statistics: {e}")
            return None
    
    def delete_chunk(self, chunk_id: str) -> bool:
        """
        Delete a chunk by ID
        
        Args:
            chunk_id: Chunk ID to delete
        
        Returns:
            bool: True if deletion successful
        """
        if not self.connected:
            return False
        
        try:
            result = self.collection.delete_one({"chunk_id": chunk_id})
            if result.deleted_count > 0:
                print(f"✅ Deleted chunk: {chunk_id}")
                return True
            else:
                print(f"⚠️  Chunk not found: {chunk_id}")
                return False
        except Exception as e:
            print(f"❌ Error deleting chunk: {e}")
            return False
    
    def export_chunk_to_json(self, chunk_id: str, filepath: str) -> bool:
        """
        Export a chunk to JSON file
        
        Args:
            chunk_id: Chunk ID to export
            filepath: Path to save JSON file
        
        Returns:
            bool: True if export successful
        """
        import json
        
        chunk = self.find_chunk(chunk_id)
        if not chunk:
            print(f"❌ Chunk not found: {chunk_id}")
            return False
        
        try:
            # Convert ObjectId to string for JSON serialization
            chunk['_id'] = str(chunk.get('_id', ''))
            chunk['timestamp'] = chunk['timestamp'].isoformat()
            
            with open(filepath, 'w') as f:
                json.dump(chunk, f, indent=2, default=str)
            
            print(f"✅ Exported chunk to: {filepath}")
            return True
        except Exception as e:
            print(f"❌ Error exporting chunk: {e}")
            return False
