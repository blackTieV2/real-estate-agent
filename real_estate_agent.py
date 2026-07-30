import os
import asyncio

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool
from langgraph.prebuilt import ToolNode
from langgraph.graph import StateGraph, MessagesState, START, END

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_mcp_adapters.client import MultiServerMCPClient

from langchain_tavily import TavilySearch
from langchain_community.tools import DuckDuckGoSearchRun


# Load local secrets from .env without hard-coding them in source control.
load_dotenv()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

missing_keys = [
    name
    for name, value in {
        "OPENROUTER_API_KEY": OPENROUTER_API_KEY,
        "TAVILY_API_KEY": TAVILY_API_KEY,
    }.items()
    if not value
]

if missing_keys:
    raise RuntimeError(
        "Missing required environment variable(s): "
        + ", ".join(missing_keys)
        + ". Copy .env.example to .env and add your API keys."
    )

from phoenix_setup import configure_phoenix

configure_phoenix()

OPENROUTER_MODEL = "openrouter/free"

model = ChatOpenAI(
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=OPENROUTER_API_KEY,
    model=OPENROUTER_MODEL,
)


# ---------------------
# MCP CLIENT SERVERS
# ---------------------
client = MultiServerMCPClient(
    {
        "PropertyData": {
            "command": "python",
            "args": ["./property_data_mcp_server.py"],  # Use full path if needed
            "transport": "stdio",
        },
        "CRM": {
            "command": "python",
            "args": ["./crm_mcp_server.py"],  # Use full path if needed
            "transport": "stdio",
        },
    }
)


# ------------------------------------------------------------------------------------
# Pre-built TOOLS: pick either one for search; you can add more such tools from langgraph
# ------------------------------------------------------------------------------------
tavily_search_tool = TavilySearch(
    max_results=5,
    topic="general",
)

duckduckgo_search_tool = DuckDuckGoSearchRun()


# ---------------------
# Custom TOOLS
# ---------------------
@tool
def estimate_property_price_tool(bedrooms: int, bathrooms: int) -> str:
    """
    Estimates the price of a property based on the number of bedrooms and bathrooms.
    """
    if bedrooms < 1 or bathrooms < 1:
        return "Please provide a valid number of bedrooms and bathrooms (at least one each)."

    base_price = 50000
    price = base_price + bedrooms * 75000 + bathrooms * 30000
    return f"Estimated property price: ${price:,.0f}"


# ---------------------
# SET UP AGENT
# ---------------------
tools = None
graph = None


async def agent_setup():
    global tools, graph
    mcp_tools = await client.get_tools()

    # Merge MCP tools + non-MCP tools.
    tools = mcp_tools + [
        tavily_search_tool,
        duckduckgo_search_tool,
        estimate_property_price_tool,
    ]

    def call_model(state: MessagesState):
        response = model.bind_tools(tools).invoke(state["messages"])
        return {"messages": response}

    def tools_condition(state: MessagesState):
        messages = state["messages"]
        last_message = messages[-1]
        if last_message.tool_calls:
            return "tools"
        return END

    builder = StateGraph(MessagesState)
    builder.add_node(call_model)
    builder.add_node(ToolNode(tools))
    builder.add_edge(START, "call_model")
    builder.add_conditional_edges("call_model", tools_condition)
    builder.add_edge("tools", "call_model")
    graph = builder.compile()


# ---------------------
# STRUCTURED AGENT RUNNER
# ---------------------
async def run_agent(user_input: str) -> dict:
    """
    Run the LangGraph agent and return structured results.

    The structured result is suitable for Phoenix experiments,
    automated evaluation, and the command-line display wrapper.
    """
    if tools is None or graph is None:
        await agent_setup()

    response = await graph.ainvoke(
        {"messages": [HumanMessage(content=user_input)]}
    )

    tool_calls = []
    tool_results = []
    final_answer = ""

    for message in response["messages"]:
        if isinstance(message, AIMessage):
            for call in message.tool_calls or []:
                tool_calls.append(
                    {
                        "name": call.get("name"),
                        "args": call.get("args", {}),
                        "id": call.get("id"),
                    }
                )

            # The last AI message without tool calls is the user-facing response.
            if message.content and not message.tool_calls:
                final_answer = str(message.content)

        elif isinstance(message, ToolMessage):
            tool_results.append(
                {
                    "name": message.name,
                    "content": str(message.content),
                    "tool_call_id": message.tool_call_id,
                }
            )

    return {
        "input": user_input,
        "answer": final_answer,
        "tool_calls": tool_calls,
        "tool_results": tool_results,
        "messages": response["messages"],
    }


# ---------------------
# COMMAND-LINE DISPLAY
# ---------------------
async def main(user_input: str) -> None:
    result = await run_agent(user_input)

    print(f"Human: {result['input']}")

    for tool_call in result["tool_calls"]:
        print(
            f"Tool requested: {tool_call['name']} "
            f"with arguments {tool_call['args']}"
        )

    for tool_result in result["tool_results"]:
        print(
            f"Tool ({tool_result['name']}) result: "
            f"{tool_result['content']}"
        )

    print(f"AI: {result['answer']}")


if __name__ == "__main__":
    import sys

    user_input = " ".join(sys.argv[1:])  # Get input from command line.
    if not user_input:
        print("Usage: python real_estate_agent.py <message>")
        print("Please provide a message.")
        sys.exit(1)

    asyncio.run(main(user_input))
