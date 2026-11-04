"""Run Chapter 08 from immutable local raw inputs, from any working directory."""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.midterm_project import run_midterm_project


def main():
    result = run_midterm_project(
        raw_dir=ROOT / "data/raw", processed_dir=ROOT / "data/processed",
        report_dir=ROOT / "reports", figure_dir=ROOT / "reports/figures",
        show_figures=False,
    )
    print("Chapter 08: completed")
    print("\n[Total consistency]")
    print(result["analysis_tables"]["total_consistency_check"].to_string(index=False))
    print("\n[Final Validation]")
    print(result["project_validation"].to_string(index=False))
    print("\nAll 8 checks: PASS")
    print("Report:", result["report_path"])
    return result


if __name__ == "__main__":
    main()
