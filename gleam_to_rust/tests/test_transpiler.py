import unittest
import os
import sys

# Add the project root directory to the Python path to allow for absolute imports
# This makes the test runnable from any directory
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, PROJECT_ROOT)

from src.parsing import GleamParser
from src.transpiling import Transpiler

class TestTranspiler(unittest.TestCase):
    """
    Unit tests for the end-to-end transpilation process.
    """

    def test_basic_transpilation(self):
        """
        Tests the transpilation of a basic Gleam file with MVP features.
        """
        # Define the path to the example Gleam file
        gleam_file_path = os.path.join(PROJECT_ROOT, 'examples', 'basic.gleam')

        # Ensure the example file exists
        self.assertTrue(os.path.exists(gleam_file_path), "Example Gleam file not found.")

        with open(gleam_file_path, 'r', encoding='utf-8') as f:
            gleam_code = f.read()

        # Define the expected Rust code output
        expected_rust_code = """
pub fn add(a: i64, b: i64) -> i64 {
  a + b
}

fn main() {
  let x = 1;
  let y = 2;
  let result = add(x, y);
  match result {
    3 => {
      "three"
    },
    _ => {
      "not three"
    },
  }
}
""".strip()

        # 1. Parse the Gleam code
        parser = GleamParser()
        tree = parser.parse(gleam_code)
        self.assertFalse(tree.root_node.has_error, "Parsing failed: syntax errors found in Gleam code.")

        # 2. Transpile the AST
        transpiler = Transpiler()
        actual_rust_code = transpiler.transpile(tree)

        # 3. Compare the actual vs. expected output
        # Normalizing both by stripping lines and removing empty lines makes the comparison
        # more robust to minor whitespace or newline differences.
        actual_lines = [line.strip() for line in actual_rust_code.splitlines() if line.strip()]
        expected_lines = [line.strip() for line in expected_rust_code.splitlines() if line.strip()]

        # For easier debugging, compare line by line
        for i, (actual, expected) in enumerate(zip(actual_lines, expected_lines)):
            self.assertEqual(actual, expected, f"Mismatch at line {i+1}:\nActual:   '{actual}'\nExpected: '{expected}'")

        # Also check that the number of lines is the same
        self.assertEqual(len(actual_lines), len(expected_lines), "The number of non-empty lines differs.")


if __name__ == '__main__':
    # This allows running the tests directly from this file
    unittest.main()
