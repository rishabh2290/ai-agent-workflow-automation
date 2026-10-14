
from pathlib import Path
import pandas as pd


# Find the Excel file
BASE_DIR = Path(__file__).parent
EXCEL_FILE = BASE_DIR / "workflows" / "workflow_assessment.xlsx"


def clean_value(value):
    """Convert Excel cell values into safe Python values."""

    if pd.isna(value):
        return ""

    return str(value).strip()


def load_workflow_registry():
    """Load Excel workflows into a dictionary indexed by workflow ID."""

    if not EXCEL_FILE.exists():
        raise FileNotFoundError(
            f"Workflow Excel file not found: {EXCEL_FILE}"
        )

    df = pd.read_excel(
        EXCEL_FILE,
        sheet_name="Workflows"
    )

    required_columns = [
        "Workflow_ID",
        "Workflow_Name",
        "Trigger",
        "Inputs",
        "Steps",
        "Decision_Logic",
        "Tools_Required",
        "Expected_Output",
    ]

    missing = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing:
        raise ValueError(
            f"Missing required Excel columns: {missing}"
        )

    registry = {}

    for _, row in df.iterrows():
        workflow_id = clean_value(row["Workflow_ID"])

        if not workflow_id:
            raise ValueError("A workflow has an empty ID.")

        if workflow_id in registry:
            raise ValueError(
                f"Duplicate workflow ID: {workflow_id}"
            )

        registry[workflow_id] = {
            "id": workflow_id,
            "name": clean_value(row["Workflow_Name"]),
            "trigger": clean_value(row["Trigger"]),
            "inputs": clean_value(row["Inputs"]),
            "steps": clean_value(row["Steps"]),
            "decision_logic": clean_value(
                row["Decision_Logic"]
            ),
            "tools_required": clean_value(
                row["Tools_Required"]
            ),
            "expected_output": clean_value(
                row["Expected_Output"]
            ),
        }

    return registry


def get_workflow(workflow_id):
    """Retrieve one workflow using its ID."""

    registry = load_workflow_registry()

    if workflow_id not in registry:
        raise ValueError(
            f"Unknown workflow ID: {workflow_id}"
        )

    return registry[workflow_id]


def load_test_questions():
    """Load the assignment's test questions."""

    if not EXCEL_FILE.exists():
        raise FileNotFoundError(
            f"Workflow Excel file not found: {EXCEL_FILE}"
        )

    df = pd.read_excel(
        EXCEL_FILE,
        sheet_name="Test_Questions"
    )

    return df.to_dict(orient="records")


if __name__ == "__main__":
    workflows = load_workflow_registry()

    print(f"Loaded {len(workflows)} workflows.\n")

    for workflow_id, workflow in workflows.items():
        print(f"{workflow_id}: {workflow['name']}")

    print("\nTesting workflow lookup...")

    workflow = get_workflow("WF001")

    print(f"Selected: {workflow['name']}")
    print(f"Steps: {workflow['steps']}")

    questions = load_test_questions()
    print(f"\nLoaded {len(questions)} test questions.")
