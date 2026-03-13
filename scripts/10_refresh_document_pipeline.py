from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def run_script(script_name: str):
    script_path = PROJECT_ROOT / "scripts" / script_name
    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True
    )
    print(f"\n--- {script_name} ---")
    print(result.stdout)
    if result.stderr:
        print(result.stderr)
    return result.returncode == 0


def main():
    scripts = [
        "04_build_document_store.py",
        "07_generate_document_summaries.py",
        "09_build_paper_catalog.py",
    ]

    all_ok = True
    for script in scripts:
        ok = run_script(script)
        if not ok:
            all_ok = False
            break

    if all_ok:
        print("\nDocument pipeline refresh complete.")
    else:
        print("\nDocument pipeline refresh failed.")


if __name__ == "__main__":
    main()
