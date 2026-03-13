from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def refresh_document_pipeline() -> dict:
    scripts = [
        "04_build_document_store.py",
        "07_generate_document_summaries.py",
        "09_build_paper_catalog.py",
    ]

    outputs = []

    for script_name in scripts:
        script_path = PROJECT_ROOT / "scripts" / script_name
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True
        )

        outputs.append({
            "script": script_name,
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        })

        if result.returncode != 0:
            return {
                "success": False,
                "message": f"Pipeline refresh failed on {script_name}",
                "details": outputs,
            }

    return {
        "success": True,
        "message": "Document pipeline refreshed successfully.",
        "details": outputs,
    }
