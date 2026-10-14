
from pathlib import Path
import pandas as pd


BASE_DIR = Path(__file__).parent
EXCEL_FILE = BASE_DIR / "workflows" / "workflow_assessment.xlsx"


def load_workflows():
    """Load workflow definitions and test questions from Excel."""

    if not EXCEL_FILE.exists():
        raise FileNotFoundError(
            f"Excel file not found: {EXCEL_FILE}"
        )

    
    workflows = pd.read_excel(
        EXCEL_FILE,
        sheet_name="Workflows"
    )

    test_questions = pd.read_excel(
        EXCEL_FILE,
        sheet_name="Test_Questions"
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
        if column not in workflows.columns
    ]

    if missing:
        raise ValueError(f"Missing columns: {missing}")

    
    if workflows["Workflow_ID"].duplicated().any():
        raise ValueError("Duplicate workflow IDs found.")

    return workflows, test_questions


if __name__ == "__main__":
    workflows, test_questions = load_workflows()

    print("\n===== WORKFLOWS LOADED =====")
    print(f"Total workflows: {len(workflows)}")

    for _, workflow in workflows.iterrows():
        print(f"\n{workflow['Workflow_ID']}: "
              f"{workflow['Workflow_Name']}")
        print(f"Trigger: {workflow['Trigger']}")
        print(f"Inputs: {workflow['Inputs']}")
        print(f"Steps: {workflow['Steps']}")
        print(f"Decision logic: {workflow['Decision_Logic']}")
        print(f"Tools: {workflow['Tools_Required']}")
        print(f"Expected output: {workflow['Expected_Output']}")

    print("\n===== TEST QUESTIONS =====")
    print(f"Total test questions: {len(test_questions)}")

    for _, question in test_questions.iterrows():
        print(f"\n{question['Workflow_ID']}: "
              f"{question['Test_Request']}")
        print(f"Check: {question['What_To_Check']}")
