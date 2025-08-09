"""
Automatic API Generator

Generates REST and GraphQL APIs automatically from model definitions
with built-in validation, pagination, filtering, and CRUD operations.
"""

import json
import uuid
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type, Callable
from datetime import datetime

from ..core.routing import Router, Route
from ..server.context import RequestContext
from .models import Model, ModelRegistry, Field, FieldType
from .database import DatabaseManager


class APIGenerator(ABC):
    """Base class for API generators"""
    
    def __init__(self, router: Router):
        self.router = router
        self.model_apis: Dict[str, Any] = {}
        
    @abstractmethod
    def generate_model_api(self, model_class: Type[Model]) -> None:
        """Generate API endpoints for a model"""
        pass
        
    def generate_all_apis(self) -> None:
        """Generate APIs for all registered models"""
        for model_name, model_class in ModelRegistry.get_all_models().items():
            self.generate_model_api(model_class)


class RESTAPIGenerator(APIGenerator):
    """
    Generates RESTful API endpoints for models.
    
    Creates standard CRUD endpoints:
    GET /api/models - List all instances
    GET /api/models/:id - Get specific instance
    POST /api/models - Create new instance
    PUT /api/models/:id - Update instance
    DELETE /api/models/:id - Delete instance
    """
    
    def __init__(self, router: Router, base_path: str = "/api"):
        super().__init__(router)
        self.base_path = base_path.rstrip('/')
        
    def generate_model_api(self, model_class: Type[Model]) -> None:
        """Generate REST API endpoints for a model"""
        
        model_name = model_class.__name__.lower()
        base_endpoint = f"{self.base_path}/{model_name}s"
        
        # Store model API info
        self.model_apis[model_name] = {
            "model_class": model_class,
            "base_endpoint": base_endpoint,
            "endpoints": {
                "list": f"GET {base_endpoint}",
                "create": f"POST {base_endpoint}",
                "get": f"GET {base_endpoint}/{{id}}",
                "update": f"PUT {base_endpoint}/{{id}}",
                "delete": f"DELETE {base_endpoint}/{{id}}"
            },
            "schema": model_class.get_schema()
        }
        
        # Generate endpoints
        self._generate_list_endpoint(model_class, base_endpoint)
        self._generate_create_endpoint(model_class, base_endpoint)
        self._generate_get_endpoint(model_class, base_endpoint)
        self._generate_update_endpoint(model_class, base_endpoint)
        self._generate_delete_endpoint(model_class, base_endpoint)
        
    def _generate_list_endpoint(self, model_class: Type[Model], base_endpoint: str) -> None:
        """Generate list/filter endpoint"""
        
        async def list_handler(context: RequestContext) -> Dict[str, Any]:
            try:
                # Parse query parameters for filtering and pagination
                filters = {}
                limit = None
                offset = None
                order_by = None
                
                for key, value in context.query_params.items():
                    if key == 'limit':
                        limit = int(value) if value.isdigit() else None
                    elif key == 'offset':
                        offset = int(value) if value.isdigit() else None
                    elif key == 'order_by':
                        order_by = value
                    elif key in model_class._fields:
                        # Validate and convert filter values
                        field_obj = model_class._fields[key]
                        try:
                            filters[key] = field_obj.validate(value)
                        except ValueError:
                            return {
                                "status": 400,
                                "headers": {"Content-Type": "application/json"},
                                "body": json.dumps({"error": f"Invalid value for field '{key}'"})
                            }
                            
                # Apply pagination limits
                if limit is None or limit > 100:
                    limit = 100  # Default/max limit
                if offset is None:
                    offset = 0
                    
                # Get instances
                instances = DatabaseManager.filter(
                    model_class, 
                    limit=limit, 
                    offset=offset, 
                    order_by=order_by,
                    **filters
                )
                
                # Get total count for pagination
                total = DatabaseManager.count(model_class, **filters)
                
                # Convert to dictionaries
                data = [instance.to_dict() for instance in instances]
                
                response_data = {
                    "data": data,
                    "pagination": {
                        "total": total,
                        "limit": limit,
                        "offset": offset,
                        "has_next": offset + limit < total,
                        "has_prev": offset > 0
                    }
                }
                
                return {
                    "status": 200,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps(response_data, default=str)
                }
                
            except Exception as e:
                return {
                    "status": 500,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": str(e)})
                }
                
        route = Route(base_endpoint, list_handler, ["GET"])
        self.router.add_route(route)
        
    def _generate_create_endpoint(self, model_class: Type[Model], base_endpoint: str) -> None:
        """Generate create endpoint"""
        
        async def create_handler(context: RequestContext) -> Dict[str, Any]:
            try:
                # Parse request body
                if not context.body:
                    return {
                        "status": 400,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps({"error": "Request body is required"})
                    }
                    
                try:
                    data = json.loads(context.body)
                except json.JSONDecodeError:
                    return {
                        "status": 400,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps({"error": "Invalid JSON in request body"})
                    }
                    
                # Create and validate instance
                try:
                    instance = model_class(**data)
                    instance.validate()
                    saved_instance = instance.save()
                    
                    return {
                        "status": 201,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps(saved_instance.to_dict(), default=str)
                    }
                    
                except ValueError as e:
                    return {
                        "status": 400,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps({"error": str(e)})
                    }
                    
            except Exception as e:
                return {
                    "status": 500,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": str(e)})
                }
                
        route = Route(base_endpoint, create_handler, ["POST"])
        self.router.add_route(route)
        
    def _generate_get_endpoint(self, model_class: Type[Model], base_endpoint: str) -> None:
        """Generate get single instance endpoint"""
        
        async def get_handler(context: RequestContext) -> Dict[str, Any]:
            try:
                instance_id = context.path_params.get("id")
                if not instance_id:
                    return {
                        "status": 400,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps({"error": "ID parameter is required"})
                    }
                    
                # Convert ID to appropriate type
                try:
                    if 'id' in model_class._fields:
                        id_field = model_class._fields['id']
                        instance_id = id_field.validate(instance_id)
                except ValueError:
                    return {
                        "status": 400,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps({"error": "Invalid ID format"})
                    }
                    
                # Get instance
                instance = DatabaseManager.get(model_class, id=instance_id)
                
                if not instance:
                    return {
                        "status": 404,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps({"error": "Instance not found"})
                    }
                    
                return {
                    "status": 200,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps(instance.to_dict(), default=str)
                }
                
            except Exception as e:
                return {
                    "status": 500,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": str(e)})
                }
                
        route = Route(f"{base_endpoint}/:id", get_handler, ["GET"])
        self.router.add_route(route)
        
    def _generate_update_endpoint(self, model_class: Type[Model], base_endpoint: str) -> None:
        """Generate update endpoint"""
        
        async def update_handler(context: RequestContext) -> Dict[str, Any]:
            try:
                instance_id = context.path_params.get("id")
                if not instance_id:
                    return {
                        "status": 400,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps({"error": "ID parameter is required"})
                    }
                    
                # Get existing instance
                try:
                    if 'id' in model_class._fields:
                        id_field = model_class._fields['id']
                        instance_id = id_field.validate(instance_id)
                except ValueError:
                    return {
                        "status": 400,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps({"error": "Invalid ID format"})
                    }
                    
                instance = DatabaseManager.get(model_class, id=instance_id)
                if not instance:
                    return {
                        "status": 404,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps({"error": "Instance not found"})
                    }
                    
                # Parse request body
                if not context.body:
                    return {
                        "status": 400,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps({"error": "Request body is required"})
                    }
                    
                try:
                    data = json.loads(context.body)
                except json.JSONDecodeError:
                    return {
                        "status": 400,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps({"error": "Invalid JSON in request body"})
                    }
                    
                # Update instance attributes
                for field_name, value in data.items():
                    if field_name in model_class._fields and field_name != 'id':
                        setattr(instance, field_name, value)
                        
                # Validate and save
                try:
                    instance.validate()
                    saved_instance = instance.save()
                    
                    return {
                        "status": 200,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps(saved_instance.to_dict(), default=str)
                    }
                    
                except ValueError as e:
                    return {
                        "status": 400,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps({"error": str(e)})
                    }
                    
            except Exception as e:
                return {
                    "status": 500,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": str(e)})
                }
                
        route = Route(f"{base_endpoint}/:id", update_handler, ["PUT"])
        self.router.add_route(route)
        
    def _generate_delete_endpoint(self, model_class: Type[Model], base_endpoint: str) -> None:
        """Generate delete endpoint"""
        
        async def delete_handler(context: RequestContext) -> Dict[str, Any]:
            try:
                instance_id = context.path_params.get("id")
                if not instance_id:
                    return {
                        "status": 400,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps({"error": "ID parameter is required"})
                    }
                    
                # Get existing instance
                try:
                    if 'id' in model_class._fields:
                        id_field = model_class._fields['id']
                        instance_id = id_field.validate(instance_id)
                except ValueError:
                    return {
                        "status": 400,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps({"error": "Invalid ID format"})
                    }
                    
                instance = DatabaseManager.get(model_class, id=instance_id)
                if not instance:
                    return {
                        "status": 404,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps({"error": "Instance not found"})
                    }
                    
                # Delete instance
                instance.delete()
                
                return {
                    "status": 204,
                    "headers": {"Content-Type": "application/json"},
                    "body": ""
                }
                
            except Exception as e:
                return {
                    "status": 500,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": str(e)})
                }
                
        route = Route(f"{base_endpoint}/:id", delete_handler, ["DELETE"])
        self.router.add_route(route)
        
    def generate_api_documentation(self) -> Dict[str, Any]:
        """Generate OpenAPI documentation for the REST API"""
        
        spec = {
            "openapi": "3.0.0",
            "info": {
                "title": "PyFrame Auto-generated API",
                "version": "1.0.0",
                "description": "Automatically generated REST API from PyFrame models"
            },
            "paths": {},
            "components": {
                "schemas": {}
            }
        }
        
        # Add model schemas
        for model_name, api_info in self.model_apis.items():
            model_class = api_info["model_class"]
            schema = model_class.get_schema()
            spec["components"]["schemas"][model_class.__name__] = schema
            
            # Add endpoints to paths
            base_endpoint = api_info["base_endpoint"]
            
            # List endpoint
            spec["paths"][base_endpoint] = {
                "get": {
                    "summary": f"List {model_class.__name__} instances",
                    "parameters": [
                        {"name": "limit", "in": "query", "schema": {"type": "integer", "default": 100}},
                        {"name": "offset", "in": "query", "schema": {"type": "integer", "default": 0}},
                        {"name": "order_by", "in": "query", "schema": {"type": "string"}}
                    ],
                    "responses": {
                        "200": {
                            "description": "List of instances",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "data": {
                                                "type": "array",
                                                "items": {"$ref": f"#/components/schemas/{model_class.__name__}"}
                                            },
                                            "pagination": {"type": "object"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "summary": f"Create new {model_class.__name__}",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": f"#/components/schemas/{model_class.__name__}"}
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Created instance",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": f"#/components/schemas/{model_class.__name__}"}
                                }
                            }
                        }
                    }
                }
            }
            
            # Instance endpoints
            instance_endpoint = f"{base_endpoint}/{{id}}"
            spec["paths"][instance_endpoint] = {
                "get": {
                    "summary": f"Get {model_class.__name__} by ID",
                    "parameters": [
                        {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {
                        "200": {
                            "description": "Instance details",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": f"#/components/schemas/{model_class.__name__}"}
                                }
                            }
                        },
                        "404": {"description": "Instance not found"}
                    }
                },
                "put": {
                    "summary": f"Update {model_class.__name__}",
                    "parameters": [
                        {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": f"#/components/schemas/{model_class.__name__}"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Updated instance",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": f"#/components/schemas/{model_class.__name__}"}
                                }
                            }
                        },
                        "404": {"description": "Instance not found"}
                    }
                },
                "delete": {
                    "summary": f"Delete {model_class.__name__}",
                    "parameters": [
                        {"name": "id", "in": "path", "required": True, "schema": {"type": "string"}}
                    ],
                    "responses": {
                        "204": {"description": "Instance deleted"},
                        "404": {"description": "Instance not found"}
                    }
                }
            }
            
        return spec


class GraphQLAPIGenerator(APIGenerator):
    """
    Generates GraphQL API from models.
    
    Creates GraphQL schema with queries and mutations for all models.
    """
    
    def __init__(self, router: Router, endpoint: str = "/graphql"):
        super().__init__(router)
        self.endpoint = endpoint
        self.schema_types = {}
        self.queries = {}
        self.mutations = {}
        
    def generate_model_api(self, model_class: Type[Model]) -> None:
        """Generate GraphQL schema for a model"""
        
        model_name = model_class.__name__
        
        # Generate GraphQL type
        self.schema_types[model_name] = self._generate_graphql_type(model_class)
        
        # Generate queries
        self.queries.update(self._generate_queries(model_class))
        
        # Generate mutations
        self.mutations.update(self._generate_mutations(model_class))
        
    def _generate_graphql_type(self, model_class: Type[Model]) -> str:
        """Generate GraphQL type definition for a model"""
        
        fields = []
        
        for field_name, field_obj in model_class._fields.items():
            graphql_type = self._field_type_to_graphql(field_obj.field_type)
            
            if field_obj.constraints.required:
                graphql_type += "!"
                
            fields.append(f"  {field_name}: {graphql_type}")
            
        return f"""
type {model_class.__name__} {{
{chr(10).join(fields)}
}}
"""
        
    def _field_type_to_graphql(self, field_type: FieldType) -> str:
        """Convert field type to GraphQL type"""
        
        type_mapping = {
            FieldType.STRING: "String",
            FieldType.INTEGER: "Int",
            FieldType.FLOAT: "Float",
            FieldType.BOOLEAN: "Boolean",
            FieldType.DATETIME: "String",  # ISO string
            FieldType.JSON: "String",  # JSON string
            FieldType.UUID: "ID",
            FieldType.TEXT: "String",
            FieldType.EMAIL: "String",
            FieldType.URL: "String"
        }
        
        return type_mapping.get(field_type, "String")
        
    def _generate_queries(self, model_class: Type[Model]) -> Dict[str, str]:
        """Generate GraphQL queries for a model"""
        
        model_name = model_class.__name__
        lower_name = model_name.lower()
        
        return {
            f"{lower_name}": f"{lower_name}(id: ID!): {model_name}",
            f"{lower_name}s": f"{lower_name}s(limit: Int, offset: Int): [{model_name}!]!"
        }
        
    def _generate_mutations(self, model_class: Type[Model]) -> Dict[str, str]:
        """Generate GraphQL mutations for a model"""
        
        model_name = model_class.__name__
        lower_name = model_name.lower()
        
        # Generate input type
        input_fields = []
        for field_name, field_obj in model_class._fields.items():
            if field_name not in ['id', 'created_at', 'updated_at']:  # Skip auto fields
                graphql_type = self._field_type_to_graphql(field_obj.field_type)
                if not field_obj.constraints.required:
                    graphql_type = f"{graphql_type}"  # Optional
                input_fields.append(f"  {field_name}: {graphql_type}")
                
        input_type = f"""
input {model_name}Input {{
{chr(10).join(input_fields)}
}}
"""
        
        self.schema_types[f"{model_name}Input"] = input_type
        
        return {
            f"create{model_name}": f"create{model_name}(input: {model_name}Input!): {model_name}!",
            f"update{model_name}": f"update{model_name}(id: ID!, input: {model_name}Input!): {model_name}!",
            f"delete{model_name}": f"delete{model_name}(id: ID!): Boolean!"
        }
        
    def generate_schema(self) -> str:
        """Generate complete GraphQL schema"""
        
        # Type definitions
        types = "\n".join(self.schema_types.values())
        
        # Query type
        query_fields = [f"  {query}" for query in self.queries.values()]
        queries = f"""
type Query {{
{chr(10).join(query_fields)}
}}
"""
        
        # Mutation type
        mutation_fields = [f"  {mutation}" for mutation in self.mutations.values()]
        mutations = f"""
type Mutation {{
{chr(10).join(mutation_fields)}
}}
"""
        
        return f"{types}\n{queries}\n{mutations}"
        
    def create_graphql_endpoint(self) -> None:
        """Create GraphQL endpoint with schema and resolvers"""
        
        async def graphql_handler(context: RequestContext) -> Dict[str, Any]:
            # This is a simplified GraphQL handler
            # In practice, you'd use a library like graphene or similar
            
            if context.method == "GET":
                # Return GraphQL playground/schema
                schema = self.generate_schema()
                return {
                    "status": 200,
                    "headers": {"Content-Type": "text/plain"},
                    "body": schema
                }
            elif context.method == "POST":
                # Handle GraphQL queries
                try:
                    data = json.loads(context.body)
                    query = data.get("query", "")
                    variables = data.get("variables", {})
                    
                    # Simple query parsing (in practice, use a real GraphQL library)
                    result = self._execute_simple_query(query, variables)
                    
                    return {
                        "status": 200,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps(result, default=str)
                    }
                    
                except Exception as e:
                    return {
                        "status": 400,
                        "headers": {"Content-Type": "application/json"},
                        "body": json.dumps({"errors": [{"message": str(e)}]})
                    }
            else:
                return {
                    "status": 405,
                    "headers": {"Content-Type": "application/json"},
                    "body": json.dumps({"error": "Method not allowed"})
                }
                
        route = Route(self.endpoint, graphql_handler, ["GET", "POST"])
        self.router.add_route(route)
        
    def _execute_simple_query(self, query: str, variables: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a simple GraphQL query (simplified implementation)"""
        
        # This is a very basic implementation
        # In practice, you'd use a proper GraphQL library
        
        if "users" in query.lower():
            from .models import User
            users = DatabaseManager.all(User)
            return {
                "data": {
                    "users": [user.to_dict() for user in users]
                }
            }
        elif "posts" in query.lower():
            from .models import Post
            posts = DatabaseManager.all(Post)
            return {
                "data": {
                    "posts": [post.to_dict() for post in posts]
                }
            }
        else:
            return {
                "data": None,
                "errors": [{"message": "Query not supported in this simplified implementation"}]
            }
