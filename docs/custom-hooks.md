# Custom Hooks

PyFrame's hook system provides powerful ways to extend and customize application behavior. Learn how to create and use custom hooks for clean, modular code.

## 🎣 Understanding Hooks

### What are Hooks?

Hooks are functions that run at specific points in your application lifecycle. They allow you to:
- **Extend functionality** without modifying core code
- **Decouple concerns** between different parts of your app
- **Create reusable behaviors** across components
- **Handle side effects** cleanly

### Hook Types

PyFrame provides several types of hooks:

1. **Lifecycle Hooks** - App startup, shutdown, etc.
2. **Request Hooks** - Before/after request processing
3. **Model Hooks** - Database operations
4. **Component Hooks** - UI lifecycle events
5. **Custom Hooks** - Your own business logic hooks

## 🏗️ Creating Custom Hooks

### Basic Hook Definition

```python
from pyframe.hooks import create_hook, use_hook

def use_counter(initial_value=0):
    """Custom hook for counter logic"""
    
    @create_hook
    def counter_hook():
        state = {'count': initial_value}
        
        def increment():
            state['count'] += 1
            return state['count']
        
        def decrement():
            state['count'] -= 1
            return state['count']
        
        def reset():
            state['count'] = initial_value
            return state['count']
        
        return {
            'count': state['count'],
            'increment': increment,
            'decrement': decrement,
            'reset': reset
        }
    
    return counter_hook()

# Usage in component
class CounterComponent(StatefulComponent):
    def __init__(self, **props):
        super().__init__(**props)
        self.counter = use_counter(0)
    
    def render(self):
        return f'''
        <div class="counter">
            <span>Count: {self.counter['count']}</span>
            <button onclick="this.component.increment()">+</button>
            <button onclick="this.component.decrement()">-</button>
            <button onclick="this.component.reset()">Reset</button>
        </div>
        '''
    
    def increment(self):
        new_count = self.counter['increment']()
        self.force_update()
    
    def decrement(self):
        new_count = self.counter['decrement']()
        self.force_update()
    
    def reset(self):
        new_count = self.counter['reset']()
        self.force_update()
```

### Stateful Custom Hooks

```python
from pyframe.hooks import create_hook, use_state, use_effect

def use_api_data(url, dependencies=None):
    """Hook for fetching and managing API data"""
    
    @create_hook
    def api_data_hook():
        data, set_data = use_state(None)
        loading, set_loading = use_state(True)
        error, set_error = use_state(None)
        
        async def fetch_data():
            try:
                set_loading(True)
                set_error(None)
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            result = await response.json()
                            set_data(result)
                        else:
                            set_error(f"HTTP {response.status}")
            
            except Exception as e:
                set_error(str(e))
            finally:
                set_loading(False)
        
        # Fetch data when dependencies change
        use_effect(fetch_data, dependencies or [url])
        
        async def refetch():
            """Manually refetch data"""
            await fetch_data()
        
        return {
            'data': data,
            'loading': loading,
            'error': error,
            'refetch': refetch
        }
    
    return api_data_hook()

# Usage
class UserList(StatefulComponent):
    def __init__(self, **props):
        super().__init__(**props)
        self.user_data = use_api_data('/api/users')
    
    def render(self):
        data = self.user_data['data']
        loading = self.user_data['loading']
        error = self.user_data['error']
        
        if loading:
            return '<div class="loading">Loading users...</div>'
        
        if error:
            return f'''
            <div class="error">
                Error: {error}
                <button onclick="this.component.refetch()">Retry</button>
            </div>
            '''
        
        if not data:
            return '<div>No users found</div>'
        
        user_items = ''.join([
            f'<li>{user["name"]} - {user["email"]}</li>'
            for user in data
        ])
        
        return f'''
        <div class="user-list">
            <button onclick="this.component.refetch()">Refresh</button>
            <ul>{user_items}</ul>
        </div>
        '''
    
    async def refetch(self):
        await self.user_data['refetch']()
        self.force_update()
```

### Local Storage Hook

```python
def use_local_storage(key, default_value=None):
    """Hook for managing localStorage data"""
    
    @create_hook
    def local_storage_hook():
        # Get initial value from localStorage
        def get_stored_value():
            try:
                stored = localStorage.getItem(key)
                return json.loads(stored) if stored else default_value
            except:
                return default_value
        
        value, set_value_state = use_state(get_stored_value())
        
        def set_value(new_value):
            """Set value in both state and localStorage"""
            try:
                localStorage.setItem(key, json.dumps(new_value))
                set_value_state(new_value)
            except Exception as e:
                print(f"Failed to save to localStorage: {e}")
        
        def remove_value():
            """Remove value from localStorage and reset to default"""
            try:
                localStorage.removeItem(key)
                set_value_state(default_value)
            except Exception as e:
                print(f"Failed to remove from localStorage: {e}")
        
        return {
            'value': value,
            'set_value': set_value,
            'remove_value': remove_value
        }
    
    return local_storage_hook()

# Usage
class UserPreferences(StatefulComponent):
    def __init__(self, **props):
        super().__init__(**props)
        self.theme = use_local_storage('theme', 'light')
        self.language = use_local_storage('language', 'en')
    
    def render(self):
        current_theme = self.theme['value']
        current_language = self.language['value']
        
        return f'''
        <div class="preferences">
            <div class="preference-group">
                <label>Theme:</label>
                <select onchange="this.component.change_theme(this.value)" value="{current_theme}">
                    <option value="light">Light</option>
                    <option value="dark">Dark</option>
                </select>
            </div>
            
            <div class="preference-group">
                <label>Language:</label>
                <select onchange="this.component.change_language(this.value)" value="{current_language}">
                    <option value="en">English</option>
                    <option value="es">Spanish</option>
                    <option value="fr">French</option>
                </select>
            </div>
        </div>
        '''
    
    def change_theme(self, new_theme):
        self.theme['set_value'](new_theme)
        self.force_update()
        
        # Apply theme to document
        self.execute_js(f"document.body.className = 'theme-{new_theme}'")
    
    def change_language(self, new_language):
        self.language['set_value'](new_language)
        self.force_update()
```

### Form Validation Hook

```python
def use_form_validation(initial_values, validation_rules):
    """Hook for form validation and management"""
    
    @create_hook
    def form_validation_hook():
        values, set_values = use_state(initial_values.copy())
        errors, set_errors = use_state({})
        touched, set_touched = use_state({})
        
        def validate_field(field_name, value):
            """Validate a single field"""
            field_errors = []
            rules = validation_rules.get(field_name, [])
            
            for rule in rules:
                if callable(rule):
                    # Custom validation function
                    error = rule(value)
                    if error:
                        field_errors.append(error)
                elif isinstance(rule, dict):
                    # Rule object with type and message
                    rule_type = rule.get('type')
                    message = rule.get('message', f'Invalid {field_name}')
                    
                    if rule_type == 'required' and not value:
                        field_errors.append(message)
                    elif rule_type == 'min_length' and len(str(value)) < rule.get('value', 0):
                        field_errors.append(message)
                    elif rule_type == 'max_length' and len(str(value)) > rule.get('value', 0):
                        field_errors.append(message)
                    elif rule_type == 'email' and value and '@' not in str(value):
                        field_errors.append(message)
                    elif rule_type == 'numeric' and value and not str(value).isdigit():
                        field_errors.append(message)
            
            return field_errors
        
        def validate_all():
            """Validate all fields"""
            all_errors = {}
            for field_name, value in values.items():
                field_errors = validate_field(field_name, value)
                if field_errors:
                    all_errors[field_name] = field_errors
            
            set_errors(all_errors)
            return len(all_errors) == 0
        
        def set_field_value(field_name, value):
            """Set value for a specific field"""
            new_values = values.copy()
            new_values[field_name] = value
            set_values(new_values)
            
            # Validate field if it's been touched
            if touched.get(field_name):
                field_errors = validate_field(field_name, value)
                new_errors = errors.copy()
                if field_errors:
                    new_errors[field_name] = field_errors
                else:
                    new_errors.pop(field_name, None)
                set_errors(new_errors)
        
        def set_field_touched(field_name):
            """Mark field as touched"""
            new_touched = touched.copy()
            new_touched[field_name] = True
            set_touched(new_touched)
            
            # Validate field when touched
            field_errors = validate_field(field_name, values.get(field_name))
            if field_errors:
                new_errors = errors.copy()
                new_errors[field_name] = field_errors
                set_errors(new_errors)
        
        def reset_form():
            """Reset form to initial state"""
            set_values(initial_values.copy())
            set_errors({})
            set_touched({})
        
        def get_field_props(field_name):
            """Get props for form field"""
            return {
                'value': values.get(field_name, ''),
                'error': errors.get(field_name, []),
                'touched': touched.get(field_name, False),
                'onChange': lambda value: set_field_value(field_name, value),
                'onBlur': lambda: set_field_touched(field_name)
            }
        
        return {
            'values': values,
            'errors': errors,
            'touched': touched,
            'is_valid': len(errors) == 0,
            'validate_all': validate_all,
            'set_field_value': set_field_value,
            'set_field_touched': set_field_touched,
            'reset_form': reset_form,
            'get_field_props': get_field_props
        }
    
    return form_validation_hook()

# Usage
class ContactForm(StatefulComponent):
    def __init__(self, **props):
        super().__init__(**props)
        
        initial_values = {
            'name': '',
            'email': '',
            'message': ''
        }
        
        validation_rules = {
            'name': [
                {'type': 'required', 'message': 'Name is required'},
                {'type': 'min_length', 'value': 2, 'message': 'Name must be at least 2 characters'}
            ],
            'email': [
                {'type': 'required', 'message': 'Email is required'},
                {'type': 'email', 'message': 'Please enter a valid email'}
            ],
            'message': [
                {'type': 'required', 'message': 'Message is required'},
                {'type': 'min_length', 'value': 10, 'message': 'Message must be at least 10 characters'}
            ]
        }
        
        self.form = use_form_validation(initial_values, validation_rules)
    
    def render(self):
        name_props = self.form['get_field_props']('name')
        email_props = self.form['get_field_props']('email')
        message_props = self.form['get_field_props']('message')
        
        return f'''
        <form class="contact-form" onsubmit="this.component.submit_form(event)">
            <div class="form-group">
                <label for="name">Name:</label>
                <input type="text" id="name" 
                       value="{name_props['value']}"
                       onchange="this.component.update_field('name', this.value)"
                       onblur="this.component.touch_field('name')"
                       class="{'error' if name_props['error'] and name_props['touched'] else ''}">
                {self.render_field_errors(name_props)}
            </div>
            
            <div class="form-group">
                <label for="email">Email:</label>
                <input type="email" id="email" 
                       value="{email_props['value']}"
                       onchange="this.component.update_field('email', this.value)"
                       onblur="this.component.touch_field('email')"
                       class="{'error' if email_props['error'] and email_props['touched'] else ''}">
                {self.render_field_errors(email_props)}
            </div>
            
            <div class="form-group">
                <label for="message">Message:</label>
                <textarea id="message" 
                          onchange="this.component.update_field('message', this.value)"
                          onblur="this.component.touch_field('message')"
                          class="{'error' if message_props['error'] and message_props['touched'] else ''}">{message_props['value']}</textarea>
                {self.render_field_errors(message_props)}
            </div>
            
            <div class="form-actions">
                <button type="submit" {'disabled' if not self.form['is_valid'] else ''}>
                    Send Message
                </button>
                <button type="button" onclick="this.component.reset_form()">
                    Reset
                </button>
            </div>
        </form>
        '''
    
    def render_field_errors(self, field_props):
        if field_props['error'] and field_props['touched']:
            error_items = ''.join([
                f'<li>{error}</li>'
                for error in field_props['error']
            ])
            return f'<ul class="field-errors">{error_items}</ul>'
        return ''
    
    def update_field(self, field_name, value):
        self.form['set_field_value'](field_name, value)
        self.force_update()
    
    def touch_field(self, field_name):
        self.form['set_field_touched'](field_name)
        self.force_update()
    
    async def submit_form(self, event):
        event.preventDefault()
        
        if self.form['validate_all']():
            # Form is valid, submit data
            values = self.form['values']
            success = await self.send_contact_message(values)
            
            if success:
                self.form['reset_form']()
                self.show_success_message()
            else:
                self.show_error_message()
        
        self.force_update()
    
    def reset_form(self):
        self.form['reset_form']()
        self.force_update()
```

## 🔗 Advanced Hook Patterns

### Hook Composition

```python
def use_user_data(user_id):
    """Composed hook using multiple other hooks"""
    
    # Use API data hook
    user_api = use_api_data(f'/api/users/{user_id}')
    
    # Use local storage for caching
    cached_user = use_local_storage(f'user_{user_id}', None)
    
    # Use state for derived data
    display_name, set_display_name = use_state('')
    
    # Update display name when user data changes
    use_effect(lambda: (
        set_display_name(
            user_api['data']['display_name'] if user_api['data'] 
            else cached_user['value']['display_name'] if cached_user['value']
            else 'Unknown User'
        )
    ), [user_api['data'], cached_user['value']])
    
    # Cache user data when loaded
    use_effect(lambda: (
        cached_user['set_value'](user_api['data'])
        if user_api['data'] and not user_api['loading']
        else None
    ), [user_api['data'], user_api['loading']])
    
    return {
        'user': user_api['data'] or cached_user['value'],
        'display_name': display_name,
        'loading': user_api['loading'],
        'error': user_api['error'],
        'refetch': user_api['refetch']
    }
```

### Conditional Hooks

```python
def use_conditional_effect(effect, condition, dependencies=None):
    """Hook that only runs effect when condition is true"""
    
    @create_hook
    def conditional_effect_hook():
        use_effect(
            lambda: effect() if condition else None,
            dependencies
        )
    
    return conditional_effect_hook()

# Usage
class ConditionalComponent(StatefulComponent):
    def __init__(self, **props):
        super().__init__(**props)
        self.user_id = props.get('user_id')
        
        # Only fetch data if user_id is provided
        use_conditional_effect(
            lambda: self.fetch_user_data(),
            condition=bool(self.user_id),
            dependencies=[self.user_id]
        )
```

### Custom Hook with Cleanup

```python
def use_websocket(url):
    """Hook for managing WebSocket connections"""
    
    @create_hook
    def websocket_hook():
        connection, set_connection = use_state(None)
        messages, set_messages = use_state([])
        connected, set_connected = use_state(False)
        
        async def connect():
            try:
                ws = await websockets.connect(url)
                set_connection(ws)
                set_connected(True)
                
                # Listen for messages
                async for message in ws:
                    data = json.loads(message)
                    set_messages(prev => [...prev, data])
            
            except Exception as e:
                print(f"WebSocket error: {e}")
                set_connected(False)
        
        async def send_message(message):
            if connection and connected:
                await connection.send(json.dumps(message))
        
        async def disconnect():
            if connection:
                await connection.close()
                set_connection(None)
                set_connected(False)
        
        # Connect on mount, disconnect on unmount
        use_effect(lambda: (
            asyncio.create_task(connect()),
            disconnect  # Cleanup function
        ), [url])
        
        return {
            'connected': connected,
            'messages': messages,
            'send_message': send_message,
            'disconnect': disconnect
        }
    
    return websocket_hook()
```

## 🎯 Hook Best Practices

### 1. Naming Convention

```python
# Good: Use "use_" prefix
def use_auth():
    pass

def use_api_data():
    pass

# Bad: Don't use "use_" prefix for non-hooks
def fetch_data():  # Not a hook
    pass
```

### 2. Hook Dependencies

```python
# Good: Specify dependencies correctly
def use_user_posts(user_id):
    posts, set_posts = use_state([])
    
    use_effect(
        lambda: fetch_posts(user_id),
        [user_id]  # Re-run when user_id changes
    )

# Bad: Missing or incorrect dependencies
def use_user_posts(user_id):
    posts, set_posts = use_state([])
    
    use_effect(
        lambda: fetch_posts(user_id),
        []  # Won't update when user_id changes!
    )
```

### 3. Error Handling

```python
def use_safe_api_call(url):
    """Hook with proper error handling"""
    
    @create_hook
    def safe_api_hook():
        data, set_data = use_state(None)
        error, set_error = use_state(None)
        loading, set_loading = use_state(False)
        
        async def fetch_data():
            try:
                set_loading(True)
                set_error(None)
                
                result = await api_call(url)
                set_data(result)
            
            except Exception as e:
                set_error(str(e))
                set_data(None)
            
            finally:
                set_loading(False)
        
        return {
            'data': data,
            'error': error,
            'loading': loading,
            'refetch': fetch_data
        }
    
    return safe_api_hook()
```

### 4. Performance Optimization

```python
def use_memoized_computation(compute_fn, dependencies):
    """Hook that memoizes expensive computations"""
    
    @create_hook
    def memoized_computation_hook():
        result, set_result = use_state(None)
        
        use_effect(
            lambda: set_result(compute_fn()),
            dependencies
        )
        
        return result
    
    return memoized_computation_hook()

# Usage
class ExpensiveComponent(StatefulComponent):
    def __init__(self, **props):
        super().__init__(**props)
        self.data = props.get('data', [])
        
        # Expensive computation is memoized
        self.processed_data = use_memoized_computation(
            lambda: self.process_large_dataset(self.data),
            [len(self.data), self.data[0] if self.data else None]
        )
```

Custom hooks are powerful tools for creating reusable, composable functionality in PyFrame applications. Use them to encapsulate complex logic and make your components cleaner! 🎣
