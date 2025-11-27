import asyncio
import os
import json
from datetime import date
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastmcp import Client
from google import genai
from google.genai import types

app = FastAPI()

# Allow Streamlit frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JSON Schema for structured output
TOOL_CALL_SCHEMA = {
    "type": "object",
    "properties": {
        "tool": {"type": "string"},
        "params": {"type": "object", "minProperties": 0},
    },
    "required": ["tool", "params"],
}

async def interpret_with_gemini(user_message, tools, genai_client):
    tool_context_list = []
    for tool in tools:
        params = tool.inputSchema.get('properties', {})
        param_desc = []
        for name, schema_dict in params.items():
            param_type = schema_dict.get('type', 'string')
            param_desc_text = schema_dict.get('description', '')
            desc_part = f" - {param_desc_text}" if param_desc_text else ""
            param_desc.append(f"'{name}' ({param_type}){desc_part}")
        params_line = "; ".join(param_desc) if param_desc else "None"
        tool_context_list.append(
            f"- Name: {tool.name}\n  Description: {tool.description}\n  Parameters: {params_line}"
        )
    tools_context = "\n".join(tool_context_list)

    today = date.today()
    system_instruction = (
        f"Assume today is {today}. "
        "If the user refers to a month only (e.g., 'October expenses'), use the current year. "
        "You are an AI financial assistant. "
        "Respond ONLY with a JSON object matching the provided schema — no markdown or text. "
        "If no tool fits, use 'None' and '{}'.\n"
        f"---TOOLS---\n{tools_context}\n---END_TOOLS---"
    )

    config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="application/json",
        response_json_schema=TOOL_CALL_SCHEMA,
    )

    model_name = "gemini-2.5-flash"
    try:
        response = await genai_client.aio.models.generate_content(
            model=model_name,
            contents=user_message,
            config=config,
        )
        return json.loads(response.text)
    except Exception as e:
        print("Error calling Gemini:", e)
        return {"tool": None, "params": {}}


@app.post("/interpret")
async def interpret(user_input: dict):
    """Handle user input and return interpreted tool + params or tool result."""
    message = user_input.get("message")
    if not message:
        raise HTTPException(status_code=400, detail="Missing 'message' field")

    API_KEY = os.getenv("GOOGLE_API_KEY")
    if not API_KEY:
        raise HTTPException(status_code=500, detail="GOOGLE_API_KEY not set")
    genai_client = genai.Client(api_key=API_KEY)

    FASTMCP_URL = os.getenv("FASTMCP_URL")
    if not FASTMCP_URL:
        raise HTTPException(status_code=500, detail="FASTMCP_URL not set")
    client = Client(FASTMCP_URL)

    async with client:
        tools = await client.list_tools()
        llm_result = await interpret_with_gemini(message, tools, genai_client)
        tool_name = llm_result.get("tool")
        params = llm_result.get("params", {})

        if tool_name and tool_name != "None":
            try:
                result = await client.call_tool(tool_name, params)
                return {"tool": tool_name, "params": params, "result": result}
            except Exception as e:
                raise HTTPException(status_code=500, detail=str(e))
        else:
            return {"tool": None, "params": {}, "result": "No matching tool found."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend:app",        # module:app name
        host="0.0.0.0",       # listen on all interfaces
        port=9000,            # set custom port
        reload=True           # auto-reload on code change (for dev)
    )
