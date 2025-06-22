import os
from transpiler import transpile_code

# Path to input and output files
INPUT_FILE = "../examples/test.isipy"
OUTPUT_FILE = "../examples/test.py"

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Input file not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as infile:
        source_code = infile.read()

    transpiled = transpile_code(source_code)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
        outfile.write(transpiled)

    print(f"Transpilation complete. Output written to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()