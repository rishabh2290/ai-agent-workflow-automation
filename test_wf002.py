
from workflow_engine import execute_workflow

products = [
    {
        "product_name": "Keyboard",
        "internal_price": 500,
        "vendor_price": 600,
    },
    {
        "product_name": "Mouse",
        "internal_price": 300,
        "vendor_price": 315,
    },
    {
        "product_name": "Monitor",
        "internal_price": 10000,
        "vendor_price": 8500,
    },
]

result = execute_workflow(
    "Find products where vendor price differs by more than 10%.",
    data={"products": products},
)

print("Status:", result["status"])
print("Workflow:", result.get("workflow_name"))
print("Steps:", result.get("steps"))
print("Output:", result.get("output", result.get("message")))

assert result["status"] == "success"
assert result["workflow_id"] == "WF002"

exceptions = result["output"]

assert len(exceptions) == 2

product_names = [item["product"] for item in exceptions]

assert "Keyboard" in product_names
assert "Monitor" in product_names
assert "Mouse" not in product_names

print("Detected exceptions:", product_names)

print("\nWF002 test passed.")
