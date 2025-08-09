"""
Reactive Component System

Implements the core component architecture with reactive state management,
lifecycle hooks, and Python-to-JS compilation support.
"""

import json
import weakref
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable, Union, Type, TypeVar
from dataclasses import dataclass, field
from enum import Enum

T = TypeVar('T')


class ComponentLifecycle(Enum):
    """Component lifecycle stages"""
    CREATED = "created"
    MOUNTED = "mounted" 
    UPDATED = "updated"
    UNMOUNTED = "unmounted"


@dataclass
class StateChange:
    """Represents a state change event"""
    key: str
    old_value: Any
    new_value: Any
    timestamp: float


class State:
    """
    Reactive state management for components.
    
    Automatically tracks changes and notifies subscribed components
    for re-rendering when state updates occur.
    """
    
    def __init__(self, initial_data: Dict[str, Any] = None):
        self._data = initial_data or {}
        self._subscribers: List[weakref.ref] = []
        self._history: List[StateChange] = []
        
    def __getitem__(self, key: str) -> Any:
        return self._data.get(key)
        
    def __setitem__(self, key: str, value: Any) -> None:
        old_value = self._data.get(key)
        self._data[key] = value
        
        # Record state change
        import time
        change = StateChange(key, old_value, value, time.time())
        self._history.append(change)
        
        # Notify subscribers
        self._notify_subscribers(change)
        
    def __contains__(self, key: str) -> bool:
        return key in self._data
        
    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)
        
    def update(self, updates: Dict[str, Any]) -> None:
        """Update multiple state values at once"""
        for key, value in updates.items():
            self[key] = value
            
    def subscribe(self, component: 'Component') -> None:
        """Subscribe a component to state changes"""
        self._subscribers.append(weakref.ref(component))
        
    def unsubscribe(self, component: 'Component') -> None:
        """Unsubscribe a component from state changes"""
        self._subscribers = [ref for ref in self._subscribers 
                           if ref() is not component]
        
    def _notify_subscribers(self, change: StateChange) -> None:
        """Notify all subscribed components of state change"""
        # Clean up dead references
        alive_refs = []
        for ref in self._subscribers:
            component = ref()
            if component is not None:
                alive_refs.append(ref)
                component._handle_state_change(change)
        self._subscribers = alive_refs
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert state to dictionary for serialization"""
        return self._data.copy()
        
    def to_json(self) -> str:
        """Convert state to JSON for client-side hydration"""
        return json.dumps(self._data, default=str)


class Component(ABC):
    """
    Base class for all PyFrame components.
    
    Provides reactive rendering, state management, lifecycle hooks,
    and compilation to JavaScript for client-side execution.
    """
    
    def __init__(self, props: Dict[str, Any] = None, children: List['Component'] = None):
        self.props = props or {}
        self.children = children or []
        self.state = State()
        self.state.subscribe(self)
        
        # Component metadata
        self._id = id(self)
        self._mounted = False
        self._needs_update = False
        self._lifecycle_hooks: Dict[ComponentLifecycle, List[Callable]] = {
            lifecycle: [] for lifecycle in ComponentLifecycle
        }
        
        # Call lifecycle hook
        self._call_lifecycle_hook(ComponentLifecycle.CREATED)
        
    @abstractmethod
    def render(self) -> str:
        """
        Render the component to HTML string.
        
        This method will be transpiled to JavaScript for client-side rendering.
        Must return valid HTML as a string.
        """
        pass
        
    def mount(self) -> None:
        """Mount the component (called when added to DOM)"""
        if not self._mounted:
            self._mounted = True
            self._call_lifecycle_hook(ComponentLifecycle.MOUNTED)
            
    def unmount(self) -> None:
        """Unmount the component (called when removed from DOM)"""
        if self._mounted:
            self._mounted = False
            self.state.unsubscribe(self)
            self._call_lifecycle_hook(ComponentLifecycle.UNMOUNTED)
            
    def update(self, new_props: Dict[str, Any] = None) -> None:
        """Update component with new props"""
        if new_props:
            self.props.update(new_props)
        self._needs_update = True
        self._call_lifecycle_hook(ComponentLifecycle.UPDATED)
        
    def _handle_state_change(self, change: StateChange) -> None:
        """Handle state change from subscribed state object"""
        self._needs_update = True
        # In a real implementation, this would trigger re-rendering
        
    def add_lifecycle_hook(self, lifecycle: ComponentLifecycle, 
                          callback: Callable) -> None:
        """Add a lifecycle hook callback"""
        self._lifecycle_hooks[lifecycle].append(callback)
        
    def _call_lifecycle_hook(self, lifecycle: ComponentLifecycle) -> None:
        """Call all registered hooks for a lifecycle stage"""
        for hook in self._lifecycle_hooks[lifecycle]:
            hook()
            
    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary for serialization"""
        return {
            "id": self._id,
            "type": self.__class__.__name__,
            "props": self.props,
            "state": self.state.to_dict(),
            "children": [child.to_dict() for child in self.children]
        }
        
    def to_js(self) -> str:
        """
        Convert component to JavaScript representation.
        
        This is a basic implementation - in practice, this would use
        the full Python-to-JS transpiler.
        """
        return f"""
class {self.__class__.__name__} extends PyFrameComponent {{
    constructor(props, children) {{
        super(props, children);
        this.state = new PyFrameState({self.state.to_json()});
    }}
    
    render() {{
        // Transpiled render method would go here
        return `{self.render()}`;
    }}
}}
"""


class StatefulComponent(Component):
    """
    A component with built-in state management helpers.
    
    Provides convenient methods for common state operations.
    """
    
    def set_state(self, key: str, value: Any) -> None:
        """Set a single state value"""
        self.state[key] = value
        
    def get_state(self, key: str, default: Any = None) -> Any:
        """Get a single state value"""
        return self.state.get(key, default)
        
    def merge_state(self, updates: Dict[str, Any]) -> None:
        """Merge multiple state updates"""
        self.state.update(updates)


class FunctionalComponent:
    """
    Decorator to create functional components from Python functions.
    
    Provides a simpler API for stateless components.
    """
    
    def __init__(self, render_func: Callable):
        self.render_func = render_func
        self.__name__ = render_func.__name__
        
    def __call__(self, props: Dict[str, Any] = None, 
                 children: List[Component] = None) -> 'Component':
        """Create a component instance from the function"""
        
        class FuncComponent(Component):
            def render(self) -> str:
                return render_func(self.props, self.children)
                
        return FuncComponent(props, children)


def component(func: Callable) -> FunctionalComponent:
    """Decorator to convert a function into a functional component"""
    return FunctionalComponent(func)


# Example components demonstrating the system

class Button(StatefulComponent):
    """Example button component with click handling"""
    
    def __init__(self, props: Dict[str, Any] = None, children: List[Component] = None):
        super().__init__(props, children)
        self.set_state("clicks", 0)
        
    def handle_click(self) -> None:
        """Handle button click event"""
        clicks = self.get_state("clicks", 0)
        self.set_state("clicks", clicks + 1)
        
        # Call custom click handler if provided
        if "onClick" in self.props:
            self.props["onClick"]()
            
    def render(self) -> str:
        """Render button component"""
        class_name = self.props.get("className", "")
        disabled = self.props.get("disabled", False)
        text = self.props.get("text", "Click me")
        clicks = self.get_state("clicks", 0)
        
        disabled_attr = "disabled" if disabled else ""
        
        return f"""
        <button class="{class_name}" {disabled_attr} 
                onclick="this.component.handle_click()">
            {text} (clicked {clicks} times)
        </button>
        """


@component
def HelloWorld(props: Dict[str, Any], children: List[Component]) -> str:
    """Example functional component"""
    name = props.get("name", "World")
    return f"<h1>Hello, {name}!</h1>"


class List(StatefulComponent):
    """Example list component with dynamic items"""
    
    def __init__(self, props: Dict[str, Any] = None, children: List[Component] = None):
        super().__init__(props, children)
        self.set_state("items", props.get("items", []))
        
    def add_item(self, item: str) -> None:
        """Add an item to the list"""
        items = self.get_state("items", [])
        items.append(item)
        self.set_state("items", items)
        
    def remove_item(self, index: int) -> None:
        """Remove an item from the list"""
        items = self.get_state("items", [])
        if 0 <= index < len(items):
            items.pop(index)
            self.set_state("items", items)
            
    def render(self) -> str:
        """Render list component"""
        items = self.get_state("items", [])
        class_name = self.props.get("className", "")
        
        items_html = ""
        for i, item in enumerate(items):
            items_html += f"""
            <li>
                {item}
                <button onclick="this.component.remove_item({i})">Remove</button>
            </li>
            """
            
        return f"""
        <div class="{class_name}">
            <ul>{items_html}</ul>
            <button onclick="this.component.add_item(prompt('Enter item:'))">
                Add Item
            </button>
        </div>
        """
