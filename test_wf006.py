
from workflow_engine import execute_workflow

products = [
    {
        "sku": "SKU001",
        "product_name": "Wireless Keyboard",
        "brand": "Logitech",
        "category": "Accessories",
    },
    {
        "sku": "SKU001",
        "product_name": "Wireless Keyboard",
        "brand": "Logitech",
        "category": "Accessories",
    },
    {
        "sku": "SKU002",
        "product_name": "Wireless Keyboards",
        "brand": "Logitech",
        "category": "Accessories",
    },
    {
        "sku": "SKU003",
        "product_name": "Office Chair",
        "brand": "Generic",
        "category": "Furniture",
    },
]

result = execute_workflow(
    "Find likely duplicate products in the catalog.",
    data={"products": products},
)

print("Status:", result["status"])
print("Workflow:", result.get("workflow_name"))
print("Steps:", result.get("steps"))
print("Output:", result.get("output", result.get("message")))

assert result["status"] == "success"
assert result["workflow_id"] == "WF006"

groups = result["output"]["duplicate_groups"]

# The two identical SKU001 records must be identified.
assert any(
    group["duplicate_type"] == "definite"
    and "sku" in group["matching_fields"]
    for group in groups
)

# The unrelated Office Chair must not appear in any duplicate group.
assert not any(
    any(
        product.get("product_name") == "Office Chair"
        for product in group["products"]
    )
    for group in groups
)

# Missing catalog should be handled gracefully.
missing_result = execute_workflow(
    "Find likely duplicate products in the catalog.",
    data={},
)
assert missing_result["status"] == "needs_input"

print("\nWF006 tests passed.")
