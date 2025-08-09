"""
Database Migration System

Automatically generates and applies database migrations based on
model changes, with rollback support and version control.
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Type
from pathlib import Path
from dataclasses import dataclass

from .models import Model, ModelRegistry, Field, FieldType
from .database import DatabaseManager, Database


@dataclass
class MigrationOperation:
    """Represents a single migration operation"""
    operation_type: str  # 'create_table', 'drop_table', 'add_column', 'drop_column', 'alter_column'
    model_name: str
    table_name: str
    details: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "operation_type": self.operation_type,
            "model_name": self.model_name,
            "table_name": self.table_name,
            "details": self.details
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MigrationOperation':
        return cls(
            operation_type=data["operation_type"],
            model_name=data["model_name"],
            table_name=data["table_name"],
            details=data["details"]
        )


@dataclass
class Migration:
    """Represents a complete migration with multiple operations"""
    version: str
    name: str
    operations: List[MigrationOperation]
    dependencies: List[str]
    created_at: datetime
    applied_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "name": self.name,
            "operations": [op.to_dict() for op in self.operations],
            "dependencies": self.dependencies,
            "created_at": self.created_at.isoformat(),
            "applied_at": self.applied_at.isoformat() if self.applied_at else None
        }
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Migration':
        return cls(
            version=data["version"],
            name=data["name"],
            operations=[MigrationOperation.from_dict(op) for op in data["operations"]],
            dependencies=data["dependencies"],
            created_at=datetime.fromisoformat(data["created_at"]),
            applied_at=datetime.fromisoformat(data["applied_at"]) if data["applied_at"] else None
        )
        
    def get_sql_forward(self, dialect: str = "sqlite") -> List[str]:
        """Generate forward SQL statements for this migration"""
        sql_statements = []
        
        for operation in self.operations:
            statements = self._operation_to_sql(operation, dialect, forward=True)
            sql_statements.extend(statements)
            
        return sql_statements
        
    def get_sql_backward(self, dialect: str = "sqlite") -> List[str]:
        """Generate backward (rollback) SQL statements for this migration"""
        sql_statements = []
        
        # Reverse the order of operations for rollback
        for operation in reversed(self.operations):
            statements = self._operation_to_sql(operation, dialect, forward=False)
            sql_statements.extend(statements)
            
        return sql_statements
        
    def _operation_to_sql(self, operation: MigrationOperation, dialect: str, forward: bool) -> List[str]:
        """Convert an operation to SQL statements"""
        
        if operation.operation_type == "create_table":
            if forward:
                return self._create_table_sql(operation, dialect)
            else:
                return [f"DROP TABLE IF EXISTS {operation.table_name}"]
                
        elif operation.operation_type == "drop_table":
            if forward:
                return [f"DROP TABLE IF EXISTS {operation.table_name}"]
            else:
                return self._create_table_sql(operation, dialect)
                
        elif operation.operation_type == "add_column":
            if forward:
                column_def = operation.details["column_definition"]
                return [f"ALTER TABLE {operation.table_name} ADD COLUMN {column_def}"]
            else:
                # SQLite doesn't support DROP COLUMN directly
                if dialect == "sqlite":
                    return [f"-- Cannot rollback ADD COLUMN on SQLite: {operation.details['column_name']}"]
                else:
                    column_name = operation.details["column_name"]
                    return [f"ALTER TABLE {operation.table_name} DROP COLUMN {column_name}"]
                    
        elif operation.operation_type == "drop_column":
            if forward:
                if dialect == "sqlite":
                    return [f"-- Cannot DROP COLUMN on SQLite: {operation.details['column_name']}"]
                else:
                    column_name = operation.details["column_name"]
                    return [f"ALTER TABLE {operation.table_name} DROP COLUMN {column_name}"]
            else:
                column_def = operation.details["column_definition"]
                return [f"ALTER TABLE {operation.table_name} ADD COLUMN {column_def}"]
                
        elif operation.operation_type == "alter_column":
            # Column alterations are complex and dialect-specific
            return [f"-- Column alteration not yet implemented: {operation.details}"]
            
        return []
        
    def _create_table_sql(self, operation: MigrationOperation, dialect: str) -> List[str]:
        """Generate CREATE TABLE SQL"""
        table_name = operation.table_name
        columns = operation.details["columns"]
        foreign_keys = operation.details.get("foreign_keys", [])
        
        all_constraints = columns + foreign_keys
        
        sql = f"""
        CREATE TABLE {table_name} (
            {', '.join(all_constraints)}
        )
        """
        
        return [sql]


class MigrationManager:
    """Manages database migrations for PyFrame applications"""
    
    def __init__(self, migrations_dir: str = "migrations"):
        self.migrations_dir = Path(migrations_dir)
        self.migrations_dir.mkdir(exist_ok=True)
        self._migrations: Dict[str, Migration] = {}
        self._load_migrations()
        
    def _load_migrations(self) -> None:
        """Load existing migrations from files"""
        for migration_file in self.migrations_dir.glob("*.json"):
            with open(migration_file, 'r') as f:
                data = json.load(f)
                migration = Migration.from_dict(data)
                self._migrations[migration.version] = migration
                
    def _save_migration(self, migration: Migration) -> None:
        """Save migration to file"""
        filename = f"{migration.version}_{migration.name.replace(' ', '_').lower()}.json"
        filepath = self.migrations_dir / filename
        
        with open(filepath, 'w') as f:
            json.dump(migration.to_dict(), f, indent=2)
            
        self._migrations[migration.version] = migration
        
    def generate_migration(self, name: str) -> Optional[Migration]:
        """Generate a new migration based on model changes"""
        
        # Get current schema state
        current_schema = self._get_current_schema()
        
        # Get target schema from models
        target_schema = self._get_target_schema()
        
        # Compare schemas and generate operations
        operations = self._compare_schemas(current_schema, target_schema)
        
        if not operations:
            print("No changes detected")
            return None
            
        # Generate migration version
        version = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Get dependencies (latest migration)
        dependencies = [max(self._migrations.keys())] if self._migrations else []
        
        migration = Migration(
            version=version,
            name=name,
            operations=operations,
            dependencies=dependencies,
            created_at=datetime.now()
        )
        
        self._save_migration(migration)
        print(f"Generated migration {version}: {name}")
        
        return migration
        
    def apply_migrations(self) -> None:
        """Apply all pending migrations"""
        db = DatabaseManager.get_database()
        
        # Ensure migration tracking table exists
        self._ensure_migration_table(db)
        
        # Get applied migrations
        applied_versions = self._get_applied_migrations(db)
        
        # Sort migrations by version
        pending_migrations = []
        for version in sorted(self._migrations.keys()):
            if version not in applied_versions:
                pending_migrations.append(self._migrations[version])
                
        if not pending_migrations:
            print("No pending migrations")
            return
            
        # Apply each migration
        for migration in pending_migrations:
            print(f"Applying migration {migration.version}: {migration.name}")
            
            try:
                sql_statements = migration.get_sql_forward(db.dialect)
                
                for sql in sql_statements:
                    if sql.strip() and not sql.strip().startswith('--'):
                        db.execute_raw(sql)
                        
                # Record migration as applied
                self._record_migration_applied(db, migration)
                migration.applied_at = datetime.now()
                self._save_migration(migration)
                
                print(f"Applied migration {migration.version}")
                
            except Exception as e:
                print(f"Error applying migration {migration.version}: {e}")
                db.connection.rollback()
                raise
                
    def rollback_migration(self, version: str) -> None:
        """Rollback a specific migration"""
        if version not in self._migrations:
            raise ValueError(f"Migration {version} not found")
            
        migration = self._migrations[version]
        db = DatabaseManager.get_database()
        
        print(f"Rolling back migration {version}: {migration.name}")
        
        try:
            sql_statements = migration.get_sql_backward(db.dialect)
            
            for sql in sql_statements:
                if sql.strip() and not sql.strip().startswith('--'):
                    db.execute_raw(sql)
                    
            # Remove migration record
            self._remove_migration_record(db, migration)
            migration.applied_at = None
            self._save_migration(migration)
            
            print(f"Rolled back migration {version}")
            
        except Exception as e:
            print(f"Error rolling back migration {version}: {e}")
            db.connection.rollback()
            raise
            
    def _get_current_schema(self) -> Dict[str, Any]:
        """Get current database schema"""
        db = DatabaseManager.get_database()
        schema = {}
        
        # For SQLite, get table info
        if db.dialect == "sqlite":
            cursor = db.execute_raw("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            for table_name in tables:
                if table_name.startswith('sqlite_') or table_name == 'pyframe_migrations':
                    continue
                    
                cursor = db.execute_raw(f"PRAGMA table_info({table_name})")
                columns = {}
                
                for row in cursor.fetchall():
                    col_name = row[1]
                    col_type = row[2]
                    not_null = row[3]
                    default_value = row[4]
                    primary_key = row[5]
                    
                    columns[col_name] = {
                        "type": col_type,
                        "not_null": bool(not_null),
                        "default": default_value,
                        "primary_key": bool(primary_key)
                    }
                    
                schema[table_name] = {"columns": columns}
                
        return schema
        
    def _get_target_schema(self) -> Dict[str, Any]:
        """Get target schema from model definitions"""
        schema = {}
        
        for model_class in ModelRegistry.get_all_models().values():
            table_name = model_class.get_table_name()
            columns = {}
            
            for field_name, field_obj in model_class._fields.items():
                columns[field_name] = {
                    "type": field_obj.to_database_type("sqlite"),
                    "not_null": field_obj.constraints.required and field_obj.constraints.default is None,
                    "default": field_obj.constraints.default,
                    "unique": field_obj.constraints.unique,
                    "foreign_key": field_obj.constraints.foreign_key
                }
                
            schema[table_name] = {"columns": columns}
            
        return schema
        
    def _compare_schemas(self, current: Dict[str, Any], target: Dict[str, Any]) -> List[MigrationOperation]:
        """Compare schemas and generate migration operations"""
        operations = []
        
        # Find new tables
        for table_name, table_def in target.items():
            if table_name not in current:
                # Create table operation
                model_name = self._get_model_name_for_table(table_name)
                if model_name:
                    model_class = ModelRegistry.get_model(model_name)
                    if model_class:
                        columns = []
                        foreign_keys = []
                        
                        for field_name, field_obj in model_class._fields.items():
                            column_def = f"{field_name} {field_obj.to_database_type('sqlite')}"
                            
                            if field_obj.constraints.unique:
                                column_def += " UNIQUE"
                            if field_obj.constraints.required and field_obj.constraints.default is None:
                                column_def += " NOT NULL"
                            if field_name == 'id':
                                column_def += " PRIMARY KEY"
                                
                            columns.append(column_def)
                            
                            # Foreign keys
                            if field_obj.constraints.foreign_key:
                                ref_model = ModelRegistry.get_model(field_obj.constraints.foreign_key)
                                if ref_model:
                                    ref_table = ref_model.get_table_name()
                                    foreign_keys.append(f"FOREIGN KEY ({field_name}) REFERENCES {ref_table}(id)")
                                    
                        operations.append(MigrationOperation(
                            operation_type="create_table",
                            model_name=model_name,
                            table_name=table_name,
                            details={
                                "columns": columns,
                                "foreign_keys": foreign_keys
                            }
                        ))
                        
        # Find dropped tables
        for table_name in current:
            if table_name not in target:
                model_name = self._get_model_name_for_table(table_name)
                operations.append(MigrationOperation(
                    operation_type="drop_table",
                    model_name=model_name or "Unknown",
                    table_name=table_name,
                    details={}
                ))
                
        # Find column changes in existing tables
        for table_name, table_def in target.items():
            if table_name in current:
                current_columns = current[table_name]["columns"]
                target_columns = table_def["columns"]
                
                # Find new columns
                for col_name, col_def in target_columns.items():
                    if col_name not in current_columns:
                        model_name = self._get_model_name_for_table(table_name)
                        model_class = ModelRegistry.get_model(model_name) if model_name else None
                        
                        if model_class and col_name in model_class._fields:
                            field_obj = model_class._fields[col_name]
                            column_def = f"{col_name} {field_obj.to_database_type('sqlite')}"
                            
                            if field_obj.constraints.unique:
                                column_def += " UNIQUE"
                            if field_obj.constraints.required and field_obj.constraints.default is None:
                                column_def += " NOT NULL"
                                
                            operations.append(MigrationOperation(
                                operation_type="add_column",
                                model_name=model_name or "Unknown",
                                table_name=table_name,
                                details={
                                    "column_name": col_name,
                                    "column_definition": column_def
                                }
                            ))
                            
                # Find dropped columns
                for col_name in current_columns:
                    if col_name not in target_columns:
                        operations.append(MigrationOperation(
                            operation_type="drop_column",
                            model_name=self._get_model_name_for_table(table_name) or "Unknown",
                            table_name=table_name,
                            details={
                                "column_name": col_name,
                                "column_definition": f"{col_name} {current_columns[col_name]['type']}"
                            }
                        ))
                        
        return operations
        
    def _get_model_name_for_table(self, table_name: str) -> Optional[str]:
        """Get model name for a table name"""
        for model_name, model_class in ModelRegistry.get_all_models().items():
            if model_class.get_table_name() == table_name:
                return model_name
        return None
        
    def _ensure_migration_table(self, db: Database) -> None:
        """Ensure migration tracking table exists"""
        sql = """
        CREATE TABLE IF NOT EXISTS pyframe_migrations (
            version VARCHAR(50) PRIMARY KEY,
            name VARCHAR(200),
            applied_at DATETIME
        )
        """
        db.execute_raw(sql)
        db.connection.commit()
        
    def _get_applied_migrations(self, db: Database) -> List[str]:
        """Get list of applied migration versions"""
        try:
            cursor = db.execute_raw("SELECT version FROM pyframe_migrations ORDER BY applied_at")
            return [row[0] for row in cursor.fetchall()]
        except:
            return []
            
    def _record_migration_applied(self, db: Database, migration: Migration) -> None:
        """Record a migration as applied"""
        sql = "INSERT INTO pyframe_migrations (version, name, applied_at) VALUES (?, ?, ?)"
        db.execute_raw(sql, (migration.version, migration.name, datetime.now().isoformat()))
        db.connection.commit()
        
    def _remove_migration_record(self, db: Database, migration: Migration) -> None:
        """Remove migration record"""
        sql = "DELETE FROM pyframe_migrations WHERE version = ?"
        db.execute_raw(sql, (migration.version,))
        db.connection.commit()
        
    def list_migrations(self) -> List[Migration]:
        """List all migrations"""
        return sorted(self._migrations.values(), key=lambda m: m.version)
        
    def get_migration_status(self) -> Dict[str, Any]:
        """Get migration status"""
        db = DatabaseManager.get_database()
        self._ensure_migration_table(db)
        
        applied_versions = self._get_applied_migrations(db)
        all_migrations = list(self._migrations.keys())
        pending_migrations = [v for v in all_migrations if v not in applied_versions]
        
        return {
            "total_migrations": len(all_migrations),
            "applied_migrations": len(applied_versions),
            "pending_migrations": len(pending_migrations),
            "latest_applied": max(applied_versions) if applied_versions else None,
            "pending_list": pending_migrations
        }
