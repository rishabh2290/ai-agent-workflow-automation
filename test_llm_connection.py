
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env
load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
MODEL = os.getenv(
    "OPENROUTER_MODEL",
    "nvidia/nemotron-3.5-lightning:free",
)

if not API_KEY:
    print("ERROR: OPENROUTER_API_KEY is missing from your .env file.")
    sys.exit(1)

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)


def test_llm_connection():
    print(f"Testing OpenRouter connection...")
    print(f"Model: {MODEL}")

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a helpful assistant. "
                        "Answer directly and briefly. "
                        "Do not explain your reasoning."
                    ),
                },
                {
                    "role": "user",
                    "content": "Say hello in one short sentence.",
                },
            ],
            max_tokens=300,
            extra_body={
                "reasoning": {
                    "max_tokens": 50,
                    "exclude": True,
                }
            },
        )

        choice = response.choices[0]
        message = choice.message

        print("\n--- RESULT ---")
        print("Finish reason:", choice.finish_reason)
        print("Response:", message.content)

        if message.content:
            print("\nSUCCESS: The model returned text.")
        elif choice.finish_reason == "length":
            print(
                "\nWARNING: The response reached its token limit "
                "before returning visible text."
            )
            print(
                "Try another model that supports ordinary text "
                "responses and tool calling."
            )
        else:
            print(
                "\nWARNING: No visible text was returned. "
                "Check the model response and finish reason."
            )

        print("\n--- USAGE ---")
        if response.usage:
            print("Prompt tokens:", response.usage.prompt_tokens)
            print("Completion tokens:", response.usage.completion_tokens)
            print("Total tokens:", response.usage.total_tokens)

    except Exception as error:
        print("\nERROR: OpenRouter request failed.")
        print(type(error).__name__ + ":", error)
        print(
            "\nCheck your API key, model ID, internet connection, "
            "and OpenRouter account limits."
        )


if __name__ == "__main__":
    test_llm_connection()
