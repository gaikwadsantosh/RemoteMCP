import streamlit as st
import asyncio
from dotenv import load_dotenv
from datetime import datetime
import json
import os

from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import ToolMessage, SystemMessage

load_dotenv()



# ------------------------------
# Async function to process chat
# ------------------------------
async def process_user_message(user_input, servers_config):
    client = MultiServerMCPClient(servers_config)
    tools = await client.get_tools()
    named_tools = {tool.name: tool for tool in tools}

    llm = ChatGoogleGenerativeAI(
        model="models/gemini-flash-latest",
    )

    llm_with_tools = llm.bind_tools(tools)

    # System message with date context
    today = datetime.now().strftime("%Y-%m-%d")
    system_message = SystemMessage(
        content=f"""
        Today's date is {today}.
        
        - When the user asks for expenses or actions for a specific month or year, automatically calculate the start_date and end_date.
        - If no month or year is mentioned (e.g., "give me list of expenses"), assume the current year ({datetime.now().year}) from Jan 1 to Dec 31.
        - If only a month is mentioned (e.g., "January"), assume the current year ({datetime.now().year}).
        - If a month and year are mentioned (e.g., "January 2025"), use that year.
        - Always provide dates in YYYY-MM-DD format.
        - For "this month", use the first day of the current month to the last day of the current month.
        - For "last month", use the first and last days of the previous month.
        - always give response in tabular format when possible.
        """
    )

    # First LLM call
    response = await llm_with_tools.ainvoke([system_message, user_input])

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
        [system_message, user_input, response, *tool_messages]
    )
    return final_response.content


# ------------------------------
# STREAMLIT UI
# ------------------------------
st.set_page_config(page_title="MCP Chatbot", page_icon="💬")

st.title("MCP Chatbot")
st.caption("MCP + Gemini + LangChain")

# ------------------------------
# SIDEBAR - SERVER CONFIGURATION
# ------------------------------
st.sidebar.header("MCP Server Configuration")

if "server_config_text" not in st.session_state:
    st.session_state.server_config_text = ""

server_config_input = st.sidebar.text_area(
    "Enter Server Name=URL (one per line)",
    value=st.session_state.server_config_text,
    height=150
)

# Parse the configuration
servers_config = {}
try:
    for line in server_config_input.splitlines():
        if "=" in line:
            name, url = line.split("=", 1)
            servers_config[name.strip()] = {
                "transport": "streamable_http",
                "url": url.strip()
            }
except Exception as e:
    st.sidebar.error(f"Error parsing config: {e}")

st.session_state.server_config_text = server_config_input

# Initialize chat history
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.write(message["content"])

# User input box
user_input = st.chat_input("Ask something ...")

if user_input:
    # Add user message to UI
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Process LLM response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            assistant_reply = asyncio.run(process_user_message(user_input, servers_config))
            st.write(assistant_reply)

    # Store assistant reply
    st.session_state.chat_history.append(
        {"role": "assistant", "content": assistant_reply}
    )

