"""
Model Definition System

Provides decorators and base classes for defining data models that automatically
generate database schemas, migrations, validation, and API endpoints.
"""

import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union, get_type_hints
from enum import Enum


class FieldType(Enum):
    """Supported field types for models"""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    JSON = "json"
    UUID = "uuid"
    TEXT = "text"
    EMAIL = "email"
    URL = "url"
    
    
@dataclass
class FieldConstraints:
    """Constraints that can be applied to model fields"""
    required: bool = True
    unique: bool = False
    default: Any = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[Union[int, float]] = None
    max_value: Optional[Union[int, float]] = None
    choices: Optional[List[Any]] = None
    regex: Optional[str] = None
    foreign_key: Optional[str] = None
    related_name: Optional[str] = None


class Field:
    """
    Field definition for model attributes.
    
    Automatically infers type from Python type annotations and provides
    validation, constraints, and database mapping.
    """
    
    def __init__(
        self,
        field_type: Optional[FieldType] = None,
        required: bool = True,
        unique: bool = False,
        default: Any = None,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
        choices: Optional[List[Any]] = None,
        regex: Optional[str] = None,
        foreign_key: Optional[str] = None,
        related_name: Optional[str] = None,
        help_text: Optional[str] = None,
        auto_now: bool = False,
        auto_now_add: bool = False
    ):
        self.field_type = field_type
        self.constraints = FieldConstraints(
            required=required,
            unique=unique,
            default=default,
            min_length=min_length,
            max_length=max_length,
            min_value=min_value,
            max_value=max_value,
            choices=choices,
            regex=regex,
            foreign_key=foreign_key,
            related_name=related_name
        )
        self.help_text = help_text
        self.auto_now = auto_now
        self.auto_now_add = auto_now_add
        
        # Runtime attributes
        self.name = None
        self.model_class = None
        
    def validate(self, value: Any) -> Any:
        """Validate field value against constraints"""
        
        # Handle None values
        if value is None:
            if self.constraints.required and self.constraints.default is None:
                raise ValueError(f"Field '{self.name}' is required")
            return self.constraints.default
            
        # Type validation
        if self.field_type == FieldType.STRING:
            if not isinstance(value, str):
                value = str(value)
            if self.constraints.min_length and len(value) < self.constraints.min_length:
                raise ValueError(f"String too short (min {self.constraints.min_length})")
            if self.constraints.max_length and len(value) > self.constraints.max_length:
                raise ValueError(f"String too long (max {self.constraints.max_length})")
                
        elif self.field_type == FieldType.INTEGER:
            if not isinstance(value, int):
                value = int(value)
            if self.constraints.min_value and value < self.constraints.min_value:
                raise ValueError(f"Value too small (min {self.constraints.min_value})")
            if self.constraints.max_value and value > self.constraints.max_value:
                raise ValueError(f"Value too large (max {self.constraints.max_value})")
                
        elif self.field_type == FieldType.FLOAT:
            if not isinstance(value, (int, float)):
                value = float(value)
            if self.constraints.min_value and value < self.constraints.min_value:
                raise ValueError(f"Value too small (min {self.constraints.min_value})")
            if self.constraints.max_value and value > self.constraints.max_value:
                raise ValueError(f"Value too large (max {self.constraints.max_value})")
                
        elif self.field_type == FieldType.BOOLEAN:
            if not isinstance(value, bool):
                value = bool(value)
                
        elif self.field_type == FieldType.DATETIME:
            if isinstance(value, str):
                # Parse datetime string
                value = datetime.fromisoformat(value.replace('Z', '+00:00'))
            elif not isinstance(value, datetime):
                raise ValueError("Invalid datetime value")
                
        elif self.field_type == FieldType.UUID:
            if isinstance(value, str):
                value = uuid.UUID(value)
            elif not isinstance(value, uuid.UUID):
                raise ValueError("Invalid UUID value")
                
        elif self.field_type == FieldType.EMAIL:
            if not isinstance(value, str):
                value = str(value)
            # Basic email validation
            if '@' not in value or '.' not in value.split('@')[1]:
                raise ValueError("Invalid email format")
                
        elif self.field_type == FieldType.URL:
            if not isinstance(value, str):
                value = str(value)
            # Basic URL validation
            if not (value.startswith('http://') or value.startswith('https://')):
                raise ValueError("Invalid URL format")
                
        # Choice validation
        if self.constraints.choices and value not in self.constraints.choices:
            raise ValueError(f"Value must be one of {self.constraints.choices}")
            
        # Regex validation
        if self.constraints.regex:
            import re
            if not re.match(self.constraints.regex, str(value)):
                raise ValueError(f"Value does not match pattern {self.constraints.regex}")
                
        return value
        
    def to_database_type(self, dialect: str = "sqlite") -> str:
        """Convert field type to database column type"""
        
        type_mapping = {
            "sqlite": {
                FieldType.STRING: "VARCHAR",
                FieldType.INTEGER: "INTEGER", 
                FieldType.FLOAT: "REAL",
                FieldType.BOOLEAN: "BOOLEAN",
                FieldType.DATETIME: "DATETIME",
                FieldType.JSON: "TEXT",
                FieldType.UUID: "VARCHAR(36)",
                FieldType.TEXT: "TEXT",
                FieldType.EMAIL: "VARCHAR",
                FieldType.URL: "VARCHAR"
            },
            "postgresql": {
                FieldType.STRING: "VARCHAR",
                FieldType.INTEGER: "INTEGER",
                FieldType.FLOAT: "REAL", 
                FieldType.BOOLEAN: "BOOLEAN",
                FieldType.DATETIME: "TIMESTAMP",
                FieldType.JSON: "JSONB",
                FieldType.UUID: "UUID",
                FieldType.TEXT: "TEXT",
                FieldType.EMAIL: "VARCHAR",
                FieldType.URL: "VARCHAR"
            }
        }
        
        mapping = type_mapping.get(dialect, type_mapping["sqlite"])
        db_type = mapping.get(self.field_type, "TEXT")
        
        # Add length constraint for strings
        if (self.field_type in [FieldType.STRING, FieldType.EMAIL, FieldType.URL] and 
            self.constraints.max_length):
            db_type = f"{db_type}({self.constraints.max_length})"
            
        return db_type
        
    def to_json_schema(self) -> Dict[str, Any]:
        """Convert field to JSON Schema definition"""
        
        schema = {}
        
        # Type mapping
        type_mapping = {
            FieldType.STRING: "string",
            FieldType.INTEGER: "integer",
            FieldType.FLOAT: "number", 
            FieldType.BOOLEAN: "boolean",
            FieldType.DATETIME: "string",
            FieldType.JSON: "object",
            FieldType.UUID: "string",
            FieldType.TEXT: "string",
            FieldType.EMAIL: "string",
            FieldType.URL: "string"
        }
        
        schema["type"] = type_mapping.get(self.field_type, "string")
        
        # Format for special types
        if self.field_type == FieldType.DATETIME:
            schema["format"] = "date-time"
        elif self.field_type == FieldType.EMAIL:
            schema["format"] = "email"
        elif self.field_type == FieldType.URL:
            schema["format"] = "uri"
        elif self.field_type == FieldType.UUID:
            schema["format"] = "uuid"
            
        # Constraints
        if self.constraints.min_length:
            schema["minLength"] = self.constraints.min_length
        if self.constraints.max_length:
            schema["maxLength"] = self.constraints.max_length
        if self.constraints.min_value:
            schema["minimum"] = self.constraints.min_value
        if self.constraints.max_value:
            schema["maximum"] = self.constraints.max_value
        if self.constraints.choices:
            schema["enum"] = self.constraints.choices
        if self.constraints.regex:
            schema["pattern"] = self.constraints.regex
        if self.constraints.default is not None:
            schema["default"] = self.constraints.default
        if self.help_text:
            schema["description"] = self.help_text
            
        return schema


class ModelMeta(type):
    """Metaclass for Model classes that processes field definitions"""
    
    def __new__(mcs, name, bases, namespace, **kwargs):
        # Extract field definitions
        fields = {}
        annotations = namespace.get('__annotations__', {})
        
        # Process annotated fields
        for field_name, field_type_hint in annotations.items():
            if not field_name.startswith('_'):
                field_obj = namespace.get(field_name)
                
                if isinstance(field_obj, Field):
                    # Explicit field definition
                    if field_obj.field_type is None:
                        field_obj.field_type = mcs._infer_field_type(field_type_hint)
                else:
                    # Infer field from type annotation
                    field_obj = Field(field_type=mcs._infer_field_type(field_type_hint))
                    
                field_obj.name = field_name
                fields[field_name] = field_obj
                
        # Process fields from base classes
        for base in bases:
            if hasattr(base, '_fields'):
                for field_name, field_obj in base._fields.items():
                    if field_name not in fields:
                        fields[field_name] = field_obj
                        
        # Create the class
        cls = super().__new__(mcs, name, bases, namespace)
        cls._fields = fields
        cls._table_name = kwargs.get('table_name', name.lower() + 's')
        
        # Set field model references
        for field_obj in fields.values():
            field_obj.model_class = cls
            
        # Register with model registry
        if name != 'Model':  # Don't register the base Model class
            ModelRegistry.register(cls)
            
        return cls
        
    @staticmethod
    def _infer_field_type(type_hint) -> FieldType:
        """Infer FieldType from Python type annotation"""
        
        # Handle Optional types
        if hasattr(type_hint, '__origin__') and type_hint.__origin__ is Union:
            type_args = type_hint.__args__
            if len(type_args) == 2 and type(None) in type_args:
                # This is Optional[T]
                type_hint = next(arg for arg in type_args if arg is not type(None))
                
        # Direct type mapping
        type_mapping = {
            str: FieldType.STRING,
            int: FieldType.INTEGER,
            float: FieldType.FLOAT,
            bool: FieldType.BOOLEAN,
            datetime: FieldType.DATETIME,
            dict: FieldType.JSON,
            list: FieldType.JSON,
            uuid.UUID: FieldType.UUID
        }
        
        return type_mapping.get(type_hint, FieldType.STRING)


class Model(metaclass=ModelMeta):
    """
    Base class for all data models.
    
    Provides automatic schema generation, validation, serialization,
    and database operations with zero boilerplate.
    """
    
    # Default fields added to all models
    id: uuid.UUID = Field(FieldType.UUID, default=lambda: uuid.uuid4(), unique=True)
    created_at: datetime = Field(FieldType.DATETIME, auto_now_add=True)
    updated_at: datetime = Field(FieldType.DATETIME, auto_now=True)
    
    def __init__(self, **kwargs):
        # Set default values
        for field_name, field_obj in self._fields.items():
            if field_name in kwargs:
                value = kwargs[field_name]
            elif field_obj.auto_now_add and field_name == 'created_at':
                value = datetime.now()
            elif field_obj.auto_now and field_name == 'updated_at':
                value = datetime.now()
            elif field_obj.constraints.default is not None:
                if callable(field_obj.constraints.default):
                    value = field_obj.constraints.default()
                else:
                    value = field_obj.constraints.default
            else:
                value = None
                
            setattr(self, field_name, value)
            
    def validate(self) -> None:
        """Validate all field values"""
        errors = {}
        
        for field_name, field_obj in self._fields.items():
            try:
                value = getattr(self, field_name, None)
                validated_value = field_obj.validate(value)
                setattr(self, field_name, validated_value)
            except ValueError as e:
                errors[field_name] = str(e)
                
        if errors:
            raise ValueError(f"Validation errors: {errors}")
            
    def save(self) -> 'Model':
        """Save the model instance to the database"""
        self.validate()
        
        # Update timestamps
        if hasattr(self, 'updated_at'):
            self.updated_at = datetime.now()
            
        # Delegate to database manager
        from .database import DatabaseManager
        return DatabaseManager.save(self)
        
    def delete(self) -> None:
        """Delete the model instance from the database"""
        from .database import DatabaseManager
        DatabaseManager.delete(self)
        
    @classmethod
    def get(cls, **filters) -> Optional['Model']:
        """Get a single instance by filters"""
        from .database import DatabaseManager
        return DatabaseManager.get(cls, **filters)
        
    @classmethod
    def filter(cls, **filters) -> List['Model']:
        """Get multiple instances by filters"""
        from .database import DatabaseManager
        return DatabaseManager.filter(cls, **filters)
        
    @classmethod
    def all(cls) -> List['Model']:
        """Get all instances of this model"""
        from .database import DatabaseManager
        return DatabaseManager.all(cls)
        
    @classmethod
    def create(cls, **kwargs) -> 'Model':
        """Create and save a new instance"""
        instance = cls(**kwargs)
        return instance.save()
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert model instance to dictionary"""
        result = {}
        
        for field_name in self._fields:
            value = getattr(self, field_name, None)
            
            # Serialize special types
            if isinstance(value, datetime):
                value = value.isoformat()
            elif isinstance(value, uuid.UUID):
                value = str(value)
            elif value is None:
                value = None
            else:
                value = value
                
            result[field_name] = value
            
        return result
        
    def to_json(self) -> str:
        """Convert model instance to JSON"""
        return json.dumps(self.to_dict(), default=str)
        
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Model':
        """Create model instance from dictionary"""
        return cls(**data)
        
    @classmethod
    def from_json(cls, json_str: str) -> 'Model':
        """Create model instance from JSON"""
        data = json.loads(json_str)
        return cls.from_dict(data)
        
    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON Schema for this model"""
        properties = {}
        required = []
        
        for field_name, field_obj in cls._fields.items():
            properties[field_name] = field_obj.to_json_schema()
            if field_obj.constraints.required:
                required.append(field_name)
                
        return {
            "type": "object",
            "properties": properties,
            "required": required,
            "title": cls.__name__,
            "description": cls.__doc__ or f"{cls.__name__} model"
        }
        
    @classmethod
    def get_table_name(cls) -> str:
        """Get database table name"""
        return cls._table_name
        
    def __repr__(self):
        return f"{self.__class__.__name__}(id={getattr(self, 'id', None)})"


class ModelRegistry:
    """Registry for all model classes"""
    
    _models: Dict[str, Type[Model]] = {}
    
    @classmethod
    def register(cls, model_class: Type[Model]) -> None:
        """Register a model class"""
        cls._models[model_class.__name__] = model_class
        
    @classmethod
    def get_model(cls, name: str) -> Optional[Type[Model]]:
        """Get a model class by name"""
        return cls._models.get(name)
        
    @classmethod
    def get_all_models(cls) -> Dict[str, Type[Model]]:
        """Get all registered models"""
        return cls._models.copy()
        
    @classmethod
    def generate_schema(cls) -> Dict[str, Any]:
        """Generate JSON Schema for all models"""
        schemas = {}
        for name, model_class in cls._models.items():
            schemas[name] = model_class.get_schema()
        return schemas


# Example models demonstrating the system

class User(Model):
    """Example user model"""
    
    username: str = Field(FieldType.STRING, unique=True, max_length=50)
    email: str = Field(FieldType.EMAIL, unique=True)
    password_hash: str = Field(FieldType.STRING, max_length=255)
    first_name: str = Field(FieldType.STRING, max_length=50, required=False)
    last_name: str = Field(FieldType.STRING, max_length=50, required=False)
    is_active: bool = Field(FieldType.BOOLEAN, default=True)
    is_admin: bool = Field(FieldType.BOOLEAN, default=False)
    

class Post(Model):
    """Example blog post model"""
    
    title: str = Field(FieldType.STRING, max_length=200)
    content: str = Field(FieldType.TEXT)
    author_id: uuid.UUID = Field(FieldType.UUID, foreign_key="User")
    slug: str = Field(FieldType.STRING, unique=True, max_length=200)
    published: bool = Field(FieldType.BOOLEAN, default=False)
    published_at: Optional[datetime] = Field(FieldType.DATETIME, required=False)
    tags: List[str] = Field(FieldType.JSON, default=list)
    

class Comment(Model):
    """Example comment model"""
    
    content: str = Field(FieldType.TEXT)
    author_id: uuid.UUID = Field(FieldType.UUID, foreign_key="User")
    post_id: uuid.UUID = Field(FieldType.UUID, foreign_key="Post")
    parent_id: Optional[uuid.UUID] = Field(FieldType.UUID, foreign_key="Comment", required=False)
    is_approved: bool = Field(FieldType.BOOLEAN, default=False)
