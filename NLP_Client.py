from fastmcp import Agent
import asyncio

async def main():
    # Connect to HTTP MCP server
    agent = Agent("http://127.0.0.1:8000/mcp")

    async with agent:
        await agent.ping()
        print("✅ Connected to MCP Agent")

        # Use natural language
        response = await agent.say("Add 200 rupees for groceries today")
        print("🧾", response.message)

        response = await agent.say("Show expenses from September")
        print("📊", response.message)

        response = await agent.say("Summarize transport expenses this month")
        print("📈", response.message)

if __name__ == "__main__":
    asyncio.run(main())
