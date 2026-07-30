import os

from openinference.instrumentation.langchain import LangChainInstrumentor
from phoenix.otel import register


def configure_phoenix() -> None:
    """Configure local Phoenix tracing for the LangGraph agent."""

    tracer_provider = register(
        project_name="real-estate-agent-lab",
        endpoint=os.getenv(
            "PHOENIX_COLLECTOR_ENDPOINT",
            "http://localhost:6006/v1/traces",
        ),
    )

    LangChainInstrumentor().instrument(
        tracer_provider=tracer_provider,
    )