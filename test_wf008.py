
from pprint import pprint
from workflow_engine import execute_workflow

print("\n--- TEST 1: SEO KEYWORD CLASSIFICATION ---")

result = execute_workflow(
    "Classify these keywords and map them to pages.",
    data={
        "keywords": [
            "buy running shoes",
            "best running shoes",
            "how to choose running shoes",
            "buy running shoes",
        ],
        "category": "Footwear",
        "output_path": "output/test_seo_keyword_report.csv",
    },
)

pprint(result)

assert result["status"] == "success"
assert result["workflow_id"] == "WF008"
assert result["output"]["unique_keywords"] == 3
assert result["output"]["duplicates_removed"] == 1

print("\n--- TEST 2: MISSING KEYWORDS ---")

result = execute_workflow(
    "Classify these keywords and map them to pages.",
    data={},
)

pprint(result)

assert result["status"] == "needs_input"

print("\nBoth WF008 tests passed!")
