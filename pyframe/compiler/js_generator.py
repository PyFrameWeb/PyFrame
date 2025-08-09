"""
JavaScript Code Generator

Generates optimized JavaScript code from transformed Python AST,
handling component lifecycle, state management, and event binding.
"""

import ast
from typing import List, Dict, Any, Optional, Union
from ..core.component import Component


class JSGenerator:
    """
    Generates JavaScript code from transformed Python AST.
    
    Converts Python component logic to efficient JavaScript while
    preserving reactive behavior and component semantics.
    """
    
    def __init__(self, minify: bool = False):
        self.minify = minify
        self.indent_level = 0
        self.indent_size = 2 if not minify else 0
        
    def generate_component_js(self, class_name: str, ast_tree: ast.AST, 
                            component_instance: Component) -> str:
        """Generate JavaScript code for a component class"""
        
        # Extract class definition from AST
        class_def = None
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                class_def = node
                break
                
        if not class_def:
            return f"// Could not find class definition for {class_name}"
            
        # Generate class code
        js_code = self._generate_class(class_def, component_instance)
        
        return js_code
        
    def generate_function_js(self, func_name: str, ast_tree: ast.AST) -> str:
        """Generate JavaScript code for a standalone function"""
        
        # Extract function definition from AST
        func_def = None
        for node in ast.walk(ast_tree):
            if isinstance(node, ast.FunctionDef) and node.name == func_name:
                func_def = node
                break
                
        if not func_def:
            return f"// Could not find function definition for {func_name}"
            
        return self._generate_function(func_def)
        
    def generate_expression_js(self, ast_tree: ast.AST) -> str:
        """Generate JavaScript code for an expression"""
        if isinstance(ast_tree, ast.Expression):
            return self._generate_expression(ast_tree.body)
        else:
            return self._generate_expression(ast_tree)
            
    def _generate_class(self, class_def: ast.ClassDef, instance: Component) -> str:
        """Generate JavaScript class from Python class definition"""
        
        # Determine base class
        extends = "PyFrameComponent"
        if hasattr(class_def, 'js_extends') and class_def.js_extends:
            extends = class_def.js_extends
            
        lines = []
        
        # Class declaration
        lines.append(f"class {class_def.name} extends {extends} {{")
        self.indent_level += 1
        
        # Constructor
        constructor_lines = [
            self._indent("constructor(props = {}, children = []) {"),
            self._indent("    super(props, children);", 1),
        ]
        
        # Initialize state with default values from instance
        if hasattr(instance, 'state') and instance.state._data:
            state_init = self._dict_to_js(instance.state._data)
            constructor_lines.append(self._indent(f"    this.state.update({state_init});", 1))
            
        constructor_lines.append(self._indent("}", 1))
        lines.extend(constructor_lines)
        lines.append("")
        
        # Generate methods
        for node in class_def.body:
            if isinstance(node, ast.FunctionDef):
                method_code = self._generate_method(node)
                lines.append(method_code)
                lines.append("")
                
        self.indent_level -= 1
        lines.append("}")
        
        return "\n".join(lines)
        
    def _generate_method(self, func_def: ast.FunctionDef) -> str:
        """Generate JavaScript method from Python method definition"""
        
        # Skip __init__ as it's handled by constructor
        if func_def.name == "__init__":
            return ""
            
        lines = []
        
        # Method signature
        args = []
        for arg in func_def.args.args[1:]:  # Skip 'self'
            args.append(arg.arg)
            
        args_str = ", ".join(args)
        lines.append(self._indent(f"{func_def.name}({args_str}) {{"))
        
        self.indent_level += 1
        
        # Method body
        for stmt in func_def.body:
            stmt_code = self._generate_statement(stmt)
            if stmt_code:
                lines.append(self._indent(stmt_code, 1))
                
        self.indent_level -= 1
        lines.append(self._indent("}"))
        
        return "\n".join(lines)
        
    def _generate_function(self, func_def: ast.FunctionDef) -> str:
        """Generate JavaScript function from Python function definition"""
        
        lines = []
        
        # Function signature
        args = [arg.arg for arg in func_def.args.args]
        args_str = ", ".join(args)
        lines.append(f"function {func_def.name}({args_str}) {{")
        
        self.indent_level += 1
        
        # Function body
        for stmt in func_def.body:
            stmt_code = self._generate_statement(stmt)
            if stmt_code:
                lines.append(self._indent(stmt_code, 1))
                
        self.indent_level -= 1
        lines.append("}")
        
        return "\n".join(lines)
        
    def _generate_statement(self, stmt: ast.stmt) -> str:
        """Generate JavaScript code for a statement"""
        
        if isinstance(stmt, ast.Return):
            return f"return {self._generate_expression(stmt.value)};"
            
        elif isinstance(stmt, ast.Assign):
            if hasattr(stmt, 'js_special') and stmt.js_special == 'state_assignment':
                # Handle state assignment: self.state["key"] = value
                target = stmt.targets[0]
                if isinstance(target, ast.Subscript):
                    key = self._generate_expression(target.slice)
                    value = self._generate_expression(stmt.value)
                    return f"this.setState({key}, {value});"
            else:
                # Regular assignment
                targets = [self._generate_expression(target) for target in stmt.targets]
                value = self._generate_expression(stmt.value)
                return f"{' = '.join(targets)} = {value};"
                
        elif isinstance(stmt, ast.AugAssign):
            target = self._generate_expression(stmt.target)
            op = self._generate_operator(stmt.op)
            value = self._generate_expression(stmt.value)
            return f"{target} {op}= {value};"
            
        elif isinstance(stmt, ast.If):
            return self._generate_if_statement(stmt)
            
        elif isinstance(stmt, ast.For):
            return self._generate_for_statement(stmt)
            
        elif isinstance(stmt, ast.While):
            test = self._generate_expression(stmt.test)
            body = self._generate_block(stmt.body)
            return f"while ({test}) {{\n{body}\n}}"
            
        elif isinstance(stmt, ast.Try):
            return self._generate_try_statement(stmt)
            
        elif isinstance(stmt, ast.Expr):
            return f"{self._generate_expression(stmt.value)};"
            
        else:
            return f"// Unsupported statement: {type(stmt).__name__}"
            
    def _generate_expression(self, expr: ast.expr) -> str:
        """Generate JavaScript code for an expression"""
        
        if expr is None:
            return "null"
            
        elif isinstance(expr, ast.Constant):
            return self._generate_constant(expr)
            
        elif isinstance(expr, ast.Name):
            if hasattr(expr, 'js_builtin'):
                return expr.js_builtin
            elif hasattr(expr, 'js_special') and expr.js_special == 'self_reference':
                return "this"
            else:
                return expr.id
                
        elif isinstance(expr, ast.Attribute):
            value = self._generate_expression(expr.value)
            if hasattr(expr, 'js_special'):
                if expr.js_special == 'component_state':
                    return f"{value}.state"
                elif expr.js_special == 'component_props':
                    return f"{value}.props"
                elif expr.js_special == 'component_children':
                    return f"{value}.children"
            return f"{value}.{expr.attr}"
            
        elif isinstance(expr, ast.Subscript):
            if hasattr(expr, 'js_special') and expr.js_special == 'state_access':
                # Handle state access: self.state["key"] -> this.getState("key")
                key = self._generate_expression(expr.slice)
                return f"this.getState({key})"
            else:
                value = self._generate_expression(expr.value)
                slice_val = self._generate_expression(expr.slice)
                return f"{value}[{slice_val}]"
                
        elif isinstance(expr, ast.Call):
            return self._generate_call(expr)
            
        elif isinstance(expr, ast.BinOp):
            left = self._generate_expression(expr.left)
            op = self._generate_operator(expr.op)
            right = self._generate_expression(expr.right)
            return f"({left} {op} {right})"
            
        elif isinstance(expr, ast.UnaryOp):
            op = "!" if hasattr(expr, 'js_op') and expr.js_op == '!' else self._generate_operator(expr.op)
            operand = self._generate_expression(expr.operand)
            return f"{op}{operand}"
            
        elif isinstance(expr, ast.BoolOp):
            op = expr.js_op if hasattr(expr, 'js_op') else ('&&' if isinstance(expr.op, ast.And) else '||')
            values = [self._generate_expression(value) for value in expr.values]
            return f"({f' {op} '.join(values)})"
            
        elif isinstance(expr, ast.Compare):
            return self._generate_compare(expr)
            
        elif isinstance(expr, ast.List):
            elements = [self._generate_expression(el) for el in expr.elts]
            return f"[{', '.join(elements)}]"
            
        elif isinstance(expr, ast.Dict):
            pairs = []
            for key, value in zip(expr.keys, expr.values):
                key_str = self._generate_expression(key)
                value_str = self._generate_expression(value)
                pairs.append(f"{key_str}: {value_str}")
            return f"{{{', '.join(pairs)}}}"
            
        elif isinstance(expr, ast.JoinedStr):
            # F-string to template literal
            parts = []
            for value in expr.values:
                if isinstance(value, ast.Constant):
                    parts.append(value.value)
                elif isinstance(value, ast.FormattedValue):
                    parts.append(f"${{{self._generate_expression(value.value)}}}")
            return f"`{''.join(parts)}`"
            
        elif isinstance(expr, ast.ListComp):
            return self._generate_list_comprehension(expr)
            
        elif isinstance(expr, ast.Lambda):
            args = [arg.arg for arg in expr.args.args]
            body = self._generate_expression(expr.body)
            return f"({', '.join(args)}) => {body}"
            
        else:
            return f"/* Unsupported expression: {type(expr).__name__} */"
            
    def _generate_call(self, call: ast.Call) -> str:
        """Generate JavaScript function call"""
        
        args = [self._generate_expression(arg) for arg in call.args]
        args_str = ", ".join(args)
        
        if hasattr(call, 'js_builtin'):
            # Handle built-in function calls
            builtin_map = {
                'len': lambda args: f"{args[0]}.length",
                'str': lambda args: f"String({args[0]})",
                'int': lambda args: f"parseInt({args[0]})",
                'float': lambda args: f"parseFloat({args[0]})",
                'bool': lambda args: f"Boolean({args[0]})",
                'list': lambda args: f"Array({args_str})" if args else "[]",
                'dict': lambda args: "{}",
                'print': lambda args: f"console.log({args_str})"
            }
            
            if call.js_builtin in builtin_map:
                return builtin_map[call.js_builtin](args)
                
        elif hasattr(call, 'js_special'):
            if call.js_special == 'state_method_call':
                # Handle state method calls
                method_name = call.func.attr
                if method_name == 'get':
                    return f"this.getState({args_str})"
                elif method_name == 'update':
                    return f"this.mergeState({args_str})"
                    
        # Regular function call
        func = self._generate_expression(call.func)
        return f"{func}({args_str})"
        
    def _generate_compare(self, compare: ast.Compare) -> str:
        """Generate JavaScript comparison expression"""
        
        left = self._generate_expression(compare.left)
        
        if hasattr(compare, 'js_special'):
            if compare.js_special == 'in_operator':
                # Handle 'in' operator
                right = self._generate_expression(compare.comparators[0])
                return f"{right}.includes({left})"
            elif compare.js_special == 'not_in_operator':
                # Handle 'not in' operator
                right = self._generate_expression(compare.comparators[0])
                return f"!{right}.includes({left})"
            elif compare.js_special == 'is_operator':
                # Handle 'is' operator
                right = self._generate_expression(compare.comparators[0])
                return f"{left} === {right}"
            elif compare.js_special == 'is_not_operator':
                # Handle 'is not' operator
                right = self._generate_expression(compare.comparators[0])
                return f"{left} !== {right}"
                
        # Regular comparison
        ops = [self._generate_operator(op) for op in compare.ops]
        comparators = [self._generate_expression(comp) for comp in compare.comparators]
        
        result = left
        for op, comp in zip(ops, comparators):
            result = f"({result} {op} {comp})"
            
        return result
        
    def _generate_if_statement(self, if_stmt: ast.If) -> str:
        """Generate JavaScript if statement"""
        test = self._generate_expression(if_stmt.test)
        body = self._generate_block(if_stmt.body)
        
        result = f"if ({test}) {{\n{body}\n}}"
        
        if if_stmt.orelse:
            if len(if_stmt.orelse) == 1 and isinstance(if_stmt.orelse[0], ast.If):
                # elif
                elif_code = self._generate_if_statement(if_stmt.orelse[0])
                result += f" else {elif_code}"
            else:
                # else
                else_body = self._generate_block(if_stmt.orelse)
                result += f" else {{\n{else_body}\n}}"
                
        return result
        
    def _generate_for_statement(self, for_stmt: ast.For) -> str:
        """Generate JavaScript for loop"""
        
        if hasattr(for_stmt, 'js_special') and for_stmt.js_special == 'for_of_loop':
            # Python for loop -> JavaScript for...of
            target = self._generate_expression(for_stmt.target)
            iter_expr = self._generate_expression(for_stmt.iter)
            body = self._generate_block(for_stmt.body)
            
            return f"for (const {target} of {iter_expr}) {{\n{body}\n}}"
        else:
            # Fallback to regular for loop
            return f"// Unsupported for loop pattern"
            
    def _generate_try_statement(self, try_stmt: ast.Try) -> str:
        """Generate JavaScript try/catch statement"""
        
        body = self._generate_block(try_stmt.body)
        result = f"try {{\n{body}\n}}"
        
        if try_stmt.handlers:
            # Take the first exception handler
            handler = try_stmt.handlers[0]
            catch_var = handler.name if handler.name else "error"
            catch_body = self._generate_block(handler.body)
            result += f" catch ({catch_var}) {{\n{catch_body}\n}}"
            
        if try_stmt.finalbody:
            finally_body = self._generate_block(try_stmt.finalbody)
            result += f" finally {{\n{finally_body}\n}}"
            
        return result
        
    def _generate_list_comprehension(self, listcomp: ast.ListComp) -> str:
        """Generate JavaScript array methods for list comprehension"""
        
        # [expr for target in iter if condition] -> iter.filter(condition).map(expr)
        iter_expr = self._generate_expression(listcomp.generators[0].iter)
        target = listcomp.generators[0].target.id
        element_expr = self._generate_expression(listcomp.elt)
        
        # Replace target variable in element expression
        element_expr = element_expr.replace(target, "item")
        
        result = f"{iter_expr}.map(item => {element_expr})"
        
        # Add filter if there are conditions
        if listcomp.generators[0].ifs:
            condition = self._generate_expression(listcomp.generators[0].ifs[0])
            condition = condition.replace(target, "item")
            result = f"{iter_expr}.filter(item => {condition}).map(item => {element_expr})"
            
        return result
        
    def _generate_block(self, statements: List[ast.stmt]) -> str:
        """Generate JavaScript code block"""
        lines = []
        self.indent_level += 1
        
        for stmt in statements:
            stmt_code = self._generate_statement(stmt)
            if stmt_code:
                lines.append(self._indent(stmt_code, 1))
                
        self.indent_level -= 1
        return "\n".join(lines)
        
    def _generate_operator(self, op: ast.operator) -> str:
        """Generate JavaScript operator"""
        op_map = {
            ast.Add: "+",
            ast.Sub: "-", 
            ast.Mult: "*",
            ast.Div: "/",
            ast.FloorDiv: "//",  # Will need special handling
            ast.Mod: "%",
            ast.Pow: "**",
            ast.LShift: "<<",
            ast.RShift: ">>",
            ast.BitOr: "|",
            ast.BitXor: "^",
            ast.BitAnd: "&",
            ast.Eq: "===",
            ast.NotEq: "!==",
            ast.Lt: "<",
            ast.LtE: "<=",
            ast.Gt: ">",
            ast.GtE: ">=",
            ast.UAdd: "+",
            ast.USub: "-",
            ast.Not: "!",
            ast.Invert: "~"
        }
        
        return op_map.get(type(op), "?")
        
    def _generate_constant(self, const: ast.Constant) -> str:
        """Generate JavaScript constant value"""
        
        if hasattr(const, 'js_value'):
            return const.js_value
        elif const.value is None:
            return "null"
        elif const.value is True:
            return "true"
        elif const.value is False:
            return "false"
        elif isinstance(const.value, str):
            # Escape string for JavaScript
            escaped = const.value.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            return f'"{escaped}"'
        else:
            return str(const.value)
            
    def _dict_to_js(self, obj: Any) -> str:
        """Convert Python dict to JavaScript object literal"""
        
        if isinstance(obj, dict):
            pairs = []
            for key, value in obj.items():
                key_str = f'"{key}"' if isinstance(key, str) else str(key)
                value_str = self._dict_to_js(value)
                pairs.append(f"{key_str}: {value_str}")
            return f"{{{', '.join(pairs)}}}"
        elif isinstance(obj, list):
            items = [self._dict_to_js(item) for item in obj]
            return f"[{', '.join(items)}]"
        elif isinstance(obj, str):
            escaped = obj.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
            return f'"{escaped}"'
        elif obj is None:
            return "null"
        elif obj is True:
            return "true"
        elif obj is False:
            return "false"
        else:
            return str(obj)
            
    def _indent(self, code: str, extra_indent: int = 0) -> str:
        """Add indentation to code"""
        if self.minify:
            return code
            
        indent = " " * (self.indent_size * (self.indent_level + extra_indent))
        return f"{indent}{code}"
