import asyncio
from typing import Any

from phoenix.client import Client

from eval_cases import EVAL_CASES
from real_estate_agent import run_agent


PHOENIX_BASE_URL = "http://localhost:6006"
DATASET_NAME = "real-estate-agent-tool-routing"
EXPERIMENT_NAME = "baseline-tool-routing-v2"


def agent_task(input: dict[str, Any]) -> dict[str, Any]:
    """
    Run one dataset example through the asynchronous LangGraph agent.

    Phoenix's synchronous experiment client requires a synchronous task.
    asyncio.run() executes our async run_agent() function and returns its
    JSON-serialisable result.
    """
    query = input["query"]
    result = asyncio.run(run_agent(query))

    return {
        "answer": result.get("answer", ""),
        "tool_calls": result.get("tool_calls", []),
        "tool_results": result.get("tool_results", []),
    }


def tool_selection_matches(
    output: dict[str, Any] | None,
    expected: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Check whether the agent selected exactly the expected tools.
    """
    output = output or {}
    expected = expected or {}

    actual_tools = [
        call.get("name")
        for call in output.get("tool_calls", [])
        if call.get("name")
    ]
    expected_tools = expected.get("expected_tools", [])

    passed = actual_tools == expected_tools

    return {
        "score": 1 if passed else 0,
        "label": "pass" if passed else "fail",
        "explanation": (
            f"Expected tools: {expected_tools}; "
            f"actual tools: {actual_tools}"
        ),
    }


def expected_text_present(
    output: dict[str, Any] | None,
    expected: dict[str, Any] | None,
) -> dict[str, Any]:
    """
    Check whether expected text appears in either the final answer or
    one of the tool results.
    """
    output = output or {}
    expected = expected or {}

    expected_text = expected.get("expected_contains")

    if not expected_text:
        return {
            "score": 1,
            "label": "not_applicable",
            "explanation": "No deterministic text expectation was specified.",
        }

    answer = str(output.get("answer", ""))

    tool_result_text = " ".join(
        str(item.get("content", ""))
        for item in output.get("tool_results", [])
    )

    combined_text = f"{answer} {tool_result_text}"
    passed = expected_text.casefold() in combined_text.casefold()

    return {
        "score": 1 if passed else 0,
        "label": "pass" if passed else "fail",
        "explanation": (
            f"Expected {expected_text!r} in the final answer or tool results."
        ),
    }


def get_or_create_dataset(client: Client):
    """
    Reuse the existing Phoenix dataset, or create it when it does not exist.
    """
    examples = [
        {
            "input": {
                "query": case["input"],
            },
            "output": {
                "expected_tools": case.get("expected_tools", []),
                "expected_contains": case.get("expected_contains"),
            },
            "metadata": {
                "case_number": index,
            },
        }
        for index, case in enumerate(EVAL_CASES, start=1)
    ]

    try:
        dataset = client.datasets.get_dataset(dataset=DATASET_NAME)
        print(f"Using existing dataset: {DATASET_NAME}")
        return dataset

    except Exception:
        dataset = client.datasets.create_dataset(
            name=DATASET_NAME,
            examples=examples,
        )
        print(f"Created dataset: {DATASET_NAME}")
        return dataset


def main() -> None:
    client = Client(base_url=PHOENIX_BASE_URL)
    dataset = get_or_create_dataset(client)

    experiment = client.experiments.run_experiment(
        dataset=dataset,
        task=agent_task,
        evaluators=[
            tool_selection_matches,
            expected_text_present,
        ],
        experiment_name=EXPERIMENT_NAME,
        experiment_description=(
            "Baseline evaluation of tool selection and deterministic "
            "answer content for the Quantic real-estate agent."
        ),
    )

    print("\nExperiment completed successfully.")

    # Phoenix client versions may return either an object or dictionary.
    if isinstance(experiment, dict):
        experiment_id = experiment.get("id", "See Phoenix UI")
    else:
        experiment_id = getattr(experiment, "id", "See Phoenix UI")

    print(f"Experiment ID: {experiment_id}")
    print(
        "Open Phoenix: "
        f"{PHOENIX_BASE_URL}/datasets"
    )


if __name__ == "__main__":
    main()