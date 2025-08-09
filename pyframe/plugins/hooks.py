"""
Hook Management System

Provides decorators and utilities for registering hooks and
middleware functions that integrate with the plugin system.
"""

import functools
from typing import Callable, Dict, Any, Optional, List
from .plugin import HookType, PluginHook


class HookManager:
    """
    Global hook manager for registering and executing hooks.
    
    Provides a centralized system for managing application hooks
    that can be used by plugins and core framework code.
    """
    
    def __init__(self):
        self.global_hooks: Dict[HookType, List[PluginHook]] = {}
        
    def register_global_hook(self, hook_type: HookType, callback: Callable,
                           priority: int = 100, conditions: Dict[str, Any] = None) -> PluginHook:
        """Register a global hook (not tied to a specific plugin)"""
        
        hook = PluginHook(hook_type, callback, priority, conditions)
        hook.plugin_name = "global"
        
        if hook_type not in self.global_hooks:
            self.global_hooks[hook_type] = []
            
        self.global_hooks[hook_type].append(hook)
        
        # Sort by priority
        self.global_hooks[hook_type].sort(key=lambda h: h.priority)
        
        return hook
        
    async def execute_global_hooks(self, hook_type: HookType, context: Dict[str, Any],
                                 *args, **kwargs) -> List[Any]:
        """Execute global hooks of a specific type"""
        results = []
        
        if hook_type in self.global_hooks:
            for hook in self.global_hooks[hook_type]:
                try:
                    result = await hook.execute(context, *args, **kwargs)
                    results.append(result)
                except Exception as e:
                    print(f"Error executing global hook {hook_type.value}: {e}")
                    
        return results


# Global hook manager instance
hook_manager = HookManager()


def hook(hook_type: HookType, priority: int = 100, 
         conditions: Dict[str, Any] = None):
    """
    Decorator to register a function as a hook.
    
    Usage:
        @hook(HookType.BEFORE_REQUEST)
        async def my_hook(context, *args, **kwargs):
            # Hook implementation
            pass
    """
    
    def decorator(func: Callable) -> Callable:
        hook_manager.register_global_hook(hook_type, func, priority, conditions)
        return func
        
    return decorator


def before(event_type: str, priority: int = 100, 
           conditions: Dict[str, Any] = None):
    """
    Decorator for 'before' hooks.
    
    Usage:
        @before("request")
        async def before_request(context, *args, **kwargs):
            # Pre-processing logic
            pass
    """
    
    # Map event types to hook types
    hook_type_map = {
        "request": HookType.BEFORE_REQUEST,
        "render": HookType.BEFORE_RENDER,
        "component_mount": HookType.BEFORE_COMPONENT_MOUNT,
        "state_change": HookType.BEFORE_STATE_CHANGE,
        "model_save": HookType.BEFORE_MODEL_SAVE
    }
    
    hook_type = hook_type_map.get(event_type, HookType.CUSTOM)
    
    return hook(hook_type, priority, conditions)


def after(event_type: str, priority: int = 100,
          conditions: Dict[str, Any] = None):
    """
    Decorator for 'after' hooks.
    
    Usage:
        @after("request")
        async def after_request(context, *args, **kwargs):
            # Post-processing logic
            pass
    """
    
    # Map event types to hook types
    hook_type_map = {
        "request": HookType.AFTER_REQUEST,
        "render": HookType.AFTER_RENDER,
        "component_mount": HookType.AFTER_COMPONENT_MOUNT,
        "state_change": HookType.AFTER_STATE_CHANGE,
        "model_save": HookType.AFTER_MODEL_SAVE
    }
    
    hook_type = hook_type_map.get(event_type, HookType.CUSTOM)
    
    return hook(hook_type, priority, conditions)


def middleware(priority: int = 100, conditions: Dict[str, Any] = None):
    """
    Decorator to register a middleware function.
    
    Middleware functions are executed before request processing.
    
    Usage:
        @middleware()
        async def my_middleware(context, *args, **kwargs):
            # Middleware logic
            pass
    """
    
    return before("request", priority, conditions)


def component_hook(hook_type: str, priority: int = 100,
                  conditions: Dict[str, Any] = None):
    """
    Decorator for component-specific hooks.
    
    Usage:
        @component_hook("before_mount")
        async def before_component_mount(context, component, *args, **kwargs):
            # Component hook logic
            pass
    """
    
    hook_type_map = {
        "before_mount": HookType.BEFORE_COMPONENT_MOUNT,
        "after_mount": HookType.AFTER_COMPONENT_MOUNT,
        "before_state_change": HookType.BEFORE_STATE_CHANGE,
        "after_state_change": HookType.AFTER_STATE_CHANGE
    }
    
    mapped_hook_type = hook_type_map.get(hook_type, HookType.CUSTOM)
    
    return hook(mapped_hook_type, priority, conditions)


def model_hook(hook_type: str, priority: int = 100,
               conditions: Dict[str, Any] = None):
    """
    Decorator for model-specific hooks.
    
    Usage:
        @model_hook("before_save")
        async def before_model_save(context, model_instance, *args, **kwargs):
            # Model hook logic
            pass
    """
    
    hook_type_map = {
        "before_save": HookType.BEFORE_MODEL_SAVE,
        "after_save": HookType.AFTER_MODEL_SAVE
    }
    
    mapped_hook_type = hook_type_map.get(hook_type, HookType.CUSTOM)
    
    return hook(mapped_hook_type, priority, conditions)


def conditional_hook(hook_type: HookType, condition_func: Callable[[Dict[str, Any]], bool],
                    priority: int = 100):
    """
    Decorator for conditional hooks that only execute when condition is met.
    
    Usage:
        def is_authenticated(context):
            return context.get("user") is not None
            
        @conditional_hook(HookType.BEFORE_REQUEST, is_authenticated)
        async def authenticated_only_hook(context, *args, **kwargs):
            # Only runs for authenticated users
            pass
    """
    
    def decorator(func: Callable) -> Callable:
        
        @functools.wraps(func)
        async def wrapper(context: Dict[str, Any], *args, **kwargs):
            if condition_func(context):
                return await func(context, *args, **kwargs)
            return None
            
        hook_manager.register_global_hook(hook_type, wrapper, priority)
        return func
        
    return decorator


def rate_limited_hook(hook_type: HookType, max_calls: int, window_seconds: int,
                     priority: int = 100):
    """
    Decorator for rate-limited hooks.
    
    Usage:
        @rate_limited_hook(HookType.BEFORE_REQUEST, max_calls=100, window_seconds=60)
        async def rate_limited_hook(context, *args, **kwargs):
            # This hook will only execute up to 100 times per minute
            pass
    """
    
    import time
    from collections import defaultdict, deque
    
    call_history = defaultdict(deque)
    
    def decorator(func: Callable) -> Callable:
        
        @functools.wraps(func)
        async def wrapper(context: Dict[str, Any], *args, **kwargs):
            now = time.time()
            func_id = id(func)
            
            # Clean old entries
            history = call_history[func_id]
            while history and history[0] < now - window_seconds:
                history.popleft()
                
            # Check rate limit
            if len(history) >= max_calls:
                print(f"Rate limit exceeded for hook {func.__name__}")
                return None
                
            # Record call and execute
            history.append(now)
            return await func(context, *args, **kwargs)
            
        hook_manager.register_global_hook(hook_type, wrapper, priority)
        return func
        
    return decorator


def cached_hook(hook_type: HookType, cache_key_func: Callable[[Dict[str, Any]], str],
               ttl_seconds: int = 300, priority: int = 100):
    """
    Decorator for cached hooks that cache results for a specified time.
    
    Usage:
        def cache_key(context):
            return f"user_{context.get('user_id', 'anonymous')}"
            
        @cached_hook(HookType.BEFORE_REQUEST, cache_key, ttl_seconds=300)
        async def cached_hook(context, *args, **kwargs):
            # Result will be cached for 5 minutes per user
            pass
    """
    
    import time
    
    cache = {}
    
    def decorator(func: Callable) -> Callable:
        
        @functools.wraps(func)
        async def wrapper(context: Dict[str, Any], *args, **kwargs):
            cache_key = cache_key_func(context)
            now = time.time()
            
            # Check cache
            if cache_key in cache:
                result, timestamp = cache[cache_key]
                if now - timestamp < ttl_seconds:
                    return result
                    
            # Execute and cache
            result = await func(context, *args, **kwargs)
            cache[cache_key] = (result, now)
            
            # Clean expired entries
            expired_keys = [k for k, (_, ts) in cache.items() 
                          if now - ts >= ttl_seconds]
            for key in expired_keys:
                del cache[key]
                
            return result
            
        hook_manager.register_global_hook(hook_type, wrapper, priority)
        return func
        
    return decorator


# Utility functions for hook execution

async def execute_before_hooks(event_type: str, context: Dict[str, Any],
                             *args, **kwargs) -> List[Any]:
    """Execute 'before' hooks for an event type"""
    
    hook_type_map = {
        "request": HookType.BEFORE_REQUEST,
        "render": HookType.BEFORE_RENDER,
        "component_mount": HookType.BEFORE_COMPONENT_MOUNT,
        "state_change": HookType.BEFORE_STATE_CHANGE,
        "model_save": HookType.BEFORE_MODEL_SAVE
    }
    
    hook_type = hook_type_map.get(event_type, HookType.CUSTOM)
    return await hook_manager.execute_global_hooks(hook_type, context, *args, **kwargs)


async def execute_after_hooks(event_type: str, context: Dict[str, Any],
                            *args, **kwargs) -> List[Any]:
    """Execute 'after' hooks for an event type"""
    
    hook_type_map = {
        "request": HookType.AFTER_REQUEST,
        "render": HookType.AFTER_RENDER,
        "component_mount": HookType.AFTER_COMPONENT_MOUNT,
        "state_change": HookType.AFTER_STATE_CHANGE,
        "model_save": HookType.AFTER_MODEL_SAVE
    }
    
    hook_type = hook_type_map.get(event_type, HookType.CUSTOM)
    return await hook_manager.execute_global_hooks(hook_type, context, *args, **kwargs)


# Example hook implementations

@hook(HookType.BEFORE_REQUEST, priority=50)
async def log_request_hook(context: Dict[str, Any], *args, **kwargs):
    """Example hook that logs incoming requests"""
    request_context = kwargs.get('request_context')
    if request_context:
        print(f"Request: {request_context.method} {request_context.path}")


@hook(HookType.AFTER_REQUEST, priority=50)
async def log_response_hook(context: Dict[str, Any], *args, **kwargs):
    """Example hook that logs response status"""
    response = kwargs.get('response')
    if response:
        status = response.get('status', 'unknown')
        print(f"Response: {status}")


@before("component_mount")
async def component_mount_logger(context: Dict[str, Any], *args, **kwargs):
    """Example hook that logs component mounting"""
    component = kwargs.get('component')
    if component:
        print(f"Mounting component: {component.__class__.__name__}")


@after("model_save")
async def model_save_logger(context: Dict[str, Any], *args, **kwargs):
    """Example hook that logs model saves"""
    model_instance = kwargs.get('model_instance')
    if model_instance:
        print(f"Saved model: {model_instance.__class__.__name__}")


@conditional_hook(
    HookType.BEFORE_REQUEST,
    lambda ctx: ctx.get('method') == 'POST'
)
async def post_request_validator(context: Dict[str, Any], *args, **kwargs):
    """Example conditional hook that only runs for POST requests"""
    print("Validating POST request")


@rate_limited_hook(HookType.BEFORE_REQUEST, max_calls=10, window_seconds=60)
async def rate_limited_logger(context: Dict[str, Any], *args, **kwargs):
    """Example rate-limited hook"""
    print("Rate-limited log entry")


# Hook utilities for testing and debugging

def list_registered_hooks() -> Dict[str, List[str]]:
    """List all registered global hooks"""
    
    hook_list = {}
    
    for hook_type, hooks in hook_manager.global_hooks.items():
        hook_names = [f"{hook.plugin_name}:{hook.callback.__name__}" 
                     for hook in hooks]
        hook_list[hook_type.value] = hook_names
        
    return hook_list


def get_hook_stats() -> Dict[str, Any]:
    """Get statistics about registered hooks"""
    
    total_hooks = sum(len(hooks) for hooks in hook_manager.global_hooks.values())
    hook_counts = {hook_type.value: len(hooks) 
                  for hook_type, hooks in hook_manager.global_hooks.items()}
    
    return {
        "total_hooks": total_hooks,
        "hook_counts": hook_counts
    }
