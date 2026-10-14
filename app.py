import json
import streamlit as st

from llm_agent import run_llm_agent
from workflow_loader import load_workflow_registry


st.set_page_config(
    page_title="AI Agent Workflow Automation",
    page_icon="🤖",
    layout="wide",
)

st.title("🤖 AI Agent Workflow Automation")
st.write(
    "Choose a business workflow, provide input data, and let the OpenRouter "
    "LLM agent select the matching workflow before Python tools execute it."
)



try:
    workflows = load_workflow_registry()
except Exception as error:
    st.error(f"Could not load workflows: {error}")
    st.stop()

if not workflows:
    st.error("No workflows were found.")
    st.stop()


examples = {
    "WF001": {
        "products": [
            {"product_name": "Keyboard", "current_stock": 5, "minimum_stock": 10},
            {"product_name": "Mouse", "current_stock": 20, "minimum_stock": 10},
        ],
        "minimum_stock": 10,
    },
    "WF002": {
        "products": [
            {"product_name": "Keyboard", "internal_price": 1000, "vendor_price": 1200},
            {"product_name": "Mouse", "internal_price": 500, "vendor_price": 520},
        ],
    },
    "WF003": {"file_path": "data/vendor_products.csv"},
    "WF004": {
        "product": {
            "product_name": "Wireless Headphones",
            "category": "Electronics",
            "features": ["Bluetooth connectivity", "Long battery life", "Lightweight design"],
        },
    },
    "WF005": {
        "order_id": "ORD1001",
        "customer_email": "customer@example.com",
        "orders": [
            {
                "order_id": "ORD1001",
                "customer_email": "customer@example.com",
                "status": "Shipped",
                "items": ["Keyboard"],
            },
        ],
    },
    "WF006": {
        "products": [
            {"product_name": "Wireless Mouse", "sku": "MOU001", "brand": "TechBrand"},
            {"product_name": "Wireless Mouse", "sku": "MOU001", "brand": "TechBrand"},
            {"product_name": "Keyboard", "sku": "KEY001", "brand": "TechBrand"},
        ],
    },
    "WF007": {
        "campaign": {
            "goal": "Increase product sales",
            "products": ["Wireless Headphones"],
            "target_audience": "Young professionals",
            "promotion": "10% discount",
            "start_date": "2026-11-01",
            "end_date": "2026-11-30",
        },
    },
    "WF008": {
        "keywords": [
            "buy running shoes",
            "best sports shoes",
            "running shoes for men",
            "cheap running shoes",
        ],
        "category": "Footwear",
        "output_path": "output/test_seo_keyword_report.csv",
    },
    "WF009": {
        "task": {
            "title": "Build a product landing page",
            "required_skills": ["Python", "React"],
            "priority": "High",
            "deadline": "2026-11-15",
        },
        "employees": [
            {"name": "Aman", "skills": ["Python", "React", "SQL"], "workload": 40, "capacity": 100},
            {"name": "Priya", "skills": ["Python", "Django"], "workload": 85, "capacity": 100},
        ],
    },
    "WF010": {
        "logs": [
            {"workflow_id": "WF001", "status": "success", "duration": 2.5},
            {"workflow_id": "WF002", "status": "success", "duration": 3.2},
            {"workflow_id": "WF001", "status": "error", "duration": 7.0, "error": "Missing input data"},
        ],
        "slow_step_threshold": 5.0,
    },
}


with st.sidebar:
    st.header("📋 Available Workflows")
    st.metric("Total Workflows", len(workflows))
    st.divider()
    for workflow in workflows.values():
        st.write(f"**{workflow['id']}** — {workflow['name']}")


st.subheader("1. Choose a Workflow")

workflow_options = {
    f"{workflow['id']} — {workflow['name']}": workflow
    for workflow in workflows.values()
}
selected_label = st.selectbox("Select workflow", options=list(workflow_options.keys()))
selected_workflow = workflow_options[selected_label]
workflow_id = selected_workflow["id"]

st.info(f"Selected: {workflow_id} — {selected_workflow['name']}")

default_requests = {
    "WF001": "Which products need restocking?",
    "WF002": "Check whether product prices differ from vendor prices by more than 10%.",
    "WF003": "Process and validate the vendor file.",
    "WF004": "Generate a product description.",
    "WF005": "Check the status of order ORD1001.",
    "WF006": "Find duplicate products.",
    "WF007": "Generate a marketing campaign brief.",
    "WF008": "Classify SEO keywords by search intent.",
    "WF009": "Assign the task to the most suitable employee.",
    "WF010": "Generate a workflow performance report.",
}

user_request = st.text_input(
    "2. Describe your request",
    value=default_requests.get(workflow_id, ""),
    key=f"request_{workflow_id}",
)

st.subheader("3. Provide Input Data")
input_data = None

if workflow_id == "WF001":
    st.caption("Enter inventory details.")
    product_name = st.text_input("Product name", value="Keyboard", key="inventory_name")
    current_stock = st.number_input("Current stock", min_value=0, value=5, step=1, key="inventory_stock")
    minimum_stock = st.number_input("Minimum stock", min_value=0, value=10, step=1, key="inventory_minimum")
    input_data = {
        "products": [{
            "product_name": product_name,
            "current_stock": current_stock,
            "minimum_stock": minimum_stock,
        }],
        "minimum_stock": minimum_stock,
    }

elif workflow_id == "WF002":
    st.caption("Add product prices. You can include multiple products.")
    if "price_products" not in st.session_state:
        st.session_state.price_products = [
            {"product_name": "Keyboard", "internal_price": 1000.0, "vendor_price": 1200.0}
        ]

    products_to_remove = []
    for index, product in enumerate(st.session_state.price_products):
        with st.container(border=True):
            st.markdown(f"**Product {index + 1}**")
            col1, col2, col3 = st.columns(3)
            product["product_name"] = col1.text_input(
                "Product name", value=product["product_name"], key=f"price_name_{index}"
            )
            product["internal_price"] = col2.number_input(
                "Internal price (₹)", min_value=0.0, value=float(product["internal_price"]),
                key=f"price_internal_{index}",
            )
            product["vendor_price"] = col3.number_input(
                "Vendor price (₹)", min_value=0.0, value=float(product["vendor_price"]),
                key=f"price_vendor_{index}",
            )
            if st.button("Remove product", key=f"remove_price_{index}"):
                products_to_remove.append(index)

    for index in reversed(products_to_remove):
        st.session_state.price_products.pop(index)
    if products_to_remove:
        st.rerun()

    col_add, col_reset = st.columns(2)
    if col_add.button("➕ Add product"):
        st.session_state.price_products.append(
            {"product_name": "", "internal_price": 0.0, "vendor_price": 0.0}
        )
        st.rerun()
    if col_reset.button("Reset products"):
        st.session_state.price_products = [
            {"product_name": "Keyboard", "internal_price": 1000.0, "vendor_price": 1200.0}
        ]
        st.rerun()

    input_data = {"products": st.session_state.price_products}

else:
    st.caption("Edit the example JSON to provide data for this workflow.")
    json_input = st.text_area(
        "Workflow Input JSON",
        value=json.dumps(examples.get(workflow_id, {}), indent=4),
        height=280,
        key=f"json_{workflow_id}",
    )
    try:
        input_data = json.loads(json_input) if json_input.strip() else {}
        if not isinstance(input_data, dict):
            st.error("Input JSON must be a JSON object.")
            input_data = None
    except json.JSONDecodeError:
        st.error("Invalid JSON. Check quotation marks, commas, brackets, and braces.")
        input_data = None


st.divider()
execute_button = st.button("▶ Execute Workflow with AI Agent", type="primary", use_container_width=True)

if execute_button:
    if not user_request.strip():
        st.warning("Please enter a request.")
    elif input_data is None:
        st.warning("Please correct the input data.")
    elif workflow_id == "WF002" and not input_data.get("products"):
        st.warning("Please add at least one product.")
    else:
        try:
            with st.spinner("The LLM is selecting a workflow and the Python engine is executing it..."):
                result = run_llm_agent(user_request, data=input_data)

            st.divider()
            st.header("4. Execution Results")

            status = result.get("status", "unknown")
            if status == "success":
                st.success("Workflow executed successfully.")
            elif status == "needs_input":
                st.warning("Additional input is required.")
            elif status == "escalation_required":
                st.warning("Manual review or escalation is required.")
            elif status == "not_found":
                st.warning(result.get("message", "No suitable workflow was found."))
            else:
                st.error(result.get("message", "The workflow could not be completed."))

            col1, col2, col3 = st.columns(3)
            col1.metric("Workflow ID", result.get("selected_workflow_id", result.get("workflow_id", "N/A")))
            col2.metric("Execution Status", status.upper())
            match_score = result.get("match_score")
            col3.metric(
                "Match Score",
                f"{match_score:.1f}%" if isinstance(match_score, (int, float)) else "N/A",
            )

            st.write(
                "**Selected Workflow:**",
                result.get("selected_workflow_name", result.get("workflow_name", "N/A")),
            )

            if result.get("selection_method"):
                st.write("**Selection Method:**", result["selection_method"])
            if result.get("selection_reason"):
                st.write("**LLM Selection Reason:**", result["selection_reason"])

            if result.get("steps"):
                st.subheader("Execution Steps")
                for index, step in enumerate(result["steps"], start=1):
                    st.write(f"{index}. {step}")

            if "output" in result:
                st.subheader("Workflow Output")
                st.json(result["output"])

            if result.get("message"):
                st.info(result["message"])
            if result.get("missing_fields"):
                st.warning("Missing fields: " + ", ".join(result["missing_fields"]))

            # The form fields are based on the dropdown selection. Warn if the LLM
            # routed the request to a different workflow to avoid executing mismatched data.
            selected_by_llm = result.get("selected_workflow_id")
            if selected_by_llm and selected_by_llm != workflow_id:
                st.warning(
                    f"The LLM selected {selected_by_llm}, but the form data is for "
                    f"{workflow_id}. Select the matching workflow and try again so "
                    "the input data is appropriate for the selected workflow."
                )

        except Exception as error:
            st.error(f"Application error: {type(error).__name__}: {error}")
