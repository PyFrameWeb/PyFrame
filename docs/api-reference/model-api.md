# Model API Reference

Complete reference for PyFrame's data models and ORM system.

## Base Model Class

### `Model`

The base class for all PyFrame data models.

```python
from pyframe import Model, Field, FieldType

class User(Model):
    name = Field(FieldType.STRING, max_length=100)
    email = Field(FieldType.EMAIL, unique=True)
    
    class Meta:
        table_name = 'users'
        indexes = ['email']
```

#### Class Methods

##### `create(**kwargs) -> Model`
Create a new model instance and save to database.

**Parameters:**
- `**kwargs` - Field values for the new instance

**Returns:**
- `Model` - The created model instance

**Example:**
```python
user = await User.create(
    name='John Doe',
    email='john@example.com'
)
```

##### `get(id) -> Model`
Get a model instance by primary key.

**Parameters:**
- `id` - Primary key value

**Returns:**
- `Model` - The model instance

**Raises:**
- `DoesNotExist` - If no instance found

**Example:**
```python
user = await User.get(123)
```

##### `filter(**kwargs) -> QuerySet`
Filter model instances by field values.

**Parameters:**
- `**kwargs` - Field filters

**Returns:**
- `QuerySet` - Query set for chaining

**Example:**
```python
active_users = await User.filter(is_active=True)
recent_users = await User.filter(created_at__gte=datetime.now() - timedelta(days=7))
```

##### `all() -> List[Model]`
Get all model instances.

**Returns:**
- `List[Model]` - All model instances

**Example:**
```python
all_users = await User.all()
```

##### `count() -> int`
Count total number of instances.

**Returns:**
- `int` - Number of instances

**Example:**
```python
user_count = await User.count()
```

##### `exists() -> bool`
Check if any instances exist.

**Returns:**
- `bool` - True if instances exist

**Example:**
```python
has_users = await User.exists()
```

##### `bulk_create(instances) -> List[Model]`
Create multiple instances in batch.

**Parameters:**
- `instances: List[Model]` - Model instances to create

**Returns:**
- `List[Model]` - Created instances with IDs

**Example:**
```python
users = [
    User(name='Alice', email='alice@example.com'),
    User(name='Bob', email='bob@example.com')
]
created_users = await User.bulk_create(users)
```

##### `bulk_update(instances, fields) -> None`
Update multiple instances in batch.

**Parameters:**
- `instances: List[Model]` - Model instances to update
- `fields: List[str]` - Fields to update

**Example:**
```python
for user in users:
    user.is_verified = True

await User.bulk_update(users, ['is_verified'])
```

#### Instance Methods

##### `save(update_fields=None) -> None`
Save the model instance to database.

**Parameters:**
- `update_fields: List[str]` - Optional list of fields to update

**Example:**
```python
user.name = 'Jane Doe'
await user.save()

# Update only specific fields
await user.save(update_fields=['name'])
```

##### `delete() -> None`
Delete the model instance from database.

**Example:**
```python
await user.delete()
```

##### `refresh() -> None`
Reload the instance from database.

**Example:**
```python
await user.refresh()
```

##### `to_dict() -> dict`
Convert instance to dictionary.

**Returns:**
- `dict` - Instance data as dictionary

**Example:**
```python
user_data = user.to_dict()
# {'id': 1, 'name': 'John', 'email': 'john@example.com'}
```

##### `update(**kwargs) -> None`
Update specific fields.

**Parameters:**
- `**kwargs` - Field values to update

**Example:**
```python
await user.update(name='New Name', is_active=False)
```

#### Properties

##### `pk`
Primary key value of the instance.

```python
user_id = user.pk
```

##### `is_saved`
Whether the instance has been saved to database.

```python
if user.is_saved:
    print("User exists in database")
```

---

## Field Types

### `Field`

Base field class for model attributes.

```python
from pyframe import Field, FieldType

class MyModel(Model):
    name = Field(FieldType.STRING, max_length=100, required=True)
    age = Field(FieldType.INTEGER, min_value=0, default=0)
```

#### Parameters

- `field_type: FieldType` - The type of field
- `required: bool` - Whether field is required (default: `False`)
- `default: Any` - Default value for field
- `null: bool` - Whether field can be NULL (default: `False`)
- `blank: bool` - Whether field can be blank in forms (default: `False`)
- `unique: bool` - Whether field values must be unique (default: `False`)
- `db_index: bool` - Whether to create database index (default: `False`)
- `validators: List[callable]` - Custom validation functions

### Field Types

#### `FieldType.STRING`
Text field with optional length limit.

**Parameters:**
- `max_length: int` - Maximum string length
- `min_length: int` - Minimum string length

```python
name = Field(FieldType.STRING, max_length=100, min_length=2)
```

#### `FieldType.INTEGER`
Integer field with optional range validation.

**Parameters:**
- `min_value: int` - Minimum allowed value
- `max_value: int` - Maximum allowed value

```python
age = Field(FieldType.INTEGER, min_value=0, max_value=150)
```

#### `FieldType.FLOAT`
Floating point number field.

**Parameters:**
- `min_value: float` - Minimum allowed value
- `max_value: float` - Maximum allowed value

```python
rating = Field(FieldType.FLOAT, min_value=0.0, max_value=5.0)
```

#### `FieldType.DECIMAL`
Fixed-precision decimal field.

**Parameters:**
- `max_digits: int` - Total number of digits
- `decimal_places: int` - Number of decimal places

```python
price = Field(FieldType.DECIMAL, max_digits=10, decimal_places=2)
```

#### `FieldType.BOOLEAN`
Boolean true/false field.

```python
is_active = Field(FieldType.BOOLEAN, default=True)
```

#### `FieldType.DATE`
Date field (year, month, day).

```python
birth_date = Field(FieldType.DATE)
```

#### `FieldType.DATETIME`
Date and time field.

**Parameters:**
- `auto_now: bool` - Update on every save
- `auto_now_add: bool` - Set on creation only

```python
created_at = Field(FieldType.DATETIME, auto_now_add=True)
updated_at = Field(FieldType.DATETIME, auto_now=True)
```

#### `FieldType.TIME`
Time field (hour, minute, second).

```python
meeting_time = Field(FieldType.TIME)
```

#### `FieldType.EMAIL`
Email address field with validation.

```python
email = Field(FieldType.EMAIL, unique=True)
```

#### `FieldType.URL`
URL field with validation.

```python
website = Field(FieldType.URL, null=True)
```

#### `FieldType.UUID`
UUID field for unique identifiers.

```python
uuid_id = Field(FieldType.UUID, primary_key=True)
```

#### `FieldType.JSON`
JSON data field.

```python
metadata = Field(FieldType.JSON, default=dict)
```

#### `FieldType.TEXT`
Large text field.

```python
description = Field(FieldType.TEXT, null=True)
```

#### `FieldType.BINARY`
Binary data field.

```python
file_content = Field(FieldType.BINARY)
```

#### `FieldType.CHOICE`
Field with predefined choices.

**Parameters:**
- `choices: List[tuple]` - Available choices as (value, label) tuples

```python
status = Field(FieldType.CHOICE, choices=[
    ('draft', 'Draft'),
    ('published', 'Published'),
    ('archived', 'Archived')
])
```

#### `FieldType.SLUG`
URL-safe slug field.

**Parameters:**
- `auto_generate: bool` - Auto-generate from another field
- `source_field: str` - Field to generate slug from

```python
slug = Field(FieldType.SLUG, auto_generate=True, source_field='title')
```

---

## Relationship Fields

### `FieldType.FOREIGN_KEY`
Reference to another model.

**Parameters:**
- `to: Model` - Target model class
- `on_delete: str` - Deletion behavior ('CASCADE', 'SET_NULL', 'PROTECT')
- `related_name: str` - Name for reverse relation

```python
class Post(Model):
    author = Field(FieldType.FOREIGN_KEY, to=User, on_delete='CASCADE')
    category = Field(FieldType.FOREIGN_KEY, to='Category', related_name='posts')

# Usage
post = await Post.get(1)
author = await post.author  # Get related user
author_posts = await author.posts.all()  # Reverse relation
```

### `FieldType.ONE_TO_ONE`
One-to-one relationship with another model.

**Parameters:**
- `to: Model` - Target model class
- `on_delete: str` - Deletion behavior

```python
class UserProfile(Model):
    user = Field(FieldType.ONE_TO_ONE, to=User, on_delete='CASCADE')
    bio = Field(FieldType.TEXT)

# Usage
profile = await UserProfile.get(user_id=1)
user = await profile.user
user_profile = await user.profile
```

### `FieldType.MANY_TO_MANY`
Many-to-many relationship with another model.

**Parameters:**
- `to: Model` - Target model class
- `through: Model` - Intermediate model (optional)
- `related_name: str` - Name for reverse relation

```python
class Post(Model):
    title = Field(FieldType.STRING, max_length=200)
    tags = Field(FieldType.MANY_TO_MANY, to='Tag')

class Tag(Model):
    name = Field(FieldType.STRING, max_length=50)

# Usage
post = await Post.get(1)
await post.tags.add(tag1, tag2)  # Add tags
await post.tags.remove(tag1)     # Remove tag
await post.tags.set([tag2, tag3])  # Replace all tags
tags = await post.tags.all()     # Get all tags
```

---

## QuerySet API

### `QuerySet`

Query set for building and executing database queries.

```python
# QuerySet is returned by filter operations
users = User.filter(is_active=True)  # Returns QuerySet
active_users = await users  # Execute query
```

#### Methods

##### `filter(**kwargs) -> QuerySet`
Add filter conditions.

```python
users = await User.filter(is_active=True, age__gte=18)
```

##### `exclude(**kwargs) -> QuerySet`
Exclude records matching conditions.

```python
users = await User.exclude(is_banned=True)
```

##### `order_by(*fields) -> QuerySet`
Order results by fields.

```python
users = await User.order_by('name', '-created_at')  # - for descending
```

##### `limit(count) -> QuerySet`
Limit number of results.

```python
recent_users = await User.order_by('-created_at').limit(10)
```

##### `offset(count) -> QuerySet`
Skip number of results.

```python
page_2_users = await User.offset(20).limit(10)
```

##### `select_related(*fields) -> QuerySet`
Eagerly load related objects (JOIN).

```python
posts = await Post.select_related('author', 'category')
# No additional query needed for post.author
```

##### `prefetch_related(*fields) -> QuerySet`
Prefetch related objects (separate queries).

```python
posts = await Post.prefetch_related('tags')
# All tags loaded in one additional query
```

##### `distinct(*fields) -> QuerySet`
Return distinct results.

```python
unique_categories = await Post.values('category').distinct()
```

##### `values(*fields) -> QuerySet`
Return dictionaries instead of model instances.

```python
user_data = await User.values('id', 'name', 'email')
# [{'id': 1, 'name': 'John', 'email': 'john@example.com'}, ...]
```

##### `values_list(*fields, flat=False) -> QuerySet`
Return tuples instead of model instances.

```python
user_names = await User.values_list('name', flat=True)
# ['John', 'Jane', 'Bob', ...]

user_pairs = await User.values_list('id', 'name')
# [(1, 'John'), (2, 'Jane'), (3, 'Bob'), ...]
```

##### `aggregate(**kwargs) -> dict`
Perform aggregation functions.

```python
from pyframe.models import Count, Sum, Avg, Max, Min

stats = await Post.aggregate(
    total_posts=Count('id'),
    avg_views=Avg('view_count'),
    max_views=Max('view_count')
)
# {'total_posts': 150, 'avg_views': 245.6, 'max_views': 1500}
```

##### `annotate(**kwargs) -> QuerySet`
Add annotations to each result.

```python
authors = await User.annotate(
    post_count=Count('posts')
).filter(post_count__gt=5)
```

##### `update(**kwargs) -> int`
Update matching records.

**Returns:**
- `int` - Number of updated records

```python
updated_count = await User.filter(is_active=False).update(is_active=True)
```

##### `delete() -> int`
Delete matching records.

**Returns:**
- `int` - Number of deleted records

```python
deleted_count = await Post.filter(published=False).delete()
```

---

## Query Filters

### Lookup Types

#### Exact Match
```python
User.filter(name='John')           # name = 'John'
User.filter(age=25)                # age = 25
```

#### Case Sensitivity
```python
User.filter(name__iexact='john')   # Case-insensitive exact match
User.filter(email__icontains='GMAIL')  # Case-insensitive contains
```

#### String Operations
```python
User.filter(name__contains='Jo')       # name LIKE '%Jo%'
User.filter(name__startswith='J')      # name LIKE 'J%'
User.filter(name__endswith='son')      # name LIKE '%son'
User.filter(email__endswith='@gmail.com')
```

#### Null Checks
```python
User.filter(bio__isnull=True)      # bio IS NULL
User.filter(bio__isnull=False)     # bio IS NOT NULL
```

#### Numeric Comparisons
```python
User.filter(age__gt=18)            # age > 18
User.filter(age__gte=18)           # age >= 18
User.filter(age__lt=65)            # age < 65
User.filter(age__lte=65)           # age <= 65
User.filter(score__range=(80, 100))  # score BETWEEN 80 AND 100
```

#### List Operations
```python
User.filter(id__in=[1, 2, 3, 4])   # id IN (1, 2, 3, 4)
User.filter(status__in=['active', 'premium'])
```

#### Date/Time Filters
```python
Post.filter(created_at__date=date.today())     # Extract date part
Post.filter(created_at__year=2024)             # Extract year
Post.filter(created_at__month=1)               # Extract month
Post.filter(created_at__day=15)                # Extract day
Post.filter(created_at__week_day=1)            # Monday = 1
```

#### Relationship Filters
```python
Post.filter(author__name='John')               # JOIN with author
Post.filter(author__age__gte=18)               # Chain through relations
Post.filter(tags__name__in=['python', 'web'])  # Many-to-many filter
```

---

## Model Meta Options

### `Meta` Class

Configure model behavior with the `Meta` inner class.

```python
class User(Model):
    name = Field(FieldType.STRING, max_length=100)
    email = Field(FieldType.EMAIL)
    
    class Meta:
        table_name = 'users'
        ordering = ['-created_at']
        indexes = ['email', 'created_at']
        unique_together = [('name', 'email')]
        abstract = False
```

#### Options

##### `table_name: str`
Custom database table name.

```python
class Meta:
    table_name = 'custom_users'
```

##### `ordering: List[str]`
Default ordering for queries.

```python
class Meta:
    ordering = ['-created_at', 'name']  # - for descending
```

##### `indexes: List[str|List[str]]`
Database indexes to create.

```python
class Meta:
    indexes = [
        'email',                    # Single field index
        ['user_id', 'created_at'],  # Composite index
        'status'
    ]
```

##### `unique_together: List[List[str]]`
Unique constraints across multiple fields.

```python
class Meta:
    unique_together = [
        ['user_id', 'post_id'],  # Unique combination
        ['slug', 'category']
    ]
```

##### `abstract: bool`
Whether model is abstract (no database table).

```python
class BaseModel(Model):
    created_at = Field(FieldType.DATETIME, auto_now_add=True)
    updated_at = Field(FieldType.DATETIME, auto_now=True)
    
    class Meta:
        abstract = True  # No table created

class User(BaseModel):  # Inherits created_at, updated_at
    name = Field(FieldType.STRING, max_length=100)
```

---

## Model Validation

### Field Validation

```python
def validate_adult_age(value):
    if value < 18:
        raise ValueError("Must be 18 or older")
    return value

class User(Model):
    age = Field(FieldType.INTEGER, validators=[validate_adult_age])
    email = Field(FieldType.EMAIL)  # Built-in email validation
    
    def clean_email(self):
        """Field-specific validation method"""
        email = self.email.lower().strip()
        if User.filter(email=email).exclude(id=self.id).exists():
            raise ValueError("Email already exists")
        return email
    
    def clean(self):
        """Model-wide validation"""
        if self.age < 13 and not self.parent_consent:
            raise ValueError("Users under 13 require parent consent")
```

### Custom Validation

```python
from pyframe.validation import ValidationError

class CustomValidator:
    def __init__(self, min_length=8):
        self.min_length = min_length
    
    def __call__(self, value):
        if len(value) < self.min_length:
            raise ValidationError(f"Must be at least {self.min_length} characters")
        
        if not any(c.isupper() for c in value):
            raise ValidationError("Must contain uppercase letter")
        
        return value

class User(Model):
    password = Field(FieldType.STRING, validators=[CustomValidator(10)])
```

---

## Database Operations

### Raw SQL

```python
# Raw queries when ORM isn't sufficient
users = await User.raw(
    "SELECT * FROM users WHERE age > %s AND created_at > %s",
    [18, datetime.now() - timedelta(days=30)]
)

# Raw SQL with parameters
result = await User.execute_sql(
    "UPDATE users SET last_login = %s WHERE id = %s",
    [datetime.now(), user_id]
)
```

### Transactions

```python
from pyframe.database import transaction

async with transaction():
    user = await User.create(name='John', email='john@example.com')
    profile = await UserProfile.create(user=user, bio='Developer')
    await send_welcome_email(user.email)
    # All operations committed together, or all rolled back on error

# Decorator syntax
@transaction
async def create_user_with_profile(name, email, bio):
    user = await User.create(name=name, email=email)
    await UserProfile.create(user=user, bio=bio)
    return user
```

This completes the Model API reference. The PyFrame ORM provides a powerful yet intuitive interface for database operations! 🗄️
