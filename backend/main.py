import os
from transpiler.transpiler import transpile_code
from executor.executor import run_transpiled_file

INPUT_FILE = "examples/test.isipy"
OUTPUT_FILE = INPUT_FILE.replace(".isipy", "_transpiled.py")

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Input file not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as infile:
        source_code = infile.read() #Note to myself: this will come from a http request once frontend is implemented

    transpiled = transpile_code(source_code)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as outfile:
        outfile.write(transpiled)

    print(f"Transpilation complete. Output written to {OUTPUT_FILE}\n")

    stdout, stderr = run_transpiled_file(OUTPUT_FILE)

    if stdout:
        print("🔹 Program Output:")
        print(stdout)

    if stderr:
        print("🔸 Errors:")
        print(stderr)

if __name__ == "__main__":
    main()