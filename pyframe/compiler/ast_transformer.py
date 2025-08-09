"""
AST Transformer

Transforms Python AST nodes to JavaScript-compatible representations
while preserving semantic meaning and adding necessary runtime support.
"""

import ast
from typing import List, Dict, Any, Optional, Union


class ASTTransformer(ast.NodeTransformer):
    """
    Transforms Python AST to JavaScript-compatible AST.
    
    Handles Python-specific constructs and converts them to equivalent
    JavaScript while maintaining reactive component behavior.
    """
    
    def __init__(self):
        self.warnings: List[str] = []
        self.scope_stack: List[Dict[str, Any]] = [{}]
        self.current_class = None
        self.in_component_method = False
        
    def warn(self, message: str) -> None:
        """Add a warning message"""
        self.warnings.append(message)
        
    def push_scope(self) -> None:
        """Push a new variable scope"""
        self.scope_stack.append({})
        
    def pop_scope(self) -> None:
        """Pop the current variable scope"""
        if len(self.scope_stack) > 1:
            self.scope_stack.pop()
            
    def visit_ClassDef(self, node: ast.ClassDef) -> ast.ClassDef:
        """Transform class definitions (components)"""
        old_class = self.current_class
        self.current_class = node.name
        
        # Add JavaScript class metadata
        node.js_extends = None
        
        # Check if this is a component class
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in ['Component', 'StatefulComponent']:
                node.js_extends = 'PyFrameComponent'
                break
                
        # Transform class body
        self.push_scope()
        node = self.generic_visit(node)
        self.pop_scope()
        
        self.current_class = old_class
        return node
        
    def visit_FunctionDef(self, node: ast.FunctionDef) -> ast.FunctionDef:
        """Transform function definitions"""
        old_in_method = self.in_component_method
        
        # Check if this is a component method
        if self.current_class and node.name in ['render', 'mount', 'unmount', 'update']:
            self.in_component_method = True
            
        self.push_scope()
        node = self.generic_visit(node)
        self.pop_scope()
        
        self.in_component_method = old_in_method
        return node
        
    def visit_Attribute(self, node: ast.Attribute) -> ast.Attribute:
        """Transform attribute access (self.state, self.props, etc.)"""
        node = self.generic_visit(node)
        
        # Handle special component attributes
        if isinstance(node.value, ast.Name) and node.value.id == 'self':
            if node.attr == 'state':
                # Mark for special handling in JS generation
                node.js_special = 'component_state'
            elif node.attr == 'props':
                node.js_special = 'component_props'
            elif node.attr == 'children':
                node.js_special = 'component_children'
                
        return node
        
    def visit_Subscript(self, node: ast.Subscript) -> ast.Subscript:
        """Transform subscript operations (dict/list access)"""
        node = self.generic_visit(node)
        
        # Handle state access like self.state["key"]
        if (isinstance(node.value, ast.Attribute) and 
            hasattr(node.value, 'js_special') and 
            node.value.js_special == 'component_state'):
            node.js_special = 'state_access'
            
        return node
        
    def visit_Assign(self, node: ast.Assign) -> ast.Assign:
        """Transform assignment operations"""
        node = self.generic_visit(node)
        
        # Handle state assignments
        for target in node.targets:
            if (isinstance(target, ast.Subscript) and
                isinstance(target.value, ast.Attribute) and
                hasattr(target.value, 'js_special') and
                target.value.js_special == 'component_state'):
                node.js_special = 'state_assignment'
                
        return node
        
    def visit_Call(self, node: ast.Call) -> ast.Call:
        """Transform function calls"""
        node = self.generic_visit(node)
        
        # Handle method calls on self
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name) and node.func.value.id == 'self':
                # Component method call
                node.js_special = 'component_method_call'
            elif (isinstance(node.func.value, ast.Attribute) and
                  hasattr(node.func.value, 'js_special') and
                  node.func.value.js_special == 'component_state'):
                # State method call like self.state.get()
                node.js_special = 'state_method_call'
                
        # Handle built-in functions
        elif isinstance(node.func, ast.Name):
            if node.func.id in ['len', 'str', 'int', 'float', 'bool', 'list', 'dict', 'print']:
                node.js_builtin = node.func.id
                
        return node
        
    def visit_For(self, node: ast.For) -> ast.For:
        """Transform for loops"""
        node = self.generic_visit(node)
        
        # Mark for JavaScript for...of conversion
        node.js_special = 'for_of_loop'
        
        return node
        
    def visit_ListComp(self, node: ast.ListComp) -> ast.ListComp:
        """Transform list comprehensions"""
        node = self.generic_visit(node)
        
        # Mark for JavaScript array methods conversion
        node.js_special = 'list_comprehension'
        
        return node
        
    def visit_DictComp(self, node: ast.DictComp) -> ast.DictComp:
        """Transform dictionary comprehensions"""
        node = self.generic_visit(node)
        
        # Mark for JavaScript object conversion
        node.js_special = 'dict_comprehension'
        
        return node
        
    def visit_Compare(self, node: ast.Compare) -> ast.Compare:
        """Transform comparison operations"""
        node = self.generic_visit(node)
        
        # Handle Python-specific operators
        for op in node.ops:
            if isinstance(op, ast.In):
                node.js_special = 'in_operator'
            elif isinstance(op, ast.NotIn):
                node.js_special = 'not_in_operator'
            elif isinstance(op, ast.Is):
                node.js_special = 'is_operator'
            elif isinstance(op, ast.IsNot):
                node.js_special = 'is_not_operator'
                
        return node
        
    def visit_BoolOp(self, node: ast.BoolOp) -> ast.BoolOp:
        """Transform boolean operations"""
        node = self.generic_visit(node)
        
        # Python 'and'/'or' vs JavaScript '&&'/'||'
        if isinstance(node.op, ast.And):
            node.js_op = '&&'
        elif isinstance(node.op, ast.Or):
            node.js_op = '||'
            
        return node
        
    def visit_UnaryOp(self, node: ast.UnaryOp) -> ast.UnaryOp:
        """Transform unary operations"""
        node = self.generic_visit(node)
        
        # Python 'not' vs JavaScript '!'
        if isinstance(node.op, ast.Not):
            node.js_op = '!'
            
        return node
        
    def visit_JoinedStr(self, node: ast.JoinedStr) -> ast.JoinedStr:
        """Transform f-strings"""
        node = self.generic_visit(node)
        
        # Mark for JavaScript template literal conversion
        node.js_special = 'template_literal'
        
        return node
        
    def visit_If(self, node: ast.If) -> ast.If:
        """Transform if statements"""
        node = self.generic_visit(node)
        
        # Add JavaScript conversion hints
        node.js_special = 'if_statement'
        
        return node
        
    def visit_While(self, node: ast.While) -> ast.While:
        """Transform while loops"""
        node = self.generic_visit(node)
        
        node.js_special = 'while_loop'
        
        return node
        
    def visit_Try(self, node: ast.Try) -> ast.Try:
        """Transform try/except blocks"""
        node = self.generic_visit(node)
        
        # Mark for JavaScript try/catch conversion
        node.js_special = 'try_catch'
        
        return node
        
    def visit_With(self, node: ast.With) -> ast.With:
        """Transform with statements"""
        node = self.generic_visit(node)
        
        # With statements need special handling in JS
        node.js_special = 'with_statement'
        self.warn("'with' statements may not translate directly to JavaScript")
        
        return node
        
    def visit_Lambda(self, node: ast.Lambda) -> ast.Lambda:
        """Transform lambda functions"""
        node = self.generic_visit(node)
        
        # Mark for JavaScript arrow function conversion
        node.js_special = 'arrow_function'
        
        return node
        
    def visit_Name(self, node: ast.Name) -> ast.Name:
        """Transform name references"""
        node = self.generic_visit(node)
        
        # Handle Python built-ins and keywords
        if node.id in ['True', 'False', 'None']:
            node.js_builtin = {
                'True': 'true',
                'False': 'false', 
                'None': 'null'
            }[node.id]
        elif node.id in ['self']:
            node.js_special = 'self_reference'
            
        return node
        
    def visit_Constant(self, node: ast.Constant) -> ast.Constant:
        """Transform constant values"""
        node = self.generic_visit(node)
        
        # Handle Python None, True, False
        if node.value is None:
            node.js_value = 'null'
        elif node.value is True:
            node.js_value = 'true'
        elif node.value is False:
            node.js_value = 'false'
            
        return node
