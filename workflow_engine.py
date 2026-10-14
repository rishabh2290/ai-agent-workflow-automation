from pathlib import Path
from workflow_selector import select_workflow
from workflow_loader import get_workflow
from tool_registry import run_tool
def execute_workflow(user_request, data=None, workflow_id_override=None):
    """Select a workflow and execute its supported logic.
    Args:
        user_request: Natural-language request used to select a workflow.
        data: Input data required by the selected workflow.
        workflow_id_override: Explicitly specify a workflow ID to execute.
    Returns:
        A dictionary describing the status, steps, and output.
    """
    if workflow_id_override is not None:
        # Use the LLM-selected workflow and skip fuzzy matching.
        workflow = get_workflow(workflow_id_override)
        score = 100.0  # Explicit selection is treated as a perfect match.
    else:
        workflow, score = select_workflow(user_request)
    if workflow is None:
        return {
            "status": "not_found",
            "message": "I could not identify a suitable workflow.",
            "match_score": score,
        }
    workflow_id = workflow["id"]
    steps = []
    data = data or {}
    try:
        if workflow_id == "WF001":
            if "products" not in data:
                return {
                    "status": "needs_input",
                    "workflow_id": workflow_id,
                    "workflow_name": workflow["name"],
                    "message": (
                        "Please provide product inventory data "
                        "and a minimum stock threshold."
                    ),
                }
            products = data["products"]
            minimum_stock = data.get("minimum_stock", 10)
            steps.append("Received inventory data.")
            restock_list = run_tool(
                "compare_stock",
                products=products,
                minimum_stock=minimum_stock,
            )
            steps.append("Compared stock against thresholds.")
            return {
                "status": "success",
                "workflow_id": workflow_id,
                "workflow_name": workflow["name"],
                "match_score": score,
                "steps": steps,
                "output": restock_list,
            }
        elif workflow_id == "WF002":
            if "products" not in data:
                return {
                    "status": "needs_input",
                    "workflow_id": workflow_id,
                    "workflow_name": workflow["name"],
                    "message": (
                        "Please provide product prices and "
                        "corresponding vendor prices."
                    ),
                }
            products = data["products"]
            exceptions = []
            steps.append("Received product and vendor prices.")
            for product in products:
                internal_price = float(product["internal_price"])
                vendor_price = float(product["vendor_price"])
                if internal_price <= 0:
                    raise ValueError(
                        "Internal prices must be greater than zero."
                    )
                difference = (
                    abs(vendor_price - internal_price)
                    / internal_price
                ) * 100
                if difference > 10:
                    exceptions.append({
                        "product": product.get(
                            "product_name", "Unknown"
                        ),
                        "internal_price": internal_price,
                        "vendor_price": vendor_price,
                        "difference_percent": round(difference, 2),
                    })
            steps.append(
                "Compared prices and identified exceptions."
            )
            return {
                "status": "success",
                "workflow_id": workflow_id,
                "workflow_name": workflow["name"],
                "match_score": score,
                "steps": steps,
                "output": exceptions,
            }
        elif workflow_id == "WF003":
            if not data.get("file_path"):
                return {
                    "status": "needs_input",
                    "workflow_id": workflow_id,
                    "workflow_name": workflow["name"],
                    "message": (
                        "Please provide a vendor CSV or Excel file path."
                    ),
                }
            steps.append("Received vendor file path.")
            rows = run_tool(
                "read_table",
                file_path=data["file_path"],
            )
            steps.append(
                "Loaded vendor file and normalized columns."
            )
            validation = run_tool(
                "validate_vendor_rows",
                rows=rows,
            )
            steps.append("Validated required vendor fields.")
            output_dir = Path("output")
            cleaned_file = output_dir / "cleaned_vendor.csv"
            invalid_file = output_dir / "invalid_vendor_rows.csv"
            clean_result = run_tool(
                "write_csv",
                rows=validation["valid_rows"],
                file_path=str(cleaned_file),
            )
            steps.append("Exported cleaned vendor data.")
            invalid_result = run_tool(
                "write_invalid_report",
                invalid_rows=validation["invalid_rows"],
                file_path=str(invalid_file),
            )
            steps.append("Exported invalid-row report.")
            return {
                "status": "success",
                "workflow_id": workflow_id,
                "workflow_name": workflow["name"],
                "match_score": score,
                "steps": steps,
                "output": {
                    **validation,
                    "files": {
                        "cleaned_vendor": clean_result,
                        "invalid_vendor_rows": invalid_result,
                    },
                },
            }
        elif workflow_id == "WF004":
            if not data.get("product"):
                return {
                    "status": "needs_input",
                    "workflow_id": workflow_id,
                    "workflow_name": workflow["name"],
                    "message": (
                        "Please provide product details, including "
                        "product_name and category."
                    ),
                }
            product = data["product"]
            steps.append("Received product details.")
            if not isinstance(product, dict):
                raise TypeError(
                    "Product details must be a dictionary."
                )
            if (
                not product.get("product_name")
                or not product.get("category")
            ):
                return {
                    "status": "needs_input",
                    "workflow_id": workflow_id,
                    "workflow_name": workflow["name"],
                    "message": (
                        "Product name and category are required "
                        "to generate product content."
                    ),
                }
            content = run_tool(
                "generate_product_content",
                product=product,
            )
            steps.append(
                "Validated required product attributes."
            )
            steps.append(
                "Generated product and SEO content."
            )
            return {
                "status": "success",
                "workflow_id": workflow_id,
                "workflow_name": workflow["name"],
                "match_score": score,
                "steps": steps,
                "output": content,
            }
        # WF005: Customer Order Status
        elif workflow_id == "WF005":
            order_id = data.get("order_id", "")
            customer_email = data.get("customer_email", "")
            orders = data.get("orders", [])
            if not order_id and not customer_email:
                return {
                    "status": "needs_input",
                    "workflow_id": workflow_id,
                    "workflow_name": workflow["name"],
                    "message": (
                        "Please provide an order ID or customer email."
                    ),
                }
            if not orders:
                return {
                    "status": "needs_input",
                    "workflow_id": workflow_id,
                    "workflow_name": workflow["name"],
                    "message": (
                        "Order data is not available. Please provide "
                        "the order records or connect an order database."
                    ),
                }
            steps.append("Received order lookup details.")
            result = run_tool(
                "lookup_order",
                orders=orders,
                order_id=order_id,
                customer_email=customer_email,
            )
            if not result["found"]:
                return {
                    "status": "not_found",
                    "workflow_id": workflow_id,
                    "workflow_name": workflow["name"],
                    "steps": steps,
                    "message": (
                        "No matching order was found. Please check "
                        "the order ID or provide another identifier."
                    ),
                }
            steps.append("Found matching order record.")
            order = result["order"]
            return {
                "status": "success",
                "workflow_id": workflow_id,
                "workflow_name": workflow["name"],
                "match_score": score,
                "steps": steps,
                "output": {
                    "order_id": order.get("order_id"),
                    "status": order.get("status"),
                    "items": order.get("items", []),
                    "shipment": order.get("shipment", {}),
                    "tracking_number": order.get("tracking_number"),
                },
            }
        elif workflow_id == "WF006":
            if "products" not in data:
                return {
                    "status": "needs_input",
                    "workflow_id": workflow_id,
                    "workflow_name": workflow["name"],
                    "message": (
                        "Please provide a product catalog to check "
                        "for duplicate products."
                    ),
                }
            products = data["products"]
            steps.append("Received product catalog.")
            if not isinstance(products, list):
                raise TypeError(
                    "Product catalog must be a list."
                )
            result = run_tool(
                "detect_duplicate_products",
                products=products,
            )
            steps.append(
                "Compared product SKUs, names, and attributes."
            )
            steps.append(
                "Grouped potential duplicate products."
            )
            return {
                "status": "success",
                "workflow_id": workflow_id,
                "workflow_name": workflow["name"],
                "match_score": score,
                "steps": steps,
                "output": result,
            }
        elif workflow_id == "WF007":
            campaign = data.get("campaign", {})
            if not isinstance(campaign, dict):
                raise TypeError(
                    "Campaign details must be a dictionary."
                )
            required_fields = [
                "goal",
                "start_date",
                "end_date",
            ]
            missing_fields = [
                field
                for field in required_fields
                if not str(campaign.get(field, "")).strip()
            ]
            if missing_fields:
                return {
                    "status": "needs_input",
                    "workflow_id": workflow_id,
                    "workflow_name": workflow["name"],
                    "missing_fields": missing_fields,
                    "message": (
                        "Please provide the campaign goal, start date, "
                        "and end date before generating the brief."
                    ),
                }
            steps.append("Received campaign details.")
            result = run_tool(
                "generate_campaign_brief",
                campaign=campaign,
            )
            steps.append(
                "Validated required campaign fields."
            )
            steps.append(
                "Generated campaign objective and product summary."
            )
            steps.append(
                "Prepared messaging recommendations and timeline."
            )
            return {
                "status": "success",
                "workflow_id": workflow_id,
                "workflow_name": workflow["name"],
                "match_score": score,
                "steps": steps,
                "output": result,
            }
        elif workflow_id == "WF008":
            if not data:
                data = {}
            keywords = data.get("keywords", [])
            category = data.get("category", "")
            output_path = data.get(
                "output_path",
                "output/seo_keyword_report.csv",
            )
            if not keywords:
                return {
                    "status": "needs_input",
                    "workflow_id": workflow_id,
                    "workflow_name": workflow["name"],
                    "message": (
                        "Please provide a list of keywords or a "
                        "keyword CSV file to classify."
                    ),
                }
            steps.append("Received SEO keywords and category.")
            if isinstance(keywords, str):
                rows = run_tool(
                    "read_table",
                    file_path=keywords,
                )
                if not rows:
                    return {
                        "status": "needs_input",
                        "workflow_id": workflow_id,
                        "workflow_name": workflow["name"],
                        "message": "The keyword file contains no rows.",
                    }
                keyword_column = next(
                    (
                        key
                        for key in rows[0].keys()
                        if key.strip().lower().replace(" ", "_")
                        in {"keyword", "keywords", "search_term"}
                    ),
                    None,
                )
                if not keyword_column:
                    raise ValueError(
                        "The keyword file must contain a "
                        "'keyword' or 'keywords' column."
                    )
                keywords = [
                    row[keyword_column]
                    for row in rows
                    if row.get(keyword_column)
                ]
                steps.append("Loaded keywords from the input file.")
            result = run_tool(
                "classify_seo_keywords",
                keywords=keywords,
                category=category,
                output_path=output_path,
            )
            steps.append("Removed duplicate keywords.")
            steps.append("Classified keyword search intent.")
            steps.append("Mapped keywords to suggested target pages.")
            steps.append("Assigned keyword priorities.")
            steps.append("Exported the SEO keyword report.")
            return {
                "status": "success",
                "workflow_id": workflow_id,
                "workflow_name": workflow["name"],
                "match_score": score,
                "steps": steps,
                "output": result,
            }
        # WF009: Employee Task Assignment
        elif workflow_id == "WF009":
            task = data.get("task", {})
            employees = data.get("employees", [])
            if not isinstance(task, dict):
                raise TypeError(
                    "Task details must be a dictionary."
                )
            if not task.get("required_skills"):
                return {
                    "status": "needs_input",
                    "workflow_id": workflow_id,
                    "workflow_name": workflow["name"],
                    "message": (
                        "Please provide the task's required skills."
                    ),
                }
            if not employees:
                return {
                    "status": "needs_input",
                    "workflow_id": workflow_id,
                    "workflow_name": workflow["name"],
                    "message": (
                        "Please provide the employee list, including "
                        "skills and workload information."
                    ),
                }
            steps.append("Received task and employee details.")
            result = run_tool(
                "assign_employee_task",
                task=task,
                employees=employees,
            )
            steps.append("Compared employee skills with task requirements.")
            steps.append("Evaluated employee availability and workload.")
            if result["assigned"]:
                steps.append("Selected the best eligible employee.")
                status = "success"
            else:
                steps.append("No eligible employee was found.")
                steps.append("Escalation is required.")
                status = "escalation_required"
            return {
                "status": status,
                "workflow_id": workflow_id,
                "workflow_name": workflow["name"],
                "match_score": score,
                "steps": steps,
                "output": result,
            }
        # WF010: Workflow Performance Report
        elif workflow_id == "WF010":
            logs = data.get("logs", [])
            slow_step_threshold = data.get(
                "slow_step_threshold",
                5.0,
            )
            if not logs:
                return {
                    "status": "needs_input",
                    "workflow_id": workflow_id,
                    "workflow_name": workflow["name"],
                    "message": (
                        "Please provide workflow execution logs "
                        "to generate a performance report."
                    ),
                }
            steps.append("Received workflow execution logs.")
            result = run_tool(
                "generate_performance_report",
                logs=logs,
                slow_step_threshold=slow_step_threshold,
            )
            steps.append("Calculated success and failure rates.")
            steps.append("Calculated average execution duration.")
            steps.append("Identified recurring errors and slow steps.")
            steps.append("Generated performance recommendations.")
            return {
                "status": "success",
                "workflow_id": workflow_id,
                "workflow_name": workflow["name"],
                "match_score": score,
                "steps": steps,
                "output": result,
            }
        else:
            return {
                "status": "not_implemented",
                "workflow_id": workflow_id,
                "workflow_name": workflow["name"],
                "message": (
                    "This workflow has been selected, but its "
                    "execution logic has not been implemented yet."
                ),
            }
    except (
        KeyError,
        TypeError,
        ValueError,
        FileNotFoundError,
    ) as error:
        return {
            "status": "error",
            "workflow_id": workflow_id,
            "workflow_name": workflow["name"],
            "message": str(error),
        }
if __name__ == "__main__":
    request = "Which products need restocking?"
    sample_data = {
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
            {
                "product_name": "Monitor",
                "current_stock": 3,
                "minimum_stock": 8,
            },
        ],
        "minimum_stock": 10,
    }
    result = execute_workflow(request, sample_data)
    print("\nWorkflow execution result:")
    print(f"Status: {result['status']}")
    print(f"Workflow: {result.get('workflow_name', 'N/A')}")
    if "steps" in result:
        for index, step in enumerate(result["steps"], start=1):
            print(f"{index}. {step}")
    print(
        "Output:",
        result.get("output", result.get("message")),
    )
