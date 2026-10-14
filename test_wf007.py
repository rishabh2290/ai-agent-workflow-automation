
from pprint import pprint
from workflow_engine import execute_workflow

# Test 1: Complete campaign details
campaign_data = {
    "campaign": {
        "campaign_name": "New Collection Launch",
        "goal": "Increase sales of the new collection",
        "products": ["Summer Shirt", "Casual Trousers"],
        "target_audience": "Young adults aged 18-30",
        "promotion": "10% launch discount",
        "start_date": "2026-10-20",
        "end_date": "2026-10-31"
    }
}

print("\n--- TEST 1: COMPLETE CAMPAIGN ---")
result = execute_workflow(
    "Create a campaign brief for the new collection.",
    data=campaign_data
)
pprint(result)

assert result["status"] == "success"
assert result["workflow_id"] == "WF007"
assert "objective" in result["output"]

# Test 2: Missing required fields
print("\n--- TEST 2: MISSING CAMPAIGN DETAILS ---")
result = execute_workflow(
    "Create a campaign brief for the new collection.",
    data={"campaign": {"products": ["Summer Shirt"]}}
)
pprint(result)

assert result["status"] == "needs_input"
assert "goal" in result["missing_fields"]

print("\nBoth WF007 tests passed!")
