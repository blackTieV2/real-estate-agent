# Set up
## Environment
* Create a virtual environment (python 3.12) and activate it
* Run `pip install -r requiements.txt`
* Now you submit queries by running `python real_estate_agent.py <message>`
* Make sure all files are in the same folder. Or you will need to adjust the paths in real_estate_agent.py

## Keys
* OpenRouter: Sign up and create an API key (no credit card needed)
* Tavily: Sign up and create an API key (no credit card needed)

------------------------------------------------------------------------------------------------------------------------

# MCP Agent Working
We have a real estate agent that makes use of different tools. It connects to tools from 2 MCP servers and makes use of pre-built as well as custom defined tools. 

## Property Data MCP Server
* Simulates a property listing database via MCP Server - uses local sqlite3 DB
* Tools: `search_properties()`, `get_property_details()`

## CRM MCP Server
* Simulates a CRM Server  via MCP Server - uses local sqlite3 DB
* Tools: `create_client_lead()`, `add_note_to_client()`, `get_client_notes()`

## LangGraph pre-built tools
* Web Search: Tavily, DuckDuckGo

## Custom tools:
* python: `estimate_property_price_tool()`

## Notes:
* Please feel free to add/remove the MCP servers or tools or change behavior to adapt it to use case. 
* Also, you can add more/proper data to "property_data.db" or "crm_db.db"

------------------------------------------------------------------------------------------------------------------------

# Usage
## Sample queries
* `python real_estate_agent.py "Find me homes between 300000 and 600000 with 3+ bedrooms."` : should call `search_properties()`
* `python real_estate_agent.py "Give me details for the property address: 789 Pine Ln, Anytown"` : should call `get_property_details()`
* `python real_estate_agent.py "Create a new client named Alice Jay with email alice.j@example.com"`: should call `create_client_lead()`
* `python real_estate_agent.py "Add a note to alice.j@example.com saying she prefers houses with 3+ bedroom"`: should call `add_note_to_client()`
* `python real_estate_agent.py "Show me the notes we have for alice.j@example.com in our CRM"`: should call `get_client_notes()`
* `python real_estate_agent.py "Estimate the price of a 4 bedroom 3 bathroom property"` => should call `estimate_property_price_tool()`
* `python real_estate_agent.py "Search the web for current real estate market trends in Miami"` => should call `tavily_search()` 
* `python real_estate_agent.py "Use DuckDuckGo search engine to find news on real estate"` => should call `duckduckgo_search()`

## Complex queries:
* `python real_estate_agent.py "Check if we have any notes on alice.j@example.com, then find available houses based on her preference. Also if we know either the number of bedroom or bathroom she wants come up with estimates for such house combinations."`: should call `get_client_notes()`, `search_properties()`, multiple times `estimate_property_price_tool()`

## Notes: 
* Delete "crm_db.db" and/or "property_data.db" if existing data is causing some issue. 

------------------------------------------------------------------------------------------------------------------------

# Tools/Technologies notes:
I am using LangGraph, MCP, and OpenRouter

## OpenRouter: 
* Currently using gpt-oss-20B
* Any of the free models can be used: https://openrouter.ai/models/?q=free
* You can also pay and use other models 

## LangChain MCP Adapters 
* Converts MCP tools into LangChain tools that can be used with LangGraph agents
* Allows you to connect to multiple MCP servers and load tools from them
* Reference: https://github.com/langchain-ai/langchain-mcp-adapters
* I am using stdio for MCP. If you like you can use streamable_http for any of the mcp servers
* Please feel free to add any other feature mentioned in the reference

------------------------------------------------------------------------------------------------------------------------
