"""
Database connection management for JobSite
Handles SQLite connections, connection pooling, and transaction management
"""

import sqlite3
import threading
from contextlib import contextmanager
from pathlib import Path
from typing import Optional, Any, Dict, List
import logging

from .models import DatabaseSchema


class DatabaseConnection:
    """Thread-safe SQLite database connection manager"""
    
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._local = threading.local()
        self._lock = threading.Lock()
        self.logger = logging.getLogger(__name__)
        
    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection"""
        if not hasattr(self._local, 'connection'):
            self._local.connection = sqlite3.connect(
                str(self.db_path),
                check_same_thread=False,
                timeout=30.0
            )
            
            # Configure connection
            self._local.connection.row_factory = sqlite3.Row
            self._local.connection.execute("PRAGMA foreign_keys = ON")
            self._local.connection.execute("PRAGMA journal_mode = WAL")
            self._local.connection.execute("PRAGMA synchronous = NORMAL")
            self._local.connection.execute("PRAGMA cache_size = -64000")  # 64MB cache
            
        return self._local.connection
    
    @contextmanager
    def get_cursor(self, transaction: bool = False):
        """Get database cursor with optional transaction management"""
        connection = self._get_connection()
        cursor = connection.cursor()
        
        try:
            if transaction:
                cursor.execute("BEGIN")
            
            yield cursor
            
            if transaction:
                connection.commit()
                
        except Exception as e:
            if transaction:
                connection.rollback()
                self.logger.error(f"Database transaction rolled back: {e}")
            raise
        finally:
            cursor.close()
    
    def execute_script(self, script: str) -> None:
        """Execute SQL script (multiple statements)"""
        with self._lock:
            connection = self._get_connection()
            try:
                connection.executescript(script)
                connection.commit()
            except Exception as e:
                connection.rollback()
                self.logger.error(f"Failed to execute script: {e}")
                raise
    
    def execute_many(self, query: str, params_list: List[tuple]) -> None:
        """Execute query with multiple parameter sets"""
        with self.get_cursor(transaction=True) as cursor:
            cursor.executemany(query, params_list)
    
    def fetchone(self, query: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        """Execute query and fetch one result"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchone()
    
    def fetchall(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute query and fetch all results"""
        with self.get_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute query and return cursor"""
        with self.get_cursor(transaction=True) as cursor:
            cursor.execute(query, params)
            return cursor
    
    def get_last_insert_id(self) -> int:
        """Get the last inserted row ID"""
        connection = self._get_connection()
        return connection.lastrowid
    
    def close(self):
        """Close database connection"""
        if hasattr(self._local, 'connection'):
            self._local.connection.close()
            del self._local.connection
    
    def initialize_database(self) -> None:
        """Initialize database schema"""
        self.logger.info(f"Initializing database at {self.db_path}")
        
        try:
            # Create tables, indexes, and triggers
            statements = DatabaseSchema.get_all_statements()
            
            with self.get_cursor(transaction=True) as cursor:
                for statement in statements:
                    cursor.execute(statement)
            
            self.logger.info("Database schema initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information and statistics"""
        info = {
            "database_path": str(self.db_path),
            "database_exists": self.db_path.exists(),
            "database_size": 0,
            "tables": {},
            "indexes": []
        }
        
        if self.db_path.exists():
            info["database_size"] = self.db_path.stat().st_size
            
            # Get table information
            tables = self.fetchall(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
            
            for table in tables:
                table_name = table[0]
                count_result = self.fetchone(f"SELECT COUNT(*) as count FROM {table_name}")
                info["tables"][table_name] = count_result[0] if count_result else 0
            
            # Get index information
            indexes = self.fetchall(
                "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
            )
            info["indexes"] = [idx[0] for idx in indexes]
        
        return info
    
    def vacuum(self) -> None:
        """Vacuum database to reclaim space and optimize"""
        with self._lock:
            connection = self._get_connection()
            connection.execute("VACUUM")
            connection.commit()
            self.logger.info("Database vacuumed successfully")
    
    def analyze(self) -> None:
        """Analyze database to update query planner statistics"""
        with self._lock:
            connection = self._get_connection()
            connection.execute("ANALYZE")
            connection.commit()
            self.logger.info("Database analyzed successfully")
    
    def backup(self, backup_path: Path) -> None:
        """Create database backup"""
        backup_path = Path(backup_path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self._lock:
            source = self._get_connection()
            backup = sqlite3.connect(str(backup_path))
            
            try:
                source.backup(backup)
                self.logger.info(f"Database backed up to {backup_path}")
            finally:
                backup.close()


class DatabaseConnectionPool:
    """Simple connection pool for multiple database operations"""
    
    def __init__(self, db_path: Path, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self._connections: List[DatabaseConnection] = []
        self._available: List[bool] = []
        self._lock = threading.Lock()
        
        # Initialize pool
        for _ in range(pool_size):
            conn = DatabaseConnection(db_path)
            self._connections.append(conn)
            self._available.append(True)
    
    @contextmanager
    def get_connection(self):
        """Get connection from pool"""
        connection = None
        index = -1
        
        with self._lock:
            for i, available in enumerate(self._available):
                if available:
                    self._available[i] = False
                    connection = self._connections[i]
                    index = i
                    break
        
        if connection is None:
            # Pool exhausted, create temporary connection
            connection = DatabaseConnection(self.db_path)
            index = -1
        
        try:
            yield connection
        finally:
            if index >= 0:
                with self._lock:
                    self._available[index] = True
            else:
                connection.close()
    
    def close_all(self):
        """Close all connections in pool"""
        with self._lock:
            for conn in self._connections:
                conn.close()
            self._connections.clear()
            self._available.clear()