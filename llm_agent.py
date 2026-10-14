
import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from workflow_loader import load_workflow_registry, get_workflow
from workflow_engine import execute_workflow


load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "nvidia/nemotron-3.5-lightning:free",
)

if not API_KEY:
    raise ValueError(
        "OPENROUTER_API_KEY is missing from your .env file."
    )

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)


def select_workflow_tool_schema(registry):
    """Build the LLM tool schema from the Excel workflow registry."""

    workflow_ids = list(registry.keys())

    workflow_details = [
        {
            "id": workflow["id"],
            "name": workflow["name"],
            "trigger": workflow["trigger"],
            "inputs": workflow["inputs"],
            "steps": workflow["steps"],
            "decision_logic": workflow["decision_logic"],
            "tools_required": workflow["tools_required"],
            "expected_output": workflow["expected_output"],
        }
        for workflow in registry.values()
    ]

    return {
        "type": "function",
        "function": {
            "name": "select_workflow",
            "description": (
                "Select the single best matching business workflow "
                "from the Excel workflow registry. Choose only an "
                "existing workflow ID. Do not execute the workflow."
                "\nAvailable workflows:\n"
                + json.dumps(workflow_details, ensure_ascii=False)
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "workflow_id": {
                        "type": "string",
                        "enum": workflow_ids,
                        "description": (
                            "ID of the best matching workflow."
                        ),
                    },
                    "reason": {
                        "type": "string",
                        "description": (
                            "Brief explanation of why this workflow "
                            "matches the user's request."
                        ),
                    },
                },
                "required": ["workflow_id", "reason"],
                "additionalProperties": False,
            },
        },
    }


def run_llm_agent(user_request, data=None):
    """
    Use the LLM to select a workflow, then execute it in Python.

    The LLM chooses the workflow. The existing workflow engine
    performs business operations and validates the supplied data.
    """

    registry = load_workflow_registry()
    tool_schema = select_workflow_tool_schema(registry)

    messages = [
        {
            "role": "system",
            "content": (
                "You are a business workflow routing agent. "
                "Read the user's request and the workflow registry. "
                "Call select_workflow with the best matching workflow. "
                "Do not invent workflow IDs. If the request does not "
                "match any workflow, do not select a random workflow."
            ),
        },
        {
            "role": "user",
            "content": user_request,
        },
    ]

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=[tool_schema],
            tool_choice="required",
            max_tokens=500,
            extra_body={
                "reasoning": {
                    "max_tokens": 50,
                    "exclude": True,
                }
            },
        )

        assistant_message = response.choices[0].message

        if not assistant_message.tool_calls:
            return {
                "status": "error",
                "message": (
                    "The LLM did not return a workflow selection."
                ),
            }

        # This agent exposes one selection tool only.
        tool_call = assistant_message.tool_calls[0]

        if tool_call.function.name != "select_workflow":
            return {
                "status": "error",
                "message": "The LLM selected an unknown tool.",
            }

        arguments = json.loads(tool_call.function.arguments)

        workflow_id = arguments.get("workflow_id")
        reason = arguments.get("reason", "")

        # Validate the model's choice against the real Excel registry.
        if workflow_id not in registry:
            return {
                "status": "error",
                "message": (
                    f"The LLM returned an unknown workflow ID: "
                    f"{workflow_id}"
                ),
            }

        workflow = get_workflow(workflow_id)

        # Execute through the existing engine, with the selected
        # workflow ID explicitly supplied.
        result = execute_workflow(
            user_request=user_request,
            data=data,
            workflow_id_override=workflow_id,
        )

        result["selection_method"] = "OpenRouter LLM tool calling"
        result["selection_reason"] = reason
        result["selected_workflow_id"] = workflow_id
        result["selected_workflow_name"] = workflow["name"]

        return result

    except (ValueError, TypeError, KeyError, FileNotFoundError) as error:
        return {
            "status": "error",
            "message": str(error),
        }
    except Exception as error:
        return {
            "status": "error",
            "message": (
                f"LLM agent failed: {type(error).__name__}: {error}"
            ),
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

    result = run_llm_agent(request, sample_data)

    print("\n--- AI AGENT RESULT ---")
    print(json.dumps(result, indent=2, default=str))
