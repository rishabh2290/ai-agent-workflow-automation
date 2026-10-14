
from pathlib import Path
from workflow_engine import execute_workflow

sample_file = Path(__file__).parent / "sample_vendor.csv"

result = execute_workflow(
    "Process this vendor spreadsheet and show invalid rows.",
    data={"file_path": str(sample_file)},
)

print("Status:", result["status"])
print("Workflow:", result.get("workflow_name"))
print("Steps:", result.get("steps"))
print("Output:", result.get("output", result.get("message")))

assert result["status"] == "success"
assert result["workflow_id"] == "WF003"
assert result["output"]["summary"]["total_rows"] == 3
assert result["output"]["summary"]["valid_count"] == 1
assert result["output"]["summary"]["invalid_count"] == 2

print("\nWF003 end-to-end test passed.")
