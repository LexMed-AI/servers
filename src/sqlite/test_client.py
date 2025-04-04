import asyncio
import json
from mcp.client.stdio import StdioClient

async def main():
    # Connect to the server
    client = StdioClient()
    
    # Test list_tables tool
    print("Testing list_tables...")
    response = await client.invoke_tool("list_tables", {})
    print(json.dumps(response, indent=2))
    
    # Test create_table tool
    print("\nTesting create_table...")
    create_table_query = """
    CREATE TABLE IF NOT EXISTS jobs (
        code TEXT PRIMARY KEY,
        title TEXT,
        industry TEXT,
        strength TEXT,
        definitions TEXT
    )
    """
    response = await client.invoke_tool("create_table", {"query": create_table_query})
    print(json.dumps(response, indent=2))
    
    # Test write_query tool
    print("\nTesting write_query...")
    insert_query = """
    INSERT INTO jobs (code, title, industry, strength, definitions)
    VALUES ('110.117-010', 'DISTRICT ATTORNEY', '(government ser.)', 'S', 
            'Conducts prosecution in court proceedings in behalf of city, county, state, or federal government')
    """
    response = await client.invoke_tool("write_query", {"query": insert_query})
    print(json.dumps(response, indent=2))
    
    # Test read_query tool
    print("\nTesting read_query...")
    select_query = "SELECT * FROM jobs"
    response = await client.invoke_tool("read_query", {"query": select_query})
    print(json.dumps(response, indent=2))

if __name__ == "__main__":
    asyncio.run(main()) 