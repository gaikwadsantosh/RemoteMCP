import streamlit as st
import asyncio
from dotenv import load_dotenv
from datetime import datetime
import json

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import ToolMessage

load_dotenv()

# ------------------------------
# MCP SERVER CONFIG
# ------------------------------
SERVERS = {
    "expensetracker": {
        "transport": "streamable_http",
        "url": "http://127.0.0.1:8000/mcp",
    }
}

# ------------------------------
# Async function to process chat
# ------------------------------
async def process_user_message(user_input):
    client = MultiServerMCPClient(SERVERS)
    tools = await client.get_tools()
    named_tools = {tool.name: tool for tool in tools}

    llm = ChatGoogleGenerativeAI(
        model="models/gemini-flash-latest",
    )

    llm_with_tools = llm.bind_tools(tools)

    # First LLM call
    response = await llm_with_tools.ainvoke(user_input)

    if not getattr(response, "tool_calls", None):
        return response.content

    # --------------------------
    # If tools are invoked
    # --------------------------
    tool_messages = []

    for tc in response.tool_calls:
        selected_tool = tc["name"]
        selected_tool_args = tc.get("args") or {}
        selected_tool_id = tc["id"]

        # Call MCP tool
        result = await named_tools[selected_tool].ainvoke(selected_tool_args)

        tool_messages.append(
            ToolMessage(
                tool_call_id=selected_tool_id,
                content=json.dumps(result)
            )
        )

    final_response = await llm_with_tools.ainvoke(
        [user_input, response, *tool_messages]
    )
    return final_response.content


# ------------------------------
# STREAMLIT UI
# ------------------------------
st.set_page_config(page_title="Expense Tracker Chatbot", page_icon="💬")

st.title("💬 Expense Tracker Chatbot")
st.caption("Powered by MCP + Gemini + LangChain")

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# User input box
user_input = st.chat_input("Ask something about your expenses...")

if user_input:
    # Add user message to UI
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Process LLM response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            assistant_reply = asyncio.run(process_user_message(user_input))
            st.write(assistant_reply)

    # Store assistant reply
    st.session_state.chat_history.append(
        {"role": "assistant", "content": assistant_reply}
    )

