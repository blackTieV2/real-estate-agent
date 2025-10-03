import os
import asyncio

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


os.environ["OPENROUTER_API_KEY"] = "your-openrouter-key"
os.environ["TAVILY_API_KEY"] = "your_tavily_api_key_here"


OPENROUTER_MODEL = "openai/gpt-oss-120b"

model = ChatOpenAI(
    openai_api_base="https://openrouter.ai/api/v1",
    openai_api_key=os.environ["OPENROUTER_API_KEY"],
    model=OPENROUTER_MODEL
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
        }
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

    # merge MCP tools + non-MCP tools
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
# MAIN ENTRY POINT
# ---------------------
async def main(user_input: str):
    # ensure setup was completed, or run setup here on first run
    if tools is None or graph is None:
        await agent_setup()

    response = await graph.ainvoke({"messages": [HumanMessage(content=user_input)]})
    
    for msg in response["messages"]:
        if isinstance(msg, HumanMessage):
            print(f"Human: {msg.content}")
        elif isinstance(msg, AIMessage):
            if msg.additional_kwargs.get("tool_calls"):
                print(f"AI (tool call requested): {msg.content}")
                print(f"Tool call details: {msg.additional_kwargs['tool_calls']}")
            else:
                print(f"AI: {msg.content}")
        elif isinstance(msg, ToolMessage):
            print(f"Tool ({msg.name}) result: {msg.content}")


if __name__ == "__main__":
    import sys
    user_input = " ".join(sys.argv[1:])  # get input from command line
    if not user_input:
        print("Usage: python real_estate_agent.py <message>")
        print("Please provide a message.")
        sys.exit(1)

    asyncio.run(main(user_input))
