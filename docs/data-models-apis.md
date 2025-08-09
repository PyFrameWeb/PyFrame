# Data Models and APIs

PyFrame's data layer provides a powerful ORM with automatic API generation, making it easy to build data-driven applications without boilerplate code.

## 💾 Model Basics

### Defining Models

```python
from pyframe import Model, Field, FieldType

class User(Model):
    # Basic fields
    name = Field(FieldType.STRING, max_length=100, required=True)
    email = Field(FieldType.EMAIL, unique=True, required=True)
    age = Field(FieldType.INTEGER, min_value=0, max_value=150)
    
    # Advanced fields
    created_at = Field(FieldType.DATETIME, auto_now_add=True)
    updated_at = Field(FieldType.DATETIME, auto_now=True)
    is_active = Field(FieldType.BOOLEAN, default=True)
    
    # Optional fields
    bio = Field(FieldType.TEXT, null=True, blank=True)
    avatar_url = Field(FieldType.URL, null=True)
    
    class Meta:
        table_name = 'users'
        indexes = ['email', 'created_at']
        unique_together = [('name', 'email')]

class Post(Model):
    title = Field(FieldType.STRING, max_length=200, required=True)
    slug = Field(FieldType.SLUG, unique=True, auto_generate=True)
    content = Field(FieldType.TEXT, required=True)
    author = Field(FieldType.FOREIGN_KEY, to=User, on_delete='CASCADE')
    tags = Field(FieldType.MANY_TO_MANY, to='Tag')
    published = Field(FieldType.BOOLEAN, default=False)
    published_at = Field(FieldType.DATETIME, null=True)
    view_count = Field(FieldType.INTEGER, default=0)
    
    class Meta:
        table_name = 'posts'
        ordering = ['-published_at', '-created_at']
```

### Field Types

```python
# String fields
name = Field(FieldType.STRING, max_length=100)
email = Field(FieldType.EMAIL)
url = Field(FieldType.URL)
slug = Field(FieldType.SLUG, auto_generate=True)

# Numeric fields
age = Field(FieldType.INTEGER, min_value=0, max_value=120)
price = Field(FieldType.DECIMAL, max_digits=10, decimal_places=2)
rating = Field(FieldType.FLOAT, min_value=0.0, max_value=5.0)

# Date and time
created_at = Field(FieldType.DATETIME, auto_now_add=True)
updated_at = Field(FieldType.DATETIME, auto_now=True)
birth_date = Field(FieldType.DATE)
login_time = Field(FieldType.TIME)

# Binary and JSON
is_active = Field(FieldType.BOOLEAN, default=True)
profile_data = Field(FieldType.JSON, default=dict)
file_content = Field(FieldType.BINARY)

# Relationships
author = Field(FieldType.FOREIGN_KEY, to=User)
tags = Field(FieldType.MANY_TO_MANY, to='Tag')
profile = Field(FieldType.ONE_TO_ONE, to='UserProfile')

# Advanced fields
uuid_id = Field(FieldType.UUID, primary_key=True)
choices_field = Field(FieldType.CHOICE, choices=[
    ('small', 'Small'),
    ('medium', 'Medium'), 
    ('large', 'Large')
])
```

## 🔍 Querying Data

### Basic Queries

```python
# Get all records
users = await User.all()

# Get a single record
user = await User.get(id=1)
user = await User.get(email='john@example.com')

# Filter records
active_users = await User.filter(is_active=True)
recent_posts = await Post.filter(created_at__gte=datetime.now() - timedelta(days=7))

# Complex filtering
published_posts = await Post.filter(
    published=True,
    author__is_active=True,
    created_at__year=2024
)

# Exclude records
non_admin_users = await User.exclude(is_admin=True)

# Count records
user_count = await User.count()
published_count = await Post.filter(published=True).count()

# Check existence
user_exists = await User.filter(email='test@example.com').exists()
```

### Advanced Queries

```python
# Ordering
users = await User.order_by('name')  # Ascending
users = await User.order_by('-created_at')  # Descending
users = await User.order_by('name', '-created_at')  # Multiple fields

# Limiting results
latest_posts = await Post.order_by('-created_at').limit(10)
paginated_users = await User.offset(20).limit(10)

# Select related (joins)
posts_with_authors = await Post.select_related('author').all()
users_with_profiles = await User.select_related('profile').all()

# Prefetch related (for many-to-many)
posts_with_tags = await Post.prefetch_related('tags').all()

# Aggregation
from pyframe.models import Count, Sum, Avg, Max, Min

stats = await Post.aggregate(
    total_posts=Count('id'),
    avg_views=Avg('view_count'),
    max_views=Max('view_count'),
    total_views=Sum('view_count')
)

# Group by
post_counts_by_author = await Post.values('author').annotate(
    post_count=Count('id')
)

# Raw SQL when needed
users = await User.raw('SELECT * FROM users WHERE age > %s', [18])
```

### Query Filters

```python
# Exact match
User.filter(name='John')

# Case-insensitive
User.filter(name__iexact='john')

# Contains
User.filter(name__contains='Jo')
User.filter(name__icontains='jo')  # Case-insensitive

# Starts/ends with
User.filter(name__startswith='J')
User.filter(email__endswith='@gmail.com')

# Null checks
User.filter(bio__isnull=True)
User.filter(bio__isnull=False)

# Numeric comparisons
User.filter(age__gt=18)  # Greater than
User.filter(age__gte=18)  # Greater than or equal
User.filter(age__lt=65)  # Less than
User.filter(age__lte=65)  # Less than or equal

# Range
User.filter(age__range=(18, 65))

# In list
User.filter(id__in=[1, 2, 3, 4, 5])

# Date/time filters
Post.filter(created_at__date=date.today())
Post.filter(created_at__year=2024)
Post.filter(created_at__month=1)
Post.filter(created_at__day=15)

# Relationship filters
Post.filter(author__name='John')
Post.filter(author__email__endswith='@gmail.com')
```

## ✏️ Creating and Updating Data

### Creating Records

```python
# Create a single record
user = await User.create(
    name='John Doe',
    email='john@example.com',
    age=30
)

# Create with related objects
post = await Post.create(
    title='My First Post',
    content='Hello world!',
    author=user,
    published=True
)

# Bulk create
users = await User.bulk_create([
    User(name='Alice', email='alice@example.com'),
    User(name='Bob', email='bob@example.com'),
    User(name='Charlie', email='charlie@example.com')
])

# Get or create
user, created = await User.get_or_create(
    email='john@example.com',
    defaults={'name': 'John Doe', 'age': 30}
)

if created:
    print('New user created')
else:
    print('User already existed')
```

### Updating Records

```python
# Update a single record
user = await User.get(id=1)
user.age = 31
await user.save()

# Update specific fields only
await user.save(update_fields=['age'])

# Update multiple records
await User.filter(is_active=False).update(is_active=True)

# Bulk update with different values
users = await User.filter(age__isnull=True)
for user in users:
    user.age = calculate_age(user.birth_date)
await User.bulk_update(users, ['age'])

# Atomic updates
from pyframe.models import F

# Increment view count
await Post.filter(id=post_id).update(view_count=F('view_count') + 1)

# Update with expressions
await User.filter(created_at__lt=datetime.now() - timedelta(days=30)).update(
    is_verified=True
)
```

### Deleting Records

```python
# Delete a single record
user = await User.get(id=1)
await user.delete()

# Delete multiple records
await User.filter(is_active=False).delete()

# Soft delete (if configured)
await user.soft_delete()

# Restore soft-deleted records
await user.restore()

# Bulk delete
await Post.filter(published=False, created_at__lt=old_date).delete()
```

## 🔗 Relationships

### Foreign Keys

```python
class Author(Model):
    name = Field(FieldType.STRING, max_length=100)

class Book(Model):
    title = Field(FieldType.STRING, max_length=200)
    author = Field(FieldType.FOREIGN_KEY, to=Author, on_delete='CASCADE')

# Using relationships
author = await Author.create(name='J.K. Rowling')
book = await Book.create(title='Harry Potter', author=author)

# Access related objects
print(book.author.name)  # J.K. Rowling

# Reverse relationship
books = await author.books.all()  # All books by this author

# Filter by relationship
fantasy_books = await Book.filter(author__name__contains='Tolkien')
```

### Many-to-Many

```python
class Tag(Model):
    name = Field(FieldType.STRING, max_length=50, unique=True)

class Post(Model):
    title = Field(FieldType.STRING, max_length=200)
    tags = Field(FieldType.MANY_TO_MANY, to=Tag)

# Create and associate
post = await Post.create(title='Python Tips')
python_tag = await Tag.create(name='Python')
tutorial_tag = await Tag.create(name='Tutorial')

# Add tags
await post.tags.add(python_tag, tutorial_tag)

# Remove tags
await post.tags.remove(python_tag)

# Set tags (replaces all existing)
await post.tags.set([tutorial_tag])

# Get all tags for a post
tags = await post.tags.all()

# Get all posts with a specific tag
python_posts = await python_tag.posts.all()

# Filter by many-to-many
tagged_posts = await Post.filter(tags__name='Python')
```

### One-to-One

```python
class UserProfile(Model):
    user = Field(FieldType.ONE_TO_ONE, to=User, on_delete='CASCADE')
    bio = Field(FieldType.TEXT)
    website = Field(FieldType.URL, null=True)
    location = Field(FieldType.STRING, max_length=100)

# Create profile
user = await User.get(id=1)
profile = await UserProfile.create(
    user=user,
    bio='Python developer',
    location='San Francisco'
)

# Access profile
print(user.profile.bio)

# Reverse access
print(profile.user.name)
```

## 🚀 Automatic API Generation

PyFrame automatically generates REST APIs for your models.

### Auto-Generated Endpoints

```python
class Product(Model):
    name = Field(FieldType.STRING, max_length=100)
    price = Field(FieldType.DECIMAL, max_digits=10, decimal_places=2)
    category = Field(FieldType.FOREIGN_KEY, to='Category')
    in_stock = Field(FieldType.BOOLEAN, default=True)

# Automatically creates these endpoints:
# GET    /api/products/         - List all products
# POST   /api/products/         - Create new product
# GET    /api/products/{id}/    - Get specific product
# PUT    /api/products/{id}/    - Update product
# PATCH  /api/products/{id}/    - Partial update
# DELETE /api/products/{id}/    - Delete product
```

### Customizing APIs

```python
from pyframe.api import ModelAPI, api_method

class ProductAPI(ModelAPI):
    model = Product
    
    # Customize which fields are included
    fields = ['id', 'name', 'price', 'category', 'in_stock']
    
    # Read-only fields
    read_only_fields = ['id', 'created_at']
    
    # Custom filtering
    filter_fields = ['category', 'in_stock', 'price__gte', 'price__lte']
    
    # Custom ordering
    ordering_fields = ['name', 'price', 'created_at']
    default_ordering = ['-created_at']
    
    # Pagination
    page_size = 20
    max_page_size = 100
    
    # Permissions
    def has_permission(self, request, action):
        if action in ['create', 'update', 'delete']:
            return request.user and request.user.is_staff
        return True
    
    # Custom validation
    def validate_price(self, value):
        if value <= 0:
            raise ValueError('Price must be positive')
        return value
    
    # Custom methods
    @api_method(methods=['POST'])
    async def mark_out_of_stock(self, request, pk):
        product = await self.get_object(pk)
        product.in_stock = False
        await product.save()
        return {'message': 'Product marked as out of stock'}
    
    @api_method(methods=['GET'])
    async def search(self, request):
        query = request.query_params.get('q', '')
        products = await Product.filter(
            name__icontains=query
        ).order_by('name')
        
        return {
            'results': [p.to_dict() for p in products],
            'count': len(products)
        }

# Register the API
app.register_api('/api/', ProductAPI)
```

### API Response Format

```python
# GET /api/products/
{
    "count": 150,
    "next": "/api/products/?page=2",
    "previous": null,
    "results": [
        {
            "id": 1,
            "name": "Python Programming Book",
            "price": "29.99",
            "category": {
                "id": 1,
                "name": "Books"
            },
            "in_stock": true,
            "created_at": "2024-01-15T10:30:00Z"
        }
    ]
}

# POST /api/products/
{
    "id": 2,
    "name": "New Product",
    "price": "19.99",
    "category": 1,
    "in_stock": true,
    "created_at": "2024-01-15T11:00:00Z"
}

# Error responses
{
    "error": "Validation failed",
    "details": {
        "price": ["This field is required"],
        "name": ["Ensure this value has at most 100 characters"]
    }
}
```

### API Authentication

```python
from pyframe.auth import api_key_required, jwt_required

class SecureProductAPI(ModelAPI):
    model = Product
    
    # Require API key for all endpoints
    decorators = [api_key_required]
    
    # Or use JWT authentication
    decorators = [jwt_required]
    
    def has_object_permission(self, request, obj, action):
        # Only allow users to modify their own products
        if action in ['update', 'delete']:
            return obj.owner == request.user
        return True

# Custom authentication
@app.api_route('/api/protected')
async def protected_endpoint(context):
    auth_header = context.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return {'error': 'Authentication required'}, 401
    
    token = auth_header[7:]  # Remove 'Bearer ' prefix
    user = await verify_jwt_token(token)
    
    if not user:
        return {'error': 'Invalid token'}, 401
    
    return {'message': f'Hello {user.name}', 'user_id': user.id}
```

## 🔧 Advanced Features

### Model Validation

```python
class User(Model):
    name = Field(FieldType.STRING, max_length=100)
    email = Field(FieldType.EMAIL)
    age = Field(FieldType.INTEGER)
    
    def clean(self):
        # Custom validation logic
        if self.age < 0:
            raise ValueError('Age cannot be negative')
        
        if '@' not in self.email:
            raise ValueError('Invalid email format')
    
    def clean_name(self):
        # Field-specific validation
        if len(self.name.strip()) < 2:
            raise ValueError('Name must be at least 2 characters')
        return self.name.strip().title()
    
    async def validate_unique_email(self):
        # Async validation
        existing = await User.filter(
            email=self.email
        ).exclude(id=self.id).exists()
        
        if existing:
            raise ValueError('Email already exists')
```

### Database Migrations

```python
# migrations/001_initial.py
from pyframe.migrations import Migration, operations

class Migration(Migration):
    dependencies = []
    
    operations = [
        operations.CreateModel(
            name='User',
            fields=[
                ('id', Field(FieldType.AUTO_FIELD, primary_key=True)),
                ('name', Field(FieldType.STRING, max_length=100)),
                ('email', Field(FieldType.EMAIL, unique=True)),
                ('created_at', Field(FieldType.DATETIME, auto_now_add=True)),
            ]
        ),
    ]

# migrations/002_add_user_profile.py
class Migration(Migration):
    dependencies = [('001_initial',)]
    
    operations = [
        operations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', Field(FieldType.AUTO_FIELD, primary_key=True)),
                ('user', Field(FieldType.ONE_TO_ONE, to='User')),
                ('bio', Field(FieldType.TEXT, null=True)),
            ]
        ),
        operations.AddField(
            model_name='User',
            name='is_active',
            field=Field(FieldType.BOOLEAN, default=True)
        ),
    ]
```

### Model Managers

```python
class PublishedManager:
    def get_queryset(self):
        return super().get_queryset().filter(published=True)

class Post(Model):
    title = Field(FieldType.STRING, max_length=200)
    content = Field(FieldType.TEXT)
    published = Field(FieldType.BOOLEAN, default=False)
    
    # Default manager
    objects = Manager()
    
    # Custom manager
    published = PublishedManager()

# Usage
all_posts = await Post.objects.all()
published_posts = await Post.published.all()
```

### Signals and Hooks

```python
from pyframe.signals import pre_save, post_save, pre_delete

@pre_save(User)
async def hash_password(sender, instance, **kwargs):
    if instance.password and not instance.password.startswith('hashed:'):
        instance.password = f'hashed:{hash_password(instance.password)}'

@post_save(Post)
async def update_search_index(sender, instance, created, **kwargs):
    if created:
        await add_to_search_index(instance)
    else:
        await update_search_index(instance)

@pre_delete(User)
async def cleanup_user_data(sender, instance, **kwargs):
    # Clean up related data before deletion
    await UserProfile.filter(user=instance).delete()
    await Post.filter(author=instance).update(author=None)
```

## 📚 Best Practices

### 1. Model Design
```python
# Good: Clear, descriptive names
class BlogPost(Model):
    title = Field(FieldType.STRING, max_length=200)
    slug = Field(FieldType.SLUG, unique=True)
    author = Field(FieldType.FOREIGN_KEY, to=User)

# Good: Proper indexing
class Order(Model):
    customer = Field(FieldType.FOREIGN_KEY, to=User, db_index=True)
    created_at = Field(FieldType.DATETIME, auto_now_add=True, db_index=True)
    status = Field(FieldType.STRING, max_length=20, db_index=True)
    
    class Meta:
        indexes = [
            ('customer', 'status'),
            ('created_at', 'status')
        ]
```

### 2. Query Optimization
```python
# Good: Use select_related for foreign keys
posts = await Post.select_related('author').all()

# Good: Use prefetch_related for many-to-many
posts = await Post.prefetch_related('tags').all()

# Good: Filter early and specifically
recent_published = await Post.filter(
    published=True,
    created_at__gte=last_week
).select_related('author')[:10]
```

### 3. API Security
```python
class UserAPI(ModelAPI):
    model = User
    
    # Don't expose sensitive fields
    fields = ['id', 'name', 'email', 'created_at']
    read_only_fields = ['id', 'created_at']
    
    # Implement proper permissions
    def has_permission(self, request, action):
        if action == 'create':
            return True  # Anyone can register
        return request.user.is_authenticated
    
    def has_object_permission(self, request, obj, action):
        # Users can only modify their own profile
        return obj == request.user or request.user.is_admin
```

## 📚 Next Steps

- [Real-Time Features](realtime-features.md)
- [Advanced Topics](advanced-topics.md)
- [Performance Optimization](performance-optimization.md)
- [Model API Reference](api-reference/model-api.md)

The data layer is the foundation of your PyFrame application - master these concepts and you'll be building robust, scalable applications in no time! 🚀
