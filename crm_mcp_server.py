"""
CRM MCP Server
---------------
A simple CRM (Customer Relationship Management) service that manages
clients and associated notes using SQLite.
"""

import sqlite3
from mcp.server.fastmcp import FastMCP
from typing import List, Dict

mcp = FastMCP("CRM")
CRM_DB_FILE = "crm_db.db"


def init_crm_db() -> None:
    """Initialize the CRM database with clients and notes tables."""
    with sqlite3.connect(CRM_DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY,
            name TEXT,
            email TEXT NOT NULL
        )
        """)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY,
            client_id INTEGER NOT NULL,
            note TEXT NOT NULL,
            FOREIGN KEY (client_id) REFERENCES clients(id)
        )
        """)
        conn.commit()


init_crm_db()


@mcp.tool()
def create_client_lead(name: str, email: str) -> str:
    """
    Create a new client lead in the CRM database.

    Args:
        name: Full name of the client.
        email: Unique email address of the client.

    Returns:
        Confirmation message with client ID, or a message if the client already exists.
    """
    try:
        with sqlite3.connect(CRM_DB_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute( "INSERT INTO clients (name, email) VALUES (?, ?)", (name, email) )
            conn.commit()
            return f"New client lead created for {name} ({email}). Client ID: {cursor.lastrowid}"
    except sqlite3.IntegrityError as e:
        return f"IntegrityError: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"



@mcp.tool()
def add_note_to_client(email: str, note: str) -> str:
    """
    Add a note to a client record by matching on email.

    Args:
        email: Client email to associate the note with.
        note: Content of the note to store.

    Returns:
        Confirmation message, or an error message if the client is not found.
    """
    with sqlite3.connect(CRM_DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM clients WHERE email = ?", (email,))
        row = cursor.fetchone()
        if not row:
            return f"Client with email {email} not found."
        client_id = row[0]
        cursor.execute(
            "INSERT INTO notes (client_id, note) VALUES (?, ?)", 
            (client_id, note)
        )
        conn.commit()
        return f"Note added for client {email}."


@mcp.tool()
def get_client_notes(email: str) -> List[str]:
    """
    Retrieve all notes associated with a client by their email.

    Args:
        email: Client email address.

    Returns:
        List of note strings. Returns an empty list if the client is not found.
    """
    with sqlite3.connect(CRM_DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM clients WHERE email = ?", (email,))
        client_id_row = cursor.fetchone()
        if not client_id_row:
            return []
        client_id = client_id_row[0]
        cursor.execute(
            "SELECT note FROM notes WHERE client_id = ?", 
            (client_id,)
        )
        return [row[0] for row in cursor.fetchall()]


if __name__ == "__main__":
    mcp.run(transport="stdio")

