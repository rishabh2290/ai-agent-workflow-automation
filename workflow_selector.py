
from rapidfuzz import fuzz
from workflow_loader import load_workflow_registry


SYNONYMS = {
    "failing": "failure failed errors unsuccessful",
    "failures": "failure failed errors unsuccessful",
    "failed": "failure failing errors unsuccessful",
    "often": "frequently frequent frequency",
    "workflows": "workflow execution performance logs",
    "workflow": "execution performance logs",
    "restocking": "reorder low-stock inventory stock",
    "products": "product items inventory",
    "duplicates": "duplicate similar matching",
    "duplicate": "duplicates similar matching",
    "seo": "search engine optimization meta description",
    "classify": "classification categorization categorize",
    "classifying": "classification categorization",
    "vendor": "supplier external",
    "price": "pricing cost",
    "brief": "summary campaign marketing",
    "assign": "assignment allocate employee",
    "urgent": "priority deadline",
    "keywords": "search terms seo",
    "invalid": "incorrect missing validation errors",
    "order": "purchase shipment delivery",
}


def expand_request(request):
    """Expand a request with common alternative terms."""
    words = request.lower().split()
    expanded_words = list(words)

    for word in words:
        clean_word = word.strip(".,!?;:'\"()[]{}")

        if clean_word in SYNONYMS:
            expanded_words.extend(SYNONYMS[clean_word].split())

    return " ".join(expanded_words)



def select_workflow(user_request):
    """
    Select a suitable workflow using phrase matching and fuzzy scoring.

    Returns:
        (workflow, score) when a suitable workflow is found.
        (None, score) when the request is unrelated or too ambiguous.
    """
    workflows = load_workflow_registry()
    request = user_request.strip().lower()

    if not request:
        return None, 0

    # Reject obvious conversational requests that are not workflow tasks.
    unrelated_phrases = [
        "tell me a joke",
        "write me a joke",
        "make me laugh",
        "tell me a story",
        "what is the weather",
        "who won the match",
    ]

    if any(phrase in request for phrase in unrelated_phrases):
        return None, 0

    # Preserve the existing vendor-file routing behavior.
    vendor_file_phrases = [
        "vendor spreadsheet",
        "vendor file",
        "vendor data",
        "invalid rows",
        "cleaned dataset",
        "process this vendor",
    ]

    if any(phrase in request for phrase in vendor_file_phrases):
        for workflow in workflows.values():
            if workflow["id"] == "WF003":
                return workflow, 100.0

    expanded_request = expand_request(request)

    best_workflow = None
    best_score = 0

    for workflow in workflows.values():
        fields = [
            workflow["name"],
            workflow["trigger"],
            workflow["inputs"],
            workflow["steps"],
            workflow["decision_logic"],
            workflow["tools_required"],
            workflow["expected_output"],
        ]

        non_empty_fields = [
            field.lower()
            for field in fields
            if field and field.strip()
        ]

        if not non_empty_fields:
            continue

        score = max(
            fuzz.token_set_ratio(expanded_request, field)
            for field in non_empty_fields
        )

        if score > best_score:
            best_score = score
            best_workflow = workflow

    # Require a stronger match than the previous threshold of 35.
    if best_score < 50:
        return None, best_score

    return best_workflow, best_score



if __name__ == "__main__":
    test_requests = [
        "Which products need restocking?",
        "Find products where vendor price differs by more than 10%.",
        "Process this vendor spreadsheet and show invalid rows.",
        "Generate SEO content for this product.",
        "Where is order ORD-1001?",
        "Find likely duplicate products in the catalog.",
        "Create a campaign brief for the new collection.",
        "Classify these keywords and map them to pages.",
        "Assign this urgent task to the best available developer.",
        "Which workflows are failing most often?",
    ]

   
    expected_ids = [
        "WF001",
        "WF002",
        "WF003",
        "WF004",
        "WF005",
        "WF006",
        "WF007",
        "WF008",
        "WF009",
        "WF010",
    ]

    correct = 0

    for request, expected_id in zip(test_requests, expected_ids):
        workflow, score = select_workflow(request)

        print(f"\nUser request: {request}")
        print(f"Expected workflow: {expected_id}")

        if workflow:
            print(f"Selected: {workflow['name']}")
            print(f"Workflow ID: {workflow['id']}")
            print(f"Match score: {score:.2f}")

            if workflow["id"] == expected_id:
                print("Result: PASS")
                correct += 1
            else:
                print("Result: FAIL")
        else:
            print("No suitable workflow found.")
            print(f"Best match score: {score:.2f}")
            print("Result: FAIL")

    print(f"\nRouting accuracy: {correct}/{len(test_requests)}")
