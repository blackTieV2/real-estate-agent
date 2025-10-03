# Simulates a property listing database via MCP Server

import sqlite3
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel
from typing import List, Optional


mcp = FastMCP("PropertyData")


class Property(BaseModel):
    """Represents a real estate property record."""
    id: int
    address: str
    price: float
    bedrooms: int
    bathrooms: int


DB_FILE = "property_data.db"


def init_db() -> None:
    """Initialize the SQLite database with a properties table and sample data."""
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY,
            address TEXT UNIQUE NOT NULL,
            price REAL NOT NULL,
            bedrooms INTEGER NOT NULL,
            bathrooms INTEGER NOT NULL
        )
        """)
        cursor.execute("SELECT COUNT(*) FROM properties")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO properties (address, price, bedrooms, bathrooms) VALUES (?, ?, ?, ?)",
                [
                    ("123 Oak St, Anytown", 550000, 4, 3),
                    ("456 Maple Ave, Anytown", 320000, 3, 2),
                    ("789 Pine Ln, Anytown", 650000, 5, 4),
                ]
            )
        conn.commit()


init_db()


@mcp.tool()
def search_properties(min_price: float, max_price: float, beds: int) -> List[Property]:
    """
    Search for properties within a price range that have at least a given number of bedrooms.
    
    Args:
        min_price: Minimum price of the property.
        max_price: Maximum price of the property.
        beds: Minimum number of bedrooms required.
    
    Returns:
        List of Property objects matching the criteria.
    """
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, address, price, bedrooms, bathrooms
            FROM properties
            WHERE price BETWEEN ? AND ? AND bedrooms >= ?
            """,
            (min_price, max_price, beds)
        )
        return [
            Property(id=row[0], address=row[1], price=row[2], bedrooms=row[3], bathrooms=row[4])
            for row in cursor.fetchall()
        ]


@mcp.tool()
def get_property_details(address: str) -> Optional[Property]:
    """
    Retrieve detailed information for a property by its street address.
    
    Args:
        address: Exact address string of the property.
    
    Returns:
        A Property object if found, otherwise None.
    """
    address=address.strip()
    with sqlite3.connect(DB_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, address, price, bedrooms, bathrooms FROM properties WHERE address = ?",
            (address,)
        )
        row = cursor.fetchone()
        return Property(id=row[0], address=row[1], price=row[2], bedrooms=row[3], bathrooms=row[4]) if row else None


if __name__ == "__main__":
    mcp.run(transport="stdio")

