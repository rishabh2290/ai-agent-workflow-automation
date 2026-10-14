
import ast
import csv
import json
import operator
from pathlib import Path
from typing import Callable, Any

import pandas as pd




TOOLS: dict[str, Callable[..., Any]] = {}


def register_tool(name: str):
    """Register a Python function as a reusable agent tool."""

    def decorator(function: Callable[..., Any]):
        TOOLS[name] = function
        return function

    return decorator


def run_tool(tool_name: str, **kwargs):
    """Find a registered tool and execute it."""

    if tool_name not in TOOLS:
        raise ValueError(f"Unknown tool: {tool_name}")

    return TOOLS[tool_name](**kwargs)




@register_tool("calculator")
def calculator(expression: str):
    """Safely evaluate basic arithmetic expressions."""

    operations = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def evaluate(node):
        if (
            isinstance(node, ast.Constant)
            and type(node.value) in (int, float)
        ):
            return node.value

        if isinstance(node, ast.BinOp) and type(node.op) in operations:
            left = evaluate(node.left)
            right = evaluate(node.right)

            if isinstance(node.op, ast.Div) and right == 0:
                raise ValueError("Cannot divide by zero.")

            return operations[type(node.op)](left, right)

        if isinstance(node, ast.UnaryOp) and type(node.op) in operations:
            return operations[type(node.op)](evaluate(node.operand))

        raise ValueError("Unsupported arithmetic expression.")

    return evaluate(ast.parse(expression, mode="eval").body)




@register_tool("read_csv")
def read_csv(file_path: str):
    """Read a CSV file and return its rows as dictionaries."""

    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"CSV file not found: {path}")

    with path.open("r", newline="", encoding="utf-8-sig") as file:
        return list(csv.DictReader(file))



@register_tool("compare_stock")
def compare_stock(
    products: list[dict],
    minimum_stock: int
):
    """Find products below their minimum stock threshold."""

    restock_list = []

    for product in products:
        current_stock = int(product["current_stock"])
        threshold = int(product.get("minimum_stock", minimum_stock))

        if current_stock < threshold:
            restock_list.append({
                "product": product.get("product_name", "Unknown"),
                "current_stock": current_stock,
                "minimum_stock": threshold,
                "reorder_quantity": threshold - current_stock,
            })

    return restock_list



@register_tool("read_table")
def read_table(file_path: str):
    """Read a CSV or Excel file into a list of dictionaries."""

    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    suffix = path.suffix.lower()

    if suffix == ".csv":
        df = pd.read_csv(path)
    elif suffix in (".xlsx", ".xls"):
        df = pd.read_excel(path)
    else:
        raise ValueError("Unsupported file type. Use CSV or Excel.")

    
    df.columns = [
        str(column).strip().lower().replace(" ", "_")
        for column in df.columns
    ]

   
    df = df.astype(object).where(pd.notna(df), None)

    return df.to_dict(orient="records")


@register_tool("validate_vendor_rows")
def validate_vendor_rows(rows: list[dict]):
    """Separate valid vendor rows from invalid rows."""

    valid_rows = []
    invalid_rows = []

    for index, row in enumerate(rows, start=1):
        cleaned_row = {
            str(key).strip().lower().replace(" ", "_"): value
            for key, value in row.items()
        }

        sku = cleaned_row.get("sku")
        product_name = cleaned_row.get("product_name")

        errors = []

        if sku is None or not str(sku).strip():
            errors.append("Missing SKU")

        if product_name is None or not str(product_name).strip():
            errors.append("Missing product name")

        if errors:
            invalid_rows.append({
                "row_number": index,
                "row": cleaned_row,
                "errors": errors,
            })
        else:
            valid_rows.append(cleaned_row)

    return {
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
        "summary": {
            "total_rows": len(rows),
            "valid_count": len(valid_rows),
            "invalid_count": len(invalid_rows),
        },
    }




@register_tool("write_csv")
def write_csv(rows: list[dict], file_path: str):
    """Write rows to a CSV file, including headers when rows are empty."""

    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(dict.fromkeys(
        key for row in rows for key in row.keys()
    ))

    with path.open("w", newline="", encoding="utf-8-sig") as file:
        if not fieldnames:
            file.write("")
        else:
            writer = csv.DictWriter(
                file,
                fieldnames=fieldnames,
                extrasaction="ignore"
            )
            writer.writeheader()
            writer.writerows(rows)

    return {
        "file_path": str(path),
        "rows_written": len(rows),
    }



@register_tool("write_invalid_report")
def write_invalid_report(
    invalid_rows: list[dict],
    file_path: str
):
    """Save invalid vendor rows and their validation errors."""

    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = ["row_number", "row", "errors"]

    with path.open("w", newline="", encoding="utf-8-sig") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for item in invalid_rows:
            writer.writerow({
                "row_number": item.get("row_number"),
                "row": json.dumps(
                    item.get("row", {}),
                    ensure_ascii=False
                ),
                "errors": "; ".join(item.get("errors", [])),
            })

    return {
        "file_path": str(path),
        "rows_written": len(invalid_rows),
    }


@register_tool("generate_product_content")
def generate_product_content(product: dict):
    """Generate product content using only supplied attributes."""

    product_name = str(product.get("product_name", "")).strip()
    category = str(product.get("category", "")).strip()

    if not product_name or not category:
        raise ValueError("Product name and category are required.")

    attributes = {
        key: str(value).strip()
        for key, value in product.items()
        if key not in ("product_name", "category")
        and value is not None
        and str(value).strip()
    }

    attribute_text = ", ".join(
        f"{key.replace('_', ' ')}: {value}"
        for key, value in attributes.items()
    )

    if attribute_text:
        description = (
            f"{product_name} is a product in the {category} category. "
            f"Provided details: {attribute_text}. "
            "Please review the listed specifications before purchasing."
        )
    else:
        description = (
            f"{product_name} is a product in the {category} category. "
            "Additional product specifications have not been provided."
        )

    short_description = (
        f"{product_name} from the {category} category."
    )

    seo_title = f"{product_name} | {category}"[:60]

    meta_description = (
        f"Explore {product_name} in the {category} category. "
        "Review the available product details."
    )[:160]

    return {
        "product_name": product_name,
        "description": description,
        "short_description": short_description,
        "seo_title": seo_title,
        "meta_description": meta_description,
        "provided_attributes": attributes,
        "missing_attributes": [
            "material", "color", "target_audience"
        ] if not all(
            product.get(key)
            for key in ("material", "color", "target_audience")
        ) else [],
    }


@register_tool("lookup_order")
def lookup_order(
    orders: list[dict],
    order_id: str = "",
    customer_email: str = "",
):
    """Find an order by order ID or customer email."""

    order_id = order_id.strip().lower()
    customer_email = customer_email.strip().lower()

    if not order_id and not customer_email:
        raise ValueError("Provide an order ID or customer email.")

    for order in orders:
        stored_id = str(order.get("order_id", "")).strip().lower()
        stored_email = str(
            order.get("customer_email", "")
        ).strip().lower()

        # Prefer an exact order ID match when supplied.
        if order_id and stored_id == order_id:
            return {
                "found": True,
                "order": order,
            }

        if customer_email and stored_email == customer_email:
            return {
                "found": True,
                "order": order,
            }

    return {
        "found": False,
        "order": None,
    }



@register_tool("detect_duplicate_products")
def detect_duplicate_products(products: list[dict]):
    """Detect exact SKU duplicates and likely product duplicates."""

    from difflib import SequenceMatcher
    from itertools import combinations

    def normalize(value):
        if value is None:
            return ""
        return " ".join(str(value).lower().strip().split())

    duplicate_groups = []
    seen_pairs = set()

    for first, second in combinations(products, 2):
        sku1 = normalize(first.get("sku"))
        sku2 = normalize(second.get("sku"))

        name1 = normalize(first.get("product_name"))
        name2 = normalize(second.get("product_name"))

        # Skip records with no identifying information.
        if not any((sku1, name1)) or not any((sku2, name2)):
            continue

        # Create a stable key so the same pair isn't reported twice.
        def product_key(product):
            return (
                normalize(product.get("sku")),
                normalize(product.get("product_name")),
                normalize(product.get("brand")),
                normalize(product.get("category")),
                normalize(product.get("color")),
                normalize(product.get("material")),
            )

        key1 = product_key(first)
        key2 = product_key(second)
        pair_key = tuple(sorted((key1, key2)))

        if pair_key in seen_pairs:
            continue

        matching_fields = []
        confidence = 0
        duplicate_type = None

        # Exact SKU match is the strongest evidence.
        if sku1 and sku2 and sku1 == sku2:
            matching_fields.append("sku")
            confidence = 100
            duplicate_type = "definite"

        else:
            name_similarity = (
                SequenceMatcher(None, name1, name2).ratio()
                if name1 and name2
                else 0
            )

            if name_similarity >= 0.85:
                matching_fields.append("product_name")

            attribute_matches = []

            for field in ("brand", "category", "color", "material"):
                value1 = normalize(first.get(field))
                value2 = normalize(second.get(field))

                if value1 and value2 and value1 == value2:
                    attribute_matches.append(field)

            matching_fields.extend(attribute_matches)

            # Require a strong name match plus at least one matching
            # attribute before classifying as a likely duplicate.
            if name_similarity >= 0.85 and attribute_matches:
                confidence = round(
                    min(
                        99,
                        70 + (name_similarity - 0.85) * 100
                        + len(attribute_matches) * 3,
                    ),
                    2,
                )
                duplicate_type = "likely"

        if duplicate_type:
            seen_pairs.add(pair_key)

            duplicate_groups.append({
                "products": [first, second],
                "duplicate_type": duplicate_type,
                "confidence": confidence,
                "matching_fields": matching_fields,
            })

    return {
        "total_products": len(products),
        "duplicate_groups": duplicate_groups,
        "duplicate_group_count": len(duplicate_groups),
    }



@register_tool("generate_campaign_brief")
def generate_campaign_brief(campaign: dict):
    """Generate a structured marketing brief from supplied details."""

    goal = str(campaign.get("goal", "")).strip()
    products = campaign.get("products", [])
    audience = str(campaign.get("target_audience", "")).strip()
    promotion = str(campaign.get("promotion", "")).strip()
    start_date = str(campaign.get("start_date", "")).strip()
    end_date = str(campaign.get("end_date", "")).strip()

    missing_fields = []

    if not goal:
        missing_fields.append("goal")

    if not start_date:
        missing_fields.append("start_date")

    if not end_date:
        missing_fields.append("end_date")

    if missing_fields:
        raise ValueError(
            "Missing required campaign fields: "
            + ", ".join(missing_fields)
        )

    if not isinstance(products, list):
        raise ValueError("Products must be provided as a list.")

    product_summary = (
        ", ".join(str(product) for product in products)
        if products
        else "No products specified"
    )

    return {
        "campaign_name": campaign.get(
            "campaign_name", "Marketing Campaign"
        ),
        "objective": goal,
        "product_summary": product_summary,
        "target_audience": audience or "Not specified",
        "promotion": promotion or "No promotion specified",
        "campaign_period": {
            "start_date": start_date,
            "end_date": end_date,
        },
        "key_messaging": (
            f"Promote {product_summary} to "
            f"{audience or 'the intended audience'} "
            f"with the objective: {goal}"
        ),
        "recommended_channels": [
            "Email marketing",
            "Social media",
            "Website or landing page",
        ],
        "timeline": [
            {
                "phase": "Preparation",
                "task": "Finalize campaign assets and messaging",
            },
            {
                "phase": "Launch",
                "task": "Publish campaign across selected channels",
            },
            {
                "phase": "Monitoring",
                "task": "Review engagement and campaign performance",
            },
        ],
        "notes": (
            "Channel recommendations and timeline are a starting point. "
            "Review them against the campaign budget and audience."
        ),
    }


@register_tool("classify_seo_keywords")
def classify_seo_keywords(keywords, category="", output_path="output/seo_keyword_report.csv"):
    """Classify SEO keywords, deduplicate them, and export a report."""

    import csv
    import re
    from pathlib import Path

    if not isinstance(keywords, list):
        raise ValueError("Keywords must be provided as a list.")

    if not keywords:
        raise ValueError("Please provide at least one keyword.")

    def classify_intent(keyword):
        text = keyword.lower().strip()

        navigational_terms = [
            "login", "log in", "official website", "website",
            "brand site",
        ]
        transactional_terms = [
            "buy", "purchase", "order", "price", "discount",
            "coupon", "deal", "for sale", "shop",
        ]
        commercial_terms = [
            "best", "top", "review", "reviews", "vs",
            "versus", "comparison", "recommended",
        ]

        if any(term in text for term in navigational_terms):
            return "navigational"

        if any(term in text for term in transactional_terms):
            return "transactional"

        if any(term in text for term in commercial_terms):
            return "commercial"

        return "informational"

    def suggest_target_page(keyword, intent):
        text = keyword.lower()

        if intent == "navigational":
            return "Homepage or brand page"

        if intent == "transactional":
            return "Product or category page"

        if intent == "commercial":
            return "Comparison or buying guide"

        if any(term in text for term in [
            "how to", "what is", "why", "guide", "tutorial"
        ]):
            return "Blog or informational guide"

        if category.strip():
            return f"{category.strip()} category guide"

        return "Relevant informational page"

    def calculate_priority(keyword, intent):
        text = keyword.lower()

        high_intent_terms = [
            "buy", "purchase", "order", "price",
            "discount", "best",
        ]

        if intent == "transactional":
            return "High"

        if intent == "commercial":
            return "High" if any(
                term in text for term in high_intent_terms
            ) else "Medium"

        if intent == "navigational":
            return "Medium"

        return "Low"

    # Normalize and deduplicate while preserving the original order.
    unique_keywords = []
    seen = set()

    for item in keywords:
        if isinstance(item, dict):
            raw_keyword = item.get("keyword", "")
        else:
            raw_keyword = item

        keyword = re.sub(r"\s+", " ", str(raw_keyword)).strip()

        if not keyword:
            continue

        normalized = keyword.casefold()

        if normalized not in seen:
            seen.add(normalized)
            unique_keywords.append(keyword)

    if not unique_keywords:
        raise ValueError("No valid keywords were found.")

    report = []

    for keyword in unique_keywords:
        intent = classify_intent(keyword)

        report.append({
            "keyword": keyword,
            "search_intent": intent,
            "category": category.strip() or "Unspecified",
            "target_page": suggest_target_page(keyword, intent),
            "priority": calculate_priority(keyword, intent),
        })

    # Export the report.
    file_path = Path(output_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "keyword",
        "search_intent",
        "category",
        "target_page",
        "priority",
    ]

    with file_path.open(
        "w", newline="", encoding="utf-8-sig"
    ) as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(report)

    return {
        "total_input_keywords": len(keywords),
        "unique_keywords": len(report),
        "duplicates_removed": len(keywords) - len(report),
        "report_file": str(file_path),
        "keywords": report,
    }


@register_tool("assign_employee_task")
def assign_employee_task(
    task,
    employees,
):
    """Rank employees by skill match and available capacity."""

    if not isinstance(task, dict):
        raise ValueError("Task details must be a dictionary.")

    if not isinstance(employees, list):
        raise ValueError("Employees must be provided as a list.")

    required_skills = {
        str(skill).strip().lower()
        for skill in task.get("required_skills", [])
        if str(skill).strip()
    }

    if not required_skills:
        raise ValueError(
            "Please provide at least one required skill for the task."
        )

    if not employees:
        return {
            "assigned": False,
            "status": "escalation_required",
            "message": "No employees are available for assignment.",
            "candidates": [],
        }

    candidates = []

    for employee in employees:
        if not isinstance(employee, dict):
            continue

        name = str(employee.get("name", "")).strip()
        skills = {
            str(skill).strip().lower()
            for skill in employee.get("skills", [])
            if str(skill).strip()
        }

        try:
            workload = float(employee.get("workload", 100))
            capacity = float(employee.get("capacity", 100))
        except (TypeError, ValueError):
            continue

        if not name or workload < 0 or capacity <= 0:
            continue

        matched_skills = required_skills.intersection(skills)
        skill_score = len(matched_skills) / len(required_skills)
        available_capacity = max(0, capacity - workload)

        candidates.append({
            "name": name,
            "matched_skills": sorted(matched_skills),
            "missing_skills": sorted(required_skills - skills),
            "skill_match_percent": round(skill_score * 100, 2),
            "workload": workload,
            "available_capacity": available_capacity,
            "eligible": (
                skill_score == 1.0
                and available_capacity > 0
            ),
        })

    eligible_candidates = [
        candidate
        for candidate in candidates
        if candidate["eligible"]
    ]

    eligible_candidates.sort(
        key=lambda candidate: (
            -candidate["skill_match_percent"],
            -candidate["available_capacity"],
            candidate["workload"],
            candidate["name"].lower(),
        )
    )

    if not eligible_candidates:
        candidates.sort(
            key=lambda candidate: (
                -candidate["skill_match_percent"],
                -candidate["available_capacity"],
                candidate["workload"],
            )
        )

        return {
            "assigned": False,
            "status": "escalation_required",
            "message": (
                "No employee has all required skills and available "
                "capacity. Review the task or escalate it."
            ),
            "candidates": candidates,
        }

    selected = eligible_candidates[0]

    return {
        "assigned": True,
        "status": "assigned",
        "task": task.get("title", "Untitled task"),
        "employee": selected["name"],
        "reason": (
            "The selected employee has all required skills and "
            "the highest available capacity among eligible candidates."
        ),
        "priority": task.get("priority", "Normal"),
        "deadline": task.get("deadline", "Not specified"),
        "matched_skills": selected["matched_skills"],
        "available_capacity": selected["available_capacity"],
        "candidates": candidates,
    }



@register_tool("generate_performance_report")
def generate_performance_report(logs, slow_step_threshold=5.0):
    """Analyze workflow execution logs and generate a report."""

    if not isinstance(logs, list):
        raise ValueError("Execution logs must be provided as a list.")

    if not logs:
        raise ValueError("Please provide at least one execution log.")

    if slow_step_threshold < 0:
        raise ValueError("The slow-step threshold cannot be negative.")

    total = len(logs)
    successes = 0
    failures = 0
    durations = []
    error_counts = {}
    slow_steps = []
    workflow_counts = {}

    for index, log in enumerate(logs, start=1):
        if not isinstance(log, dict):
            raise ValueError(
                f"Execution log {index} must be a dictionary."
            )

        status = str(log.get("status", "")).lower()

        if status in {"success", "completed"}:
            successes += 1
        elif status in {"failed", "failure", "error"}:
            failures += 1

        workflow_name = log.get(
            "workflow_name",
            log.get("workflow_id", "Unknown workflow"),
        )
        workflow_counts.setdefault(
            str(workflow_name),
            {"total": 0, "failures": 0},
        )
        workflow_counts[str(workflow_name)]["total"] += 1

        if status in {"failed", "failure", "error"}:
            workflow_counts[str(workflow_name)]["failures"] += 1

        duration = log.get("duration_seconds")

        if duration is not None:
            try:
                duration = float(duration)
            except (TypeError, ValueError):
                raise ValueError(
                    f"Invalid duration in execution log {index}."
                )

            if duration < 0:
                raise ValueError(
                    f"Duration cannot be negative in log {index}."
                )

            durations.append(duration)

        error = log.get("error")

        if error:
            error_text = str(error)
            error_counts[error_text] = (
                error_counts.get(error_text, 0) + 1
            )

        for step in log.get("steps", []):
            if not isinstance(step, dict):
                continue

            step_name = step.get("name", "Unknown step")
            step_duration = step.get("duration_seconds")

            if step_duration is None:
                continue

            try:
                step_duration = float(step_duration)
            except (TypeError, ValueError):
                continue

            if step_duration >= slow_step_threshold:
                slow_steps.append({
                    "workflow": str(workflow_name),
                    "step": str(step_name),
                    "duration_seconds": step_duration,
                })

    failure_rate = failures / total * 100
    success_rate = successes / total * 100
    average_duration = (
        sum(durations) / len(durations)
        if durations else None
    )

    frequent_errors = sorted(
        [
            {"error": error, "count": count}
            for error, count in error_counts.items()
        ],
        key=lambda item: item["count"],
        reverse=True,
    )

    workflow_summary = []

    for name, counts in workflow_counts.items():
        rate = counts["failures"] / counts["total"] * 100
        workflow_summary.append({
            "workflow": name,
            "total_runs": counts["total"],
            "failures": counts["failures"],
            "failure_rate_percent": round(rate, 2),
        })

    recommendations = []

    if failure_rate > 10:
        recommendations.append(
            "Investigate failures because the overall failure rate "
            "exceeds 10%."
        )

    if average_duration is not None and average_duration > slow_step_threshold:
        recommendations.append(
            "Review execution duration and identify opportunities "
            "to optimize slow workflows."
        )

    if frequent_errors:
        recommendations.append(
            "Investigate recurring errors and add validation or "
            "error handling where appropriate."
        )

    if slow_steps:
        recommendations.append(
            "Profile the slow steps listed in the report."
        )

    if not recommendations:
        recommendations.append(
            "No threshold-based issues were identified in these logs."
        )

    return {
        "total_executions": total,
        "successful_executions": successes,
        "failed_executions": failures,
        "success_rate_percent": round(success_rate, 2),
        "failure_rate_percent": round(failure_rate, 2),
        "average_duration_seconds": (
            round(average_duration, 2)
            if average_duration is not None else None
        ),
        "frequent_errors": frequent_errors,
        "slow_steps": slow_steps,
        "workflow_summary": workflow_summary,
        "recommendations": recommendations,
        "thresholds": {
            "failure_rate_percent": 10,
            "slow_step_seconds": slow_step_threshold,
        },
    }


if __name__ == "__main__":
    print("Registered tools:", list(TOOLS.keys()))

    print("\nCalculator test:")
    print(run_tool("calculator", expression="100 - 25 * 2"))

    print("\nStock comparison test:")
    products = [
        {"product_name": "Keyboard", "current_stock": "5"},
        {"product_name": "Mouse", "current_stock": "20"},
    ]

    print(run_tool(
        "compare_stock",
        products=products,
        minimum_stock=10,
    ))

    print("\nCSV writer test:")
    test_output = Path("output") / "test_output.csv"

    print(run_tool(
        "write_csv",
        rows=[
            {"sku": "SKU001", "product_name": "Keyboard"},
        ],
        file_path=str(test_output),
    ))

    print("\nAll basic tests completed.")
