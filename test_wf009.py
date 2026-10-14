
from pprint import pprint
from workflow_engine import execute_workflow

task = {
    "title": "Build customer support API",
    "required_skills": ["Python", "FastAPI"],
    "priority": "Urgent",
    "deadline": "2026-10-20",
}

employees = [
    {
        "name": "Aman",
        "skills": ["Python", "FastAPI", "SQL"],
        "workload": 80,
        "capacity": 100,
    },
    {
        "name": "Priya",
        "skills": ["Python", "FastAPI", "Django"],
        "workload": 40,
        "capacity": 100,
    },
    {
        "name": "Rahul",
        "skills": ["JavaScript", "React"],
        "workload": 20,
        "capacity": 100,
    },
]

print("\n--- TEST 1: ASSIGN TASK ---")

result = execute_workflow(
    "Assign this urgent task to the best available developer.",
    data={
        "task": task,
        "employees": employees,
    },
)

pprint(result)

assert result["status"] == "success"
assert result["workflow_id"] == "WF009"
assert result["output"]["employee"] == "Priya"

print("\n--- TEST 2: ESCALATE TASK ---")

result = execute_workflow(
    "Assign this urgent task to the best available developer.",
    data={
        "task": {
            "title": "Build a mobile application",
            "required_skills": ["Swift", "iOS"],
            "priority": "Urgent",
        },
        "employees": employees,
    },
)

pprint(result)

assert result["status"] == "escalation_required"
assert result["output"]["assigned"] is False

print("\nBoth WF009 tests passed!")

