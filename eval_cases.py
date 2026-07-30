EVAL_CASES = [
    {
        "input": "Estimate the price of a 4 bedroom 3 bathroom property",
        "expected_tools": ["estimate_property_price_tool"],
        "expected_contains": "$440,000",
    },
    {
        "input": "Find me homes between 300000 and 600000 with 3+ bedrooms",
        "expected_tools": ["search_properties"],
    },
    {
        "input": (
            "Create a new client named Alice Jay "
            "with email alice.j@example.com"
        ),
        "expected_tools": ["create_client_lead"],
    },
    {
        "input": (
            "Add a note to alice.j@example.com saying "
            "she prefers houses with 3+ bedrooms"
        ),
        "expected_tools": ["add_note_to_client"],
    },
    {
        "input": "Show me the notes for alice.j@example.com",
        "expected_tools": ["get_client_notes"],
    },
]