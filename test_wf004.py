
from workflow_engine import execute_workflow

product = {
    "product_name": "Wireless Keyboard",
    "category": "Computer Accessories",
    "material": "ABS plastic",
    "color": "Black",
    "target_audience": "Office professionals",
}

result = execute_workflow(
    "Generate SEO content for this product.",
    data={"product": product},
)

print("Status:", result["status"])
print("Workflow:", result.get("workflow_name"))
print("Steps:", result.get("steps"))
print("Output:", result.get("output", result.get("message")))

assert result["status"] == "success"
assert result["workflow_id"] == "WF004"
assert result["output"]["description"]
assert result["output"]["short_description"]
assert result["output"]["seo_title"]
assert result["output"]["meta_description"]

# Verify missing required input is handled.
missing_result = execute_workflow(
    "Generate SEO content for this product.",
    data={"product": {"product_name": "Wireless Keyboard"}},
)

assert missing_result["status"] == "needs_input"

print("\nWF004 tests passed.")

