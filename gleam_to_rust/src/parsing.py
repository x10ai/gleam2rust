"""
This module is responsible for parsing Gleam source code into an
Abstract Syntax Tree (AST) using the tree-sitter library.
"""

from tree_sitter import Language, Parser
from tree_sitter_gleam import language as gleam_language_binding

class GleamParser:
    """A parser for Gleam code."""

    def __init__(self):
        """Initializes the parser with the Gleam language."""
        self.parser = Parser()
        # We must wrap the language binding in a Language object.
        self.parser.language = Language(gleam_language_binding())

    def parse(self, source_code: str):
        """
        Parses the given Gleam source code.

        Args:
            source_code: A string containing the Gleam code.

        Returns:
            A tree-sitter Tree object representing the parsed code.
        """
        return self.parser.parse(bytes(source_code, "utf8"))
