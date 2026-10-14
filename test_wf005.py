
from workflow_engine import execute_workflow

sample_orders = [
    {
        "order_id": "ORD-1001",
        "customer_email": "rahul@example.com",
        "status": "Shipped",
        "items": ["Wireless Keyboard", "Mouse"],
        "shipment": {
            "carrier": "BlueDart",
            "estimated_delivery": "2026-10-16",
        },
        "tracking_number": "BD123456789",
    },
    {
        "order_id": "ORD-1002",
        "customer_email": "priya@example.com",
        "status": "Processing",
        "items": ["Monitor"],
        "shipment": {
            "carrier": None,
            "estimated_delivery": None,
        },
        "tracking_number": None,
    },
]

# Test 1: Find an order by order ID.
result = execute_workflow(
    "Where is order ORD-1001?",
    data={
        "order_id": "ORD-1001",
        "orders": sample_orders,
    },
)

print("Status:", result["status"])
print("Workflow:", result.get("workflow_name"))
print("Steps:", result.get("steps"))
print("Output:", result.get("output", result.get("message")))

assert result["status"] == "success"
assert result["workflow_id"] == "WF005"
assert result["output"]["status"] == "Shipped"
assert result["output"]["tracking_number"] == "BD123456789"

# Test 2: Find an order by customer email.
email_result = execute_workflow(
    "Where is order ORD-1001?",
    data={
        "customer_email": "PRIYA@example.com",
        "orders": sample_orders,
    },
)

assert email_result["status"] == "success"
assert email_result["output"]["order_id"] == "ORD-1002"

# Test 3: Handle an unknown order.
missing_result = execute_workflow(
    "Where is order ORD-9999?",
    data={
        "order_id": "ORD-9999",
        "orders": sample_orders,
    },
)

assert missing_result["status"] == "not_found"

# Test 4: Ask for an identifier when none is supplied.
input_result = execute_workflow(
    "Where is order ORD-1001?",
    data={"orders": sample_orders},
)

assert input_result["status"] == "needs_input"

print("\nWF005 tests passed.")
