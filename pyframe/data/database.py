"""
Database Management

Handles database connections, query execution, and automatic
schema management for PyFrame models.
"""

import sqlite3
import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union
from pathlib import Path

from .models import Model, ModelRegistry


class DatabaseConnection:
    """Database connection wrapper with query execution"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.connection = None
        self._dialect = self._parse_dialect(database_url)
        
    def _parse_dialect(self, url: str) -> str:
        """Parse database dialect from URL"""
        if url.startswith('sqlite'):
            return 'sqlite'
        elif url.startswith('postgresql'):
            return 'postgresql'
        elif url.startswith('mysql'):
            return 'mysql'
        else:
            return 'sqlite'  # Default fallback
            
    def connect(self) -> None:
        """Establish database connection"""
        if self._dialect == 'sqlite':
            # Extract path from sqlite:///path
            db_path = self.database_url.replace('sqlite:///', '')
            self.connection = sqlite3.connect(db_path)
            self.connection.row_factory = sqlite3.Row  # Enable dict-like access
        else:
            # For other databases, you'd use appropriate drivers
            raise NotImplementedError(f"Database dialect '{self._dialect}' not yet implemented")
            
    def disconnect(self) -> None:
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            
    def execute(self, query: str, params: tuple = None) -> sqlite3.Cursor:
        """Execute a SQL query"""
        if not self.connection:
            self.connect()
            
        cursor = self.connection.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
            
        return cursor
        
    def execute_many(self, query: str, params_list: List[tuple]) -> sqlite3.Cursor:
        """Execute a SQL query with multiple parameter sets"""
        if not self.connection:
            self.connect()
            
        cursor = self.connection.cursor()
        cursor.executemany(query, params_list)
        return cursor
        
    def commit(self) -> None:
        """Commit current transaction"""
        if self.connection:
            self.connection.commit()
            
    def rollback(self) -> None:
        """Rollback current transaction"""
        if self.connection:
            self.connection.rollback()
            
    def get_dialect(self) -> str:
        """Get database dialect"""
        return self._dialect
        
    def __enter__(self):
        self.connect()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        else:
            self.commit()
        self.disconnect()


class Database:
    """Database interface for model operations"""
    
    def __init__(self, connection: DatabaseConnection):
        self.connection = connection
        self.dialect = connection.get_dialect()
        
    def create_table(self, model_class: Type[Model]) -> None:
        """Create database table for a model"""
        table_name = model_class.get_table_name()
        
        columns = []
        for field_name, field_obj in model_class._fields.items():
            column_def = f"{field_name} {field_obj.to_database_type(self.dialect)}"
            
            # Add constraints
            if field_obj.constraints.unique:
                column_def += " UNIQUE"
            if field_obj.constraints.required and field_obj.constraints.default is None:
                column_def += " NOT NULL"
            if field_name == 'id':
                column_def += " PRIMARY KEY"
                
            columns.append(column_def)
            
        # Add foreign key constraints
        foreign_keys = []
        for field_name, field_obj in model_class._fields.items():
            if field_obj.constraints.foreign_key:
                ref_model = ModelRegistry.get_model(field_obj.constraints.foreign_key)
                if ref_model:
                    ref_table = ref_model.get_table_name()
                    foreign_keys.append(f"FOREIGN KEY ({field_name}) REFERENCES {ref_table}(id)")
                    
        all_constraints = columns + foreign_keys
        
        query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {', '.join(all_constraints)}
        )
        """
        
        self.connection.execute(query)
        self.connection.commit()
        
    def drop_table(self, model_class: Type[Model]) -> None:
        """Drop database table for a model"""
        table_name = model_class.get_table_name()
        query = f"DROP TABLE IF EXISTS {table_name}"
        self.connection.execute(query)
        self.connection.commit()
        
    def insert(self, instance: Model) -> Model:
        """Insert a new model instance"""
        table_name = instance.get_table_name()
        
        # Prepare data
        data = {}
        for field_name, field_obj in instance._fields.items():
            value = getattr(instance, field_name, None)
            
            # Handle special field types
            if value is not None:
                if field_obj.field_type.value in ['json']:
                    value = json.dumps(value)
                elif field_obj.field_type.value in ['uuid']:
                    value = str(value)
                elif field_obj.field_type.value in ['datetime']:
                    value = value.isoformat()
                    
            data[field_name] = value
            
        # Build query
        columns = ', '.join(data.keys())
        placeholders = ', '.join(['?' for _ in data])
        values = tuple(data.values())
        
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
        
        cursor = self.connection.execute(query, values)
        self.connection.commit()
        
        return instance
        
    def update(self, instance: Model) -> Model:
        """Update an existing model instance"""
        table_name = instance.get_table_name()
        
        # Prepare data (exclude id from updates)
        data = {}
        for field_name, field_obj in instance._fields.items():
            if field_name != 'id':  # Don't update primary key
                value = getattr(instance, field_name, None)
                
                # Handle special field types
                if value is not None:
                    if field_obj.field_type.value in ['json']:
                        value = json.dumps(value)
                    elif field_obj.field_type.value in ['uuid']:
                        value = str(value)
                    elif field_obj.field_type.value in ['datetime']:
                        value = value.isoformat()
                        
                data[field_name] = value
                
        # Build query
        set_clauses = [f"{col} = ?" for col in data.keys()]
        values = list(data.values())
        values.append(str(instance.id))  # Add id for WHERE clause
        
        query = f"UPDATE {table_name} SET {', '.join(set_clauses)} WHERE id = ?"
        
        self.connection.execute(query, tuple(values))
        self.connection.commit()
        
        return instance
        
    def delete(self, instance: Model) -> None:
        """Delete a model instance"""
        table_name = instance.get_table_name()
        query = f"DELETE FROM {table_name} WHERE id = ?"
        
        self.connection.execute(query, (str(instance.id),))
        self.connection.commit()
        
    def get(self, model_class: Type[Model], **filters) -> Optional[Model]:
        """Get a single instance by filters"""
        results = self.filter(model_class, limit=1, **filters)
        return results[0] if results else None
        
    def filter(self, model_class: Type[Model], limit: Optional[int] = None, 
               offset: Optional[int] = None, order_by: Optional[str] = None, 
               **filters) -> List[Model]:
        """Get multiple instances by filters"""
        table_name = model_class.get_table_name()
        
        # Build WHERE clause
        where_clauses = []
        params = []
        
        for field_name, value in filters.items():
            if value is not None:
                where_clauses.append(f"{field_name} = ?")
                
                # Handle special types
                field_obj = model_class._fields.get(field_name)
                if field_obj and field_obj.field_type.value in ['uuid']:
                    value = str(value)
                elif field_obj and field_obj.field_type.value in ['datetime']:
                    if isinstance(value, datetime):
                        value = value.isoformat()
                        
                params.append(value)
            else:
                where_clauses.append(f"{field_name} IS NULL")
                
        # Build query
        query = f"SELECT * FROM {table_name}"
        
        if where_clauses:
            query += f" WHERE {' AND '.join(where_clauses)}"
            
        if order_by:
            query += f" ORDER BY {order_by}"
            
        if limit:
            query += f" LIMIT {limit}"
            
        if offset:
            query += f" OFFSET {offset}"
            
        # Execute query
        cursor = self.connection.execute(query, tuple(params))
        rows = cursor.fetchall()
        
        # Convert rows to model instances
        instances = []
        for row in rows:
            data = dict(row)
            
            # Convert special types back
            for field_name, field_obj in model_class._fields.items():
                if field_name in data and data[field_name] is not None:
                    if field_obj.field_type.value == 'json':
                        data[field_name] = json.loads(data[field_name])
                    elif field_obj.field_type.value == 'uuid':
                        data[field_name] = uuid.UUID(data[field_name])
                    elif field_obj.field_type.value == 'datetime':
                        data[field_name] = datetime.fromisoformat(data[field_name])
                        
            instances.append(model_class(**data))
            
        return instances
        
    def all(self, model_class: Type[Model]) -> List[Model]:
        """Get all instances of a model"""
        return self.filter(model_class)
        
    def count(self, model_class: Type[Model], **filters) -> int:
        """Count instances matching filters"""
        table_name = model_class.get_table_name()
        
        # Build WHERE clause
        where_clauses = []
        params = []
        
        for field_name, value in filters.items():
            if value is not None:
                where_clauses.append(f"{field_name} = ?")
                params.append(str(value) if isinstance(value, uuid.UUID) else value)
            else:
                where_clauses.append(f"{field_name} IS NULL")
                
        # Build query
        query = f"SELECT COUNT(*) FROM {table_name}"
        
        if where_clauses:
            query += f" WHERE {' AND '.join(where_clauses)}"
            
        cursor = self.connection.execute(query, tuple(params))
        return cursor.fetchone()[0]
        
    def execute_raw(self, query: str, params: tuple = None) -> sqlite3.Cursor:
        """Execute raw SQL query"""
        return self.connection.execute(query, params)


class DatabaseManager:
    """Global database manager singleton"""
    
    _instance: Optional['DatabaseManager'] = None
    _database: Optional[Database] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
        
    @classmethod
    def initialize(cls, database_url: str) -> None:
        """Initialize the database manager"""
        connection = DatabaseConnection(database_url)
        cls._database = Database(connection)
        
    @classmethod
    def get_database(cls) -> Database:
        """Get the database instance"""
        if cls._database is None:
            # Default to in-memory SQLite for development
            cls.initialize("sqlite:///:memory:")
        return cls._database
        
    @classmethod
    def create_all_tables(cls) -> None:
        """Create tables for all registered models"""
        db = cls.get_database()
        
        for model_class in ModelRegistry.get_all_models().values():
            db.create_table(model_class)
            
    @classmethod
    def drop_all_tables(cls) -> None:
        """Drop all tables"""
        db = cls.get_database()
        
        for model_class in ModelRegistry.get_all_models().values():
            db.drop_table(model_class)
            
    @classmethod
    def save(cls, instance: Model) -> Model:
        """Save a model instance"""
        db = cls.get_database()
        
        # Check if instance exists (has been saved before)
        if hasattr(instance, 'id') and instance.id:
            existing = db.get(instance.__class__, id=instance.id)
            if existing:
                return db.update(instance)
                
        return db.insert(instance)
        
    @classmethod
    def delete(cls, instance: Model) -> None:
        """Delete a model instance"""
        db = cls.get_database()
        db.delete(instance)
        
    @classmethod
    def get(cls, model_class: Type[Model], **filters) -> Optional[Model]:
        """Get a single instance"""
        db = cls.get_database()
        return db.get(model_class, **filters)
        
    @classmethod
    def filter(cls, model_class: Type[Model], **kwargs) -> List[Model]:
        """Filter instances"""
        db = cls.get_database()
        return db.filter(model_class, **kwargs)
        
    @classmethod
    def all(cls, model_class: Type[Model]) -> List[Model]:
        """Get all instances"""
        db = cls.get_database()
        return db.all(model_class)
        
    @classmethod
    def count(cls, model_class: Type[Model], **filters) -> int:
        """Count instances"""
        db = cls.get_database()
        return db.count(model_class, **filters)
