"""
The command-line interface for the Gleam to Rust transpiler.
"""

import argparse
from .parsing import GleamParser
from .transpiling import Transpiler

def main():
    """
    Parses command-line arguments and runs the transpiler.
    """
    parser = argparse.ArgumentParser(
        description="Transpile Gleam code to Rust."
    )
    parser.add_argument(
        "input_file",
        help="The path to the input Gleam file."
    )
    parser.add_argument(
        "-o", "--output",
        dest="output_file",
        help="The path to the output Rust file. If not provided, prints to stdout."
    )
    args = parser.parse_args()

    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            gleam_code = f.read()
    except FileNotFoundError:
        print(f"Error: Input file not found at '{args.input_file}'")
        return
    except Exception as e:
        print(f"Error reading input file: {e}")
        return

    # 1. Parse the code
    gleam_parser = GleamParser()
    tree = gleam_parser.parse(gleam_code)

    if tree.root_node.has_error:
        # TODO: More granular error reporting
        print("Error: Could not parse the Gleam code. Please check for syntax errors.")
        return

    # 2. Transpile the AST
    transpiler = Transpiler()
    rust_code = transpiler.transpile(tree)

    # 3. Output the result
    if args.output_file:
        try:
            with open(args.output_file, 'w', encoding='utf-8') as f:
                f.write(rust_code)
            print(f"Successfully transpiled '{args.input_file}' to '{args.output_file}'")
        except Exception as e:
            print(f"Error writing to output file: {e}")
    else:
        print(rust_code)

if __name__ == "__main__":
    main()
