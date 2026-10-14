
from pprint import pprint
from workflow_engine import execute_workflow

logs = [
    {
        "workflow_name": "Inventory Restock Check",
        "status": "success",
        "duration_seconds": 2.4,
        "error": None,
        "steps": [
            {"name": "Read inventory", "duration_seconds": 1.2},
            {"name": "Compare stock", "duration_seconds": 6.3},
        ],
    },
    {
        "workflow_name": "Product Price Validation",
        "status": "error",
        "duration_seconds": 8.0,
        "error": "Invalid price data",
        "steps": [
            {"name": "Validate prices", "duration_seconds": 8.0},
        ],
    },
    {
        "workflow_name": "Inventory Restock Check",
        "status": "success",
        "duration_seconds": 3.6,
        "error": None,
        "steps": [
            {"name": "Read inventory", "duration_seconds": 1.4},
        ],
    },
]

print("\n--- TEST 1: PERFORMANCE REPORT ---")

result = execute_workflow(
    "Which workflows are failing most often?",
    data={
        "logs": logs,
        "slow_step_threshold": 5.0,
    },
)

pprint(result)

assert result["status"] == "success"
assert result["workflow_id"] == "WF010"

report = result["output"]
assert report["total_executions"] == 3
assert report["successful_executions"] == 2
assert report["failed_executions"] == 1
assert report["failure_rate_percent"] == 33.33
assert report["average_duration_seconds"] == 4.67
assert len(report["slow_steps"]) >= 1

print("\n--- TEST 2: MISSING EXECUTION LOGS ---")

result = execute_workflow(
    "Which workflows are failing most often?",
    data={},
)

pprint(result)

assert result["status"] == "needs_input"

print("\nBoth WF010 tests passed!")
