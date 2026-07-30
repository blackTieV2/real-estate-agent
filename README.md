# Set up

## Environment

1. Create and activate a virtual environment.
2. Install the dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Copy the environment template to a local `.env` file:

   ```powershell
   Copy-Item .env.example .env
   ```

4. Open `.env` and replace the placeholder values with your OpenRouter and Tavily API keys.
5. Submit queries with:

   ```powershell
   python real_estate_agent.py "<message>"
   ```

Keep all project files in the same folder unless you update the MCP server paths in `real_estate_agent.py`.

## API keys

- OpenRouter: sign up and create an API key.
- Tavily: sign up and create an API key.
- Store both keys only in the local `.env` file.
- Never commit `.env`; it is excluded by `.gitignore`.
- `.env.example` contains safe placeholders and may be committed.

------------------------------------------------------------------------------------------------------------------------

# MCP Agent Working

We have a real estate agent that makes use of different tools. It connects to tools from two MCP servers and makes use of pre-built as well as custom-defined tools.

## Property Data MCP Server

- Simulates a property listing database via MCP Server and uses a local SQLite database.
- Tools: `search_properties()`, `get_property_details()`.

## CRM MCP Server

- Simulates a CRM Server via MCP Server and uses a local SQLite database.
- Tools: `create_client_lead()`, `add_note_to_client()`, `get_client_notes()`.

## LangGraph pre-built tools

- Web Search: Tavily, DuckDuckGo.

## Custom tools

- Python: `estimate_property_price_tool()`.

## Notes

- Please feel free to add or remove MCP servers or tools, or change behaviour to adapt it to your use case.
- You can add more or improved data to `property_data.db` or `crm_db.db`.

------------------------------------------------------------------------------------------------------------------------

# Usage

## Sample queries

- `python real_estate_agent.py "Find me homes between 300000 and 600000 with 3+ bedrooms."` — should call `search_properties()`.
- `python real_estate_agent.py "Give me details for the property address: 789 Pine Ln, Anytown"` — should call `get_property_details()`.
- `python real_estate_agent.py "Create a new client named Alice Jay with email alice.j@example.com"` — should call `create_client_lead()`.
- `python real_estate_agent.py "Add a note to alice.j@example.com saying she prefers houses with 3+ bedroom"` — should call `add_note_to_client()`.
- `python real_estate_agent.py "Show me the notes we have for alice.j@example.com in our CRM"` — should call `get_client_notes()`.
- `python real_estate_agent.py "Estimate the price of a 4 bedroom 3 bathroom property"` — should call `estimate_property_price_tool()`.
- `python real_estate_agent.py "Search the web for current real estate market trends in Miami"` — should call `tavily_search()`.
- `python real_estate_agent.py "Use DuckDuckGo search engine to find news on real estate"` — should call `duckduckgo_search()`.

## Complex queries

- `python real_estate_agent.py "Check if we have any notes on alice.j@example.com, then find available houses based on her preference. Also if we know either the number of bedroom or bathroom she wants come up with estimates for such house combinations."` — should call `get_client_notes()`, `search_properties()`, and `estimate_property_price_tool()` multiple times.

## Notes

- Delete `crm_db.db` and/or `property_data.db` if existing data is causing an issue.

------------------------------------------------------------------------------------------------------------------------

# Tools and technologies

This project uses LangGraph, MCP, and OpenRouter.

## OpenRouter

- The configured model is `openai/gpt-oss-120b`.
- Other supported OpenRouter models may be selected by changing `OPENROUTER_MODEL` in `real_estate_agent.py`.

## LangChain MCP Adapters

- Converts MCP tools into LangChain tools that can be used with LangGraph agents.
- Allows connection to multiple MCP servers and loading tools from them.
- Reference: https://github.com/langchain-ai/langchain-mcp-adapters
- The project uses `stdio`; `streamable_http` can also be used for MCP servers that support it.
