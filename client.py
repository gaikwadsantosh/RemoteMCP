import asyncio
from fastmcp import Client

async def main():
    #client = Client("ExpenseTracker") #if server is running on stdio transport
    
    # Use the Server URL provided in the terminal output
    SERVER_URL = "http://127.0.0.1:8000/mcp"
    # Initialize the client by passing the URL
    client = Client(SERVER_URL)
    
    async with client:
        # Optionally ping to check connection
        await client.ping()
        print("Connected to server")

        # List all available tools
        tools = await client.list_tools()
        print("Tools:", tools)

        # List available resources
        resources = await client.list_resources()
        print("Resources:", resources)

        # Call your tools

        # 1. Add an expense
        add_resp = await client.call_tool("add_expense", {
            "date": "2025-09-30",
            "amount": 200,
            "category": "Housing",
            "subcategory": "Rent",
            "note": "September rent"
        })
        print("add_expense response:", add_resp)

        # 2. List expenses in a date range
        list_resp = await client.call_tool("list_expenses", {
            "start_date": "2025-09-01",
            "end_date": "2025-09-30"
        })
        print("list_expenses response:", list_resp)

        # 3. Summarize expenses
        sum_resp = await client.call_tool("summarize", {
            "start_date": "2025-09-01",
            "end_date": "2025-09-30"
        })
        print("summarize response:", sum_resp)

        # 4. Read your categories resource
        cat_resp = await client.read_resource("expense://categories")
        # The resource response is a list of “ResourceReadResult” objects;
        # you may want to inspect .text or .data fields
        print("categories resource read:", [r.text for r in cat_resp])

if __name__ == "__main__":
    asyncio.run(main())
