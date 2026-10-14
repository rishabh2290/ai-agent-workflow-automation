
from tool_registry import run_tool


sample_rows = [
    {
        "SKU": "SKU001",
        "Product Name": "Keyboard",
        "Price": 500,
    },
    {
        "SKU": "",
        "Product Name": "Mouse",
        "Price": 300,
    },
    {
        "SKU": "SKU003",
        "Product Name": "",
        "Price": 200,
    },
]

result = run_tool(
    "validate_vendor_rows",
    rows=sample_rows,
)

print("Validation summary:")
print(result["summary"])

print("\nValid rows:")
print(result["valid_rows"])

print("\nInvalid rows:")
print(result["invalid_rows"])

assert result["summary"]["total_rows"] == 3
assert result["summary"]["valid_count"] == 1
assert result["summary"]["invalid_count"] == 2

print("\nAll vendor validation tests passed.")
