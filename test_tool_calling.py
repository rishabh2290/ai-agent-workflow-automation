
import json
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "nvidia/nemotron-3.5-lightning:free",
)

if not API_KEY:
    raise ValueError("OPENROUTER_API_KEY is missing from .env")

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)


# This is a Python tool that our application can execute.
def calculator(a, b, operation):
    if operation == "add":
        return {"result": a + b}
    elif operation == "subtract":
        return {"result": a - b}
    elif operation == "multiply":
        return {"result": a * b}
    elif operation == "divide":
        if b == 0:
            return {"error": "Cannot divide by zero"}
        return {"result": a / b}
    else:
        return {"error": f"Unsupported operation: {operation}"}


# Describe the available tool to the LLM.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": (
                "Calculate the result of adding, subtracting, "
                "multiplying, or dividing two numbers."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {
                        "type": "number",
                        "description": "First number",
                    },
                    "b": {
                        "type": "number",
                        "description": "Second number",
                    },
                    "operation": {
                        "type": "string",
                        "enum": [
                            "add",
                            "subtract",
                            "multiply",
                            "divide",
                        ],
                    },
                },
                "required": ["a", "b", "operation"],
                "additionalProperties": False,
            },
        },
    }
]


def run_tool_calling_test():
    messages = [
        {
            "role": "system",
            "content": (
                "You are an assistant that uses tools for calculations. "
                "When a calculation is requested, call the calculator "
                "tool. After receiving its result, explain the answer "
                "in one short sentence."
            ),
        },
        {
            "role": "user",
            "content": "Calculate 25 multiplied by 4 using the calculator tool.",
        },
    ]

    print(f"Model: {MODEL}")
    print("User request: Calculate 25 multiplied by 4")
    print("\nSending request to the LLM...")

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            max_tokens=500,
            extra_body={
                "reasoning": {
                    "max_tokens": 50,
                    "exclude": True,
                }
            },
        )

        assistant_message = response.choices[0].message

        # Preserve the assistant's message, including its tool calls.
        messages.append(assistant_message.model_dump(exclude_none=True))

        if not assistant_message.tool_calls:
            print("\nThe model did not call a tool.")
            print("Model response:", assistant_message.content)
            print("Finish reason:", response.choices[0].finish_reason)
            print("Try a different tool-capable model if necessary.")
            return

        # Execute every tool requested by the model.
        for tool_call in assistant_message.tool_calls:
            tool_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            print(f"\nTool selected by LLM: {tool_name}")
            print("Arguments:", arguments)

            if tool_name == "calculator":
                result = calculator(**arguments)
            else:
                result = {"error": f"Unknown tool: {tool_name}"}

            print("Python tool result:", result)

            # Return the result to the model.
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )

        print("\nSending tool result back to the LLM...")

        final_response = client.chat.completions.create(
            model=MODEL,
            messages=messages,
            max_tokens=300,
            extra_body={
                "reasoning": {
                    "max_tokens": 50,
                    "exclude": True,
                }
            },
        )

        final_message = final_response.choices[0].message

        print("\n--- FINAL RESULT ---")
        print(final_message.content or "No final text returned.")

        if final_message.content:
            print("\nSUCCESS: LLM tool calling worked.")

    except Exception as error:
        print("\nERROR:", type(error).__name__, error)


if __name__ == "__main__":
    run_tool_calling_test()
