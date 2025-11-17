import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import ToolMessage
import json
from datetime import datetime
import os

load_dotenv()

MCP_SERVER_URL = os.getenv("MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")

SERVERS = {
    "expensetracker": {
        "transport": "streamable_http",
        "url": MCP_SERVER_URL,
    }
}

async def main():
    client = MultiServerMCPClient(SERVERS)
    tools = await client.get_tools()

    named_tools = {tool.name: tool for tool in tools}
    print("Available tools:", named_tools.keys())

    # ✅ Use Gemini free model
    llm = ChatGoogleGenerativeAI(
        model="models/gemini-flash-latest",
    )

    llm_with_tools = llm.bind_tools(tools)

    current_year = datetime.now().year

    prompt = f"Give me list of expenses for October month of year {current_year}"
    response = await llm_with_tools.ainvoke(prompt)

    if not getattr(response, "tool_calls", None):
        print("\nLLM Reply:", response.content)
        return

    tool_messages = []

    for tc in response.tool_calls:
        selected_tool = tc["name"]
        selected_tool_args = tc.get("args") or {}
        selected_tool_id = tc["id"]

        # Invoke tool
        result = await named_tools[selected_tool].ainvoke(selected_tool_args)

        tool_messages.append(
            ToolMessage(
                tool_call_id=selected_tool_id,
                content=json.dumps(result)
            )
        )

    # Final LLM call with tool output
    final_response = await llm_with_tools.ainvoke([prompt, response, *tool_messages])
    print(f"Final response: {final_response.content}")

if __name__ == "__main__":
    asyncio.run(main())
