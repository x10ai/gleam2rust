"""
This module contains the core logic for transpiling a Gleam AST into Rust code.
It uses a visitor pattern to walk the AST and generate code.
This version is simplified to focus on correctness for basic examples.
"""

import tree_sitter

class Transpiler:
    """
    Traverses a tree-sitter AST for Gleam and generates Rust code.
    """

    OPERATOR_MAP = {
        # Float operators
        "+.": "+",
        "-.": "-",
        "*.": "*",
        "/.": "/",
        ">.": ">",
        "<.": "<",
        ">=.": ">=",
        "<=.": "<=",
        # String concat
        "<>": "+",
    }

    TYPE_MAP = {
        "Int": "i64",
        "Float": "f64",
        "String": "String",
        "Bool": "bool",
    }

    def __init__(self):
        self._rust_code = []
        self._indentation_level = 0

    def transpile(self, tree: tree_sitter.Tree) -> str:
        """
        Public method to start the transpilation process.
        """
        self._visit(tree.root_node)
        return "".join(self._rust_code).strip()

    def _visit(self, node: tree_sitter.Node, **kwargs):
        """
        Generic visit method that dispatches to specific handlers for named nodes.
        """
        if not node.is_named:
            return

        handler_name = f"_handle_{node.type}"
        handler = getattr(self, handler_name, self._unsupported_node)
        handler(node, **kwargs)

    def _emit(self, code: str, indent=True):
        """Appends a string of code to the output, managing indentation."""
        if indent:
            self._rust_code.append("  " * self._indentation_level)
        self._rust_code.append(code)

    def _increase_indent(self):
        self._indentation_level += 1

    def _decrease_indent(self):
        self._indentation_level -= 1

    def _text(self, node: tree_sitter.Node) -> str:
        """Gets the text content of a node."""
        return node.text.decode('utf8')

    def _unsupported_node(self, node: tree_sitter.Node, **kwargs):
        """Handler for node types that are not yet supported."""
        print(f"Warning: Unsupported node type '{node.type}' encountered. Skipping.")

    # --- Handlers ---

    def _handle_source_file(self, node: tree_sitter.Node, **kwargs):
        for child in node.named_children:
            self._visit(child, **kwargs)
            self._emit("\n\n")

    def _handle_import(self, node: tree_sitter.Node, **kwargs):
        # Ignoring imports for now
        pass

    def _handle_function(self, node: tree_sitter.Node, **kwargs):
        is_public = any(child.type == 'visibility_modifier' for child in node.children)
        if is_public:
            self._emit("pub ")

        self._emit("fn ")
        name_node = node.child_by_field_name('name')
        if name_node:
            self._emit(self._text(name_node))

        self._emit("(", indent=False)
        params_node = node.child_by_field_name('parameters')
        if params_node:
            for i, child in enumerate(params_node.named_children):
                self._visit(child, **kwargs)
                if i < len(params_node.named_children) - 1:
                    self._emit(", ", indent=False)
        self._emit(")", indent=False)

        return_type_node = node.child_by_field_name('return_type')
        if return_type_node:
            self._emit(" -> ", indent=False)
            # The actual type is nested inside the 'return_type' node
            self._visit(return_type_node.named_children[0], **kwargs)

        body_node = node.child_by_field_name('body')
        if body_node:
            self._emit(" ", indent=False)
            self._visit(body_node, **kwargs)

    def _handle_block(self, node: tree_sitter.Node, **kwargs):
        self._emit("{\n", indent=False)
        self._increase_indent()

        num_children = len(node.named_children)
        for i, child in enumerate(node.named_children):
            self._emit("", indent=True)
            self._visit(child, **kwargs)
            # In Rust, the last expression of a block is its return value,
            # so we don't add a semicolon.
            if i < num_children - 1:
                self._emit(";\n", indent=False)
            else:
                self._emit("\n", indent=False)

        self._decrease_indent()
        self._emit("}", indent=False)

    def _handle_let(self, node: tree_sitter.Node, **kwargs):
        self._emit("let ", indent=False)
        self._visit(node.child_by_field_name('pattern'), **kwargs)
        self._emit(" = ", indent=False)
        self._visit(node.child_by_field_name('value'), is_expression=True, **kwargs)

    def _handle_binary_expression(self, node: tree_sitter.Node, **kwargs):
        left_node = node.child_by_field_name('left')
        op_text = self._text(node.child_by_field_name('operator'))
        right_node = node.child_by_field_name('right')

        rust_op = self.OPERATOR_MAP.get(op_text, op_text)

        self._visit(left_node, **kwargs)
        self._emit(f" {rust_op} ", indent=False)
        self._visit(right_node, **kwargs)

    def _handle_echo(self, node: tree_sitter.Node, **kwargs):
        self._emit('println!("{:?}", ', indent=False)
        if node.named_children:
            expression_node = node.named_children[-1]
            self._visit(expression_node, is_expression=True, **kwargs)
        self._emit(")", indent=False)

    def _handle_function_parameter(self, node: tree_sitter.Node, **kwargs):
        name_node = node.child_by_field_name('name')
        type_node = node.child_by_field_name('type')

        if name_node:
            self._emit(self._text(name_node), indent=False)

        if type_node:
            self._emit(": ", indent=False)
            # The actual type is nested inside the 'type' node
            self._visit(type_node.named_children[0], **kwargs)

    def _handle_function_call(self, node: tree_sitter.Node, **kwargs):
        function_node = node.child_by_field_name('function')
        args_node = node.child_by_field_name('arguments')

        # Special case for io.println -> println! macro
        if function_node.type == 'field_access':
            module_name = self._text(function_node.child_by_field_name('record'))
            func_name = self._text(function_node.child_by_field_name('field'))
            if module_name == 'io' and func_name == 'println':
                self._emit("println!", indent=False)
                self._emit("(", indent=False)
                # We need to handle the format string for multiple arguments,
                # but for now, let's assume a single argument.
                if args_node and args_node.named_children:
                    self._emit("\"{:?}\", ", indent=False)
                    self._visit(args_node.named_children[0], is_expression=True, **kwargs)
                self._emit(")", indent=False)
                return

        # General function call
        self._visit(function_node, **kwargs)
        self._emit("(", indent=False)
        if args_node:
            self._visit(args_node, **kwargs)
        self._emit(")", indent=False)

    def _handle_arguments(self, node: tree_sitter.Node, **kwargs):
        for i, child in enumerate(node.named_children):
            self._visit(child, **kwargs)
            if i < len(node.named_children) - 1:
                self._emit(", ", indent=False)

    def _handle_argument(self, node: tree_sitter.Node, **kwargs):
        value_node = node.child_by_field_name('value')
        if value_node: self._visit(value_node, **kwargs)

    def _handle_identifier(self, node: tree_sitter.Node, **kwargs):
        self._emit(self._text(node), indent=False)

    def _handle_integer(self, node: tree_sitter.Node, **kwargs):
        self._emit(self._text(node), indent=False)

    def _handle_string(self, node: tree_sitter.Node, **kwargs):
        self._emit(self._text(node), indent=False)

    def _handle_float(self, node: tree_sitter.Node, **kwargs):
        self._emit(self._text(node), indent=False)

    def _handle_case(self, node: tree_sitter.Node, **kwargs):
        self._emit("match ", indent=False)
        subjects_node = node.child_by_field_name('subjects')
        if subjects_node and subjects_node.named_children:
            self._visit(subjects_node.named_children[0], **kwargs)

        self._emit(" {\n", indent=False)
        self._increase_indent()

        clauses_node = node.child_by_field_name('clauses')
        if clauses_node:
            for clause in clauses_node.named_children:
                self._emit("", indent=True)
                self._visit(clause, **kwargs)
                self._emit("\n", indent=False)


        self._decrease_indent()
        self._emit("", indent=True)
        self._emit("}", indent=False)

    def _handle_case_clause(self, node: tree_sitter.Node, **kwargs):
        patterns_node = node.child_by_field_name('patterns')
        value_node = node.child_by_field_name('value')

        if patterns_node and patterns_node.named_children:
            # The AST nests the actual pattern inside a few nodes
            self._visit(patterns_node.named_children[0].named_children[0], **kwargs)

        self._emit(" => {\n", indent=False)
        self._increase_indent()
        self._emit("", indent=True)

        if value_node:
            self._visit(value_node, **kwargs)

        self._emit("\n", indent=False)
        self._decrease_indent()
        self._emit("", indent=True)
        self._emit("},", indent=False)

    def _handle_discard(self, node: tree_sitter.Node, **kwargs):
        self._emit("_", indent=False)

    def _handle_type_identifier(self, node: tree_sitter.Node, **kwargs):
        gleam_type = self._text(node)
        rust_type = self.TYPE_MAP.get(gleam_type, gleam_type)
        self._emit(rust_type, indent=False)
