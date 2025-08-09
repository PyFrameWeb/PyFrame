"""
Python-to-JavaScript Transpiler

Converts Python component code into optimized JavaScript that can run
in browsers while preserving reactive behavior and component semantics.
"""

import ast
import inspect
import re
from typing import Dict, List, Any, Optional, Union, Type
from dataclasses import dataclass

from ..core.component import Component
from .ast_transformer import ASTTransformer
from .js_generator import JSGenerator


@dataclass
class TranspilationResult:
    """Result of transpiling Python code to JavaScript"""
    js_code: str
    source_map: Optional[str] = None
    dependencies: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.warnings is None:
            self.warnings = []


class PythonToJSTranspiler:
    """
    Main transpiler class that converts Python component code to JavaScript.
    
    Handles:
    - Python syntax to JavaScript conversion
    - State management preservation  
    - Event handler binding
    - Template string processing
    - Import/dependency resolution
    """
    
    def __init__(self, minify: bool = False, source_maps: bool = True):
        self.minify = minify
        self.source_maps = source_maps
        self.ast_transformer = ASTTransformer()
        self.js_generator = JSGenerator(minify=minify)
        
        # Built-in Python to JS mappings
        self._builtin_mappings = {
            "len": "length",
            "str": "String",
            "int": "parseInt",
            "float": "parseFloat", 
            "bool": "Boolean",
            "list": "Array",
            "dict": "Object",
            "range": "Array.from({length: %s}, (_, i) => i)",
            "enumerate": "Array.prototype.entries",
            "zip": "Array.prototype.zip",  # Would need polyfill
            "print": "console.log"
        }
        
    def transpile_component(self, component: Union[Component, Type[Component]]) -> TranspilationResult:
        """
        Transpile a component class to JavaScript.
        
        Converts the component's render method and state management 
        to equivalent JavaScript code.
        """
        if isinstance(component, type):
            component_class = component
            # Create a temporary instance to get default state
            temp_instance = component_class()
        else:
            component_class = component.__class__
            temp_instance = component
            
        # Get the source code
        try:
            source = inspect.getsource(component_class)
        except OSError:
            # Fallback for dynamically created classes
            source = self._generate_component_source(component_class)
            
        # Parse into AST
        tree = ast.parse(source)
        
        # Transform the AST
        transformed_tree = self.ast_transformer.visit(tree)
        
        # Generate JavaScript
        js_code = self.js_generator.generate_component_js(
            component_class.__name__,
            transformed_tree,
            temp_instance
        )
        
        return TranspilationResult(
            js_code=js_code,
            dependencies=self._extract_dependencies(tree),
            warnings=self.ast_transformer.warnings
        )
        
    def transpile_function(self, func) -> TranspilationResult:
        """Transpile a standalone Python function to JavaScript"""
        source = inspect.getsource(func)
        tree = ast.parse(source)
        
        transformed_tree = self.ast_transformer.visit(tree)
        js_code = self.js_generator.generate_function_js(func.__name__, transformed_tree)
        
        return TranspilationResult(
            js_code=js_code,
            dependencies=self._extract_dependencies(tree)
        )
        
    def transpile_expression(self, expression: str) -> str:
        """Transpile a Python expression to JavaScript"""
        tree = ast.parse(expression, mode='eval')
        transformed_tree = self.ast_transformer.visit(tree)
        return self.js_generator.generate_expression_js(transformed_tree)
        
    def _generate_component_source(self, component_class: Type[Component]) -> str:
        """Generate source code for dynamically created component classes"""
        # This is a fallback for when inspect.getsource fails
        render_method = getattr(component_class, 'render', None)
        if render_method:
            try:
                render_source = inspect.getsource(render_method)
            except OSError:
                render_source = "def render(self):\n    return '<div>Dynamic Component</div>'"
        else:
            render_source = "def render(self):\n    return '<div>No Render Method</div>'"
            
        return f"""
class {component_class.__name__}:
    def __init__(self, props=None, children=None):
        self.props = props or {{}}
        self.children = children or []
        self.state = {{}}
        
    {render_source}
"""
        
    def _extract_dependencies(self, tree: ast.AST) -> List[str]:
        """Extract import dependencies from AST"""
        dependencies = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    dependencies.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    dependencies.append(node.module)
                    
        return dependencies
        
    def generate_runtime_js(self) -> str:
        """Generate the PyFrame runtime JavaScript code"""
        return """
// PyFrame Runtime - Client-side reactive component system

class PyFrameState {
    constructor(initialData = {}) {
        this._data = { ...initialData };
        this._subscribers = new Set();
        this._history = [];
    }
    
    get(key, defaultValue = null) {
        return this._data.hasOwnProperty(key) ? this._data[key] : defaultValue;
    }
    
    set(key, value) {
        const oldValue = this._data[key];
        this._data[key] = value;
        
        const change = {
            key,
            oldValue,
            newValue: value,
            timestamp: Date.now()
        };
        
        this._history.push(change);
        this._notifySubscribers(change);
    }
    
    update(updates) {
        Object.entries(updates).forEach(([key, value]) => {
            this.set(key, value);
        });
    }
    
    subscribe(component) {
        this._subscribers.add(component);
    }
    
    unsubscribe(component) {
        this._subscribers.delete(component);
    }
    
    _notifySubscribers(change) {
        this._subscribers.forEach(component => {
            if (component._handleStateChange) {
                component._handleStateChange(change);
            }
        });
    }
    
    toJSON() {
        return this._data;
    }
}

class PyFrameComponent {
    constructor(props = {}, children = []) {
        this.props = props;
        this.children = children;
        this.state = new PyFrameState();
        this.state.subscribe(this);
        
        this._id = Math.random().toString(36).substr(2, 9);
        this._mounted = false;
        this._needsUpdate = false;
        this._element = null;
        
        this._lifecycleHooks = {
            created: [],
            mounted: [],
            updated: [],
            unmounted: []
        };
        
        this._callLifecycleHook('created');
    }
    
    render() {
        // Override in subclasses
        return '<div>PyFrame Component</div>';
    }
    
    mount(element) {
        if (!this._mounted) {
            this._mounted = true;
            this._element = element;
            this._bindEventHandlers(element);
            this._callLifecycleHook('mounted');
        }
    }
    
    unmount() {
        if (this._mounted) {
            this._mounted = false;
            this.state.unsubscribe(this);
            this._callLifecycleHook('unmounted');
        }
    }
    
    update(newProps = {}) {
        Object.assign(this.props, newProps);
        this._needsUpdate = true;
        this._callLifecycleHook('updated');
        this._rerender();
    }
    
    _handleStateChange(change) {
        this._needsUpdate = true;
        this._rerender();
    }
    
    _rerender() {
        if (this._element && this._mounted) {
            const newHtml = this.render();
            this._element.innerHTML = newHtml;
            this._bindEventHandlers(this._element);
        }
    }
    
    _bindEventHandlers(element) {
        // Bind component methods to DOM elements
        const self = this;
        element.querySelectorAll('[data-pyframe-handler]').forEach(el => {
            const handlerName = el.getAttribute('data-pyframe-handler');
            const eventType = el.getAttribute('data-pyframe-event') || 'click';
            
            if (typeof self[handlerName] === 'function') {
                el.addEventListener(eventType, (e) => {
                    self[handlerName](e);
                });
            }
        });
        
        // Also bind onclick handlers that reference this.component
        element.querySelectorAll('[onclick*="this.component"]').forEach(el => {
            el.component = this;
        });
    }
    
    addLifecycleHook(lifecycle, callback) {
        if (this._lifecycleHooks[lifecycle]) {
            this._lifecycleHooks[lifecycle].push(callback);
        }
    }
    
    _callLifecycleHook(lifecycle) {
        if (this._lifecycleHooks[lifecycle]) {
            this._lifecycleHooks[lifecycle].forEach(hook => hook.call(this));
        }
    }
    
    setState(key, value) {
        this.state.set(key, value);
    }
    
    getState(key, defaultValue = null) {
        return this.state.get(key, defaultValue);
    }
    
    mergeState(updates) {
        this.state.update(updates);
    }
    
    toJSON() {
        return {
            id: this._id,
            type: this.constructor.name,
            props: this.props,
            state: this.state.toJSON(),
            children: this.children.map(child => 
                child.toJSON ? child.toJSON() : child
            )
        };
    }
}

// Global PyFrame object
window.PyFrame = {
    Component: PyFrameComponent,
    State: PyFrameState,
    
    render(element, data) {
        if (data.component) {
            const ComponentClass = window[data.component.type];
            if (ComponentClass) {
                const component = new ComponentClass(data.component.props, data.component.children);
                component.state._data = data.component.state;
                
                element.innerHTML = component.render();
                component.mount(element);
                
                return component;
            }
        }
    },
    
    hydrate(element, data) {
        // Hydrate server-rendered content with client-side interactivity
        if (data.component) {
            const ComponentClass = window[data.component.type];
            if (ComponentClass) {
                const component = new ComponentClass(data.component.props, data.component.children);
                component.state._data = data.component.state;
                
                // Don't re-render, just bind events to existing DOM
                component.mount(element);
                
                return component;
            }
        }
    }
};

// Utility functions
window.PyFrame.utils = {
    // Python-like range function
    range(start, stop, step = 1) {
        if (stop === undefined) {
            stop = start;
            start = 0;
        }
        return Array.from({length: Math.ceil((stop - start) / step)}, (_, i) => start + (i * step));
    },
    
    // Python-like enumerate
    enumerate(iterable) {
        return Array.from(iterable).map((item, index) => [index, item]);
    },
    
    // Python-like zip
    zip(...arrays) {
        const minLength = Math.min(...arrays.map(arr => arr.length));
        return Array.from({length: minLength}, (_, i) => arrays.map(arr => arr[i]));
    },
    
    // String formatting
    format(template, ...args) {
        return template.replace(/{(\\d+)}/g, (match, index) => args[index] || '');
    }
};
"""
        
    def generate_polyfills_js(self) -> str:
        """Generate JavaScript polyfills for Python functionality"""
        return """
// PyFrame Polyfills for Python-like functionality

// Array prototype extensions
if (!Array.prototype.append) {
    Array.prototype.append = function(item) {
        this.push(item);
        return this;
    };
}

if (!Array.prototype.extend) {
    Array.prototype.extend = function(items) {
        this.push(...items);
        return this;
    };
}

if (!Array.prototype.insert) {
    Array.prototype.insert = function(index, item) {
        this.splice(index, 0, item);
        return this;
    };
}

if (!Array.prototype.remove) {
    Array.prototype.remove = function(item) {
        const index = this.indexOf(item);
        if (index > -1) {
            this.splice(index, 1);
        }
        return this;
    };
}

if (!Array.prototype.pop) {
    Array.prototype.pop = function(index = -1) {
        if (index === -1) {
            return Array.prototype.pop.call(this);
        } else {
            return this.splice(index, 1)[0];
        }
    };
}

// String prototype extensions  
if (!String.prototype.format) {
    String.prototype.format = function(...args) {
        return this.replace(/{(\\d+)}/g, (match, index) => args[index] || '');
    };
}

if (!String.prototype.startswith) {
    String.prototype.startswith = function(prefix) {
        return this.startsWith(prefix);
    };
}

if (!String.prototype.endswith) {
    String.prototype.endswith = function(suffix) {
        return this.endsWith(suffix);
    };
}

// Object extensions for dict-like behavior
Object.defineProperty(Object.prototype, 'get', {
    value: function(key, defaultValue = null) {
        return this.hasOwnProperty(key) ? this[key] : defaultValue;
    },
    enumerable: false
});

Object.defineProperty(Object.prototype, 'keys', {
    value: function() {
        return Object.keys(this);
    },
    enumerable: false
});

Object.defineProperty(Object.prototype, 'values', {
    value: function() {
        return Object.values(this);
    },
    enumerable: false
});

Object.defineProperty(Object.prototype, 'items', {
    value: function() {
        return Object.entries(this);
    },
    enumerable: false
});

// Python-like truthiness
function pythonBool(value) {
    if (value === null || value === undefined) return false;
    if (typeof value === 'boolean') return value;
    if (typeof value === 'number') return value !== 0;
    if (typeof value === 'string') return value !== '';
    if (Array.isArray(value)) return value.length > 0;
    if (typeof value === 'object') return Object.keys(value).length > 0;
    return true;
}

// Make pythonBool available globally
window.pythonBool = pythonBool;
"""
