
# from workflow_engine import execute_workflow
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from workflow_engine import execute_workflow

def test_inventory_restock():
    data = {
        "products": [
            {
                "product_name": "Keyboard",
                "current_stock": 5,
                "minimum_stock": 10,
            },
            {
                "product_name": "Mouse",
                "current_stock": 20,
                "minimum_stock": 10,
            },
        ],
        "minimum_stock": 10,
    }

    result = execute_workflow(
        "Which products need restocking?",
        data,
    )

    assert result["status"] == "success"
    assert result["workflow_id"] == "WF001"
    assert len(result["output"]) == 1
    assert result["output"][0]["product"] == "Keyboard"
    assert result["output"][0]["reorder_quantity"] == 5


def test_inventory_needs_input():
    result = execute_workflow(
        "Which products need restocking?"
    )

    assert result["status"] == "needs_input"


def test_unknown_request():
    result = execute_workflow(
        "Tell me a joke about a penguin"
    )

    assert result["status"] in ("not_found", "not_implemented")


if __name__ == "__main__":
    test_inventory_restock()
    test_inventory_needs_input()
    test_unknown_request()
    print("All workflow engine tests passed.")
