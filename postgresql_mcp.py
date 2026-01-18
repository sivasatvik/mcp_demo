import os
import psycopg2
import json
from loguru import logger
from mcp.server.fastmcp import FastMCP



mcp = FastMCP("Postgres_Demo")

@mcp.tool()
def query_data(sql_query: str) -> str:
    """Run a SQL query on the PostgreSQL database and return the results as JSON."""
    logger.info(f"Executing SQL query: {sql_query}")
    # Read connection from environment to use a restricted DB role
    DB_NAME = os.getenv("PGDATABASE", "mcp_demo")
    DB_USER = os.getenv("PGUSER", "sivasatvik")  # set to your restricted role
    DB_PASS = os.getenv("PGPASSWORD", "")
    DB_HOST = os.getenv("PGHOST", "localhost")
    DB_PORT = os.getenv("PGPORT", "5432")

    # Enforce read-only operation: allow SELECT/CTE only
    normalized = sql_query.lstrip().lower()
    if not (normalized.startswith("select") or normalized.startswith("with")):
        return json.dumps({
            "error": "Only read-only SELECT queries are allowed",
            "hint": "Use a view and SELECT from it (or a WITH CTE)"
        })
    conn = None
    cursor = None
    try:
        # Connect to the PostgreSQL database
        print(f"Connecting to database {DB_NAME} at {DB_HOST}:{DB_PORT} as user {DB_USER}")
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        print("Connection successful")
        cursor = conn.cursor()
        
        # Optional: set search_path to restrict accessible schemas (configure as needed)
        search_path = os.getenv("PGSEARCHPATH")
        if search_path:
            cursor.execute(f"SET search_path TO {search_path}")
        
        # Execute the SQL query
        print(f"Executing query: {sql_query}")
        cursor.execute(sql_query)
        
        # Fetch all results
        results = cursor.fetchall()
    except Exception as e:
        logger.error(f"Error executing query: {e}")
        return json.dumps({"error": str(e)})
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()
            print("Database connection closed")

    print("Scrtipt finished.")
    return json.dumps(results, indent=2)

if __name__ == "__main__":
    print("Starting MCP server...")
    mcp.run(transport="stdio")