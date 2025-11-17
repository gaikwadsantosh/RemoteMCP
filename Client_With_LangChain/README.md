Steps to build LanngChain Adapter FastMCP
------------------------------------
uv init .
uv add langchain langchain-google-genai langchain-mcp-adapters python-dotenv streamlit
uv run client1.py
uv run streamlit run streamlit_ui.py
docker build -t langchain-client-expensetracker . 
docker run -p 8501:8501 -e MCP_SERVER_URL="http://host.docker.internal:8000/mcp" langchain-client-expensetracker

