# AI Agent Workflow Automation

## Project Overview

AI Agent Workflow Automation is a Python-based application that identifies and executes predefined business workflows based on a user's request. It uses workflow selection, registered tools, validation rules, and a Streamlit interface to automate common business operations.

## Features

- Selects a suitable workflow from a natural-language request.
- Loads workflow definitions and test questions from an Excel workbook.
- Executes workflows through a central workflow engine and tool registry.
- Provides a Streamlit interface for user interaction.
- Validates inputs and reports missing information.
- Generates structured outputs and CSV reports.
- Includes individual tests for workflow functionality.

## Workflows

1. **Inventory Restock Check** — identifies products that need restocking.
2. **Product Price Validation** — compares internal and vendor prices.
3. **Vendor File Processing** — validates vendor records and exports clean and invalid rows.
4. **Product Description Generator** — generates product descriptions and SEO content.
5. **Customer Order Status** — looks up an order in supplied order data.
6. **Duplicate Product Detection** — identifies potential duplicate products.
7. **Marketing Campaign Brief** — prepares a campaign brief from supplied details.
8. **SEO Keyword Classification** — classifies keywords and generates a CSV report.
9. **Employee Task Assignment** — recommends an eligible employee based on skills and workload.
10. **Workflow Performance Report** — analyzes supplied execution logs and generates performance metrics.

## Technology Stack

- Python
- Streamlit
- Pandas
- OpenPyXL
- RapidFuzz
- pytest
- Excel and CSV files

## Project Structure

```text
ai-agent-workflow-automation/
├── app.py
├── workflow_engine.py
├── workflow_selector.py
├── workflow_loader.py
├── tool_registry.py
├── workflows/
│   └── workflow_assessment.xlsx
├── data/
├── output/
├── tests/
├── requirements.txt
└── README.md
```

The structure above is representative. The project may also contain individual workflow test scripts and other supporting files.

## Setup and Installation

### 1. Open the project directory

```powershell
cd C:\Users\Acer\ai-agent-workflow-automation
```

### 2. Activate the virtual environment

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
pip install -r requirements.txt
```

## Run the Application

Start the Streamlit application with:

```powershell
streamlit run app.py
```

Open the local URL displayed in the terminal, usually:

```text
http://localhost:8501
```

Select a workflow, provide the required inputs, execute it, and review the result.

## Run Tests

Run the workflow engine test:

```powershell
python tests/test_workflow_engine.py
```

Run individual workflow tests as applicable:

```powershell
python test_vendor_tools.py
python test_wf002.py
python test_wf003.py
python test_wf004.py
python test_wf005.py
python test_wf006.py
python test_wf007.py
python test_wf008.py
python test_wf009.py
python test_wf010.py
```

## Limitations

- Workflow selection relies on text matching and similarity scoring.
- Product content and campaign briefs use predefined logic rather than requiring a live generative AI model.
- Order lookup uses the data provided to the application; it is not connected to a live order-management system.
- SEO classification uses rules and does not fetch live search-volume data.
- Employee assignment uses the supplied skills and workload information; it does not create tasks in an external project-management system.
- Performance reporting analyzes provided logs rather than automatically collecting production monitoring data.

## Future Improvements

- Integrate an LLM for more flexible reasoning and content generation.
- Add persistent storage for workflow execution history.
- Integrate external business APIs.
- Add authentication and role-based access control.
- Improve monitoring, logging, and error reporting.

## Project Status

The workflow engine and individual workflow tests have been exercised locally. Further validation should be performed before production deployment.