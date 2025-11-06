## Test Code in MCP Inspector

uv run fastmcp dev server.py -- this command will lanuch the MCP inspector, but you need to run another command to run server

---

## Run Server (FASTMCP)

python server.py -- This command will run the actual server

OR

docker build -t fastmcp-expensetracker .
docker run -p 8000:8000 fastmcp-expensetracker

---

## Run Server2 (FASTMCP_2)

python server2.py -- This command will run the actual server

OR

docker build -t fastmcp-foodcardactions .
docker run -p 8001:8001 fastmcp-foodcardactions

---

## Run Client

#### 1. Client Backend (FASTAPI) \client\backend

python backend.py -- this command will fastapi which connects to server and expose to frontend

OR

docker build -t fastapi-client .

docker run -p 9000:9000 -e GOOGLE_API_KEY="your_actual_api_key_here" -e FASTMCP_URL="http://host.docker.internal:8000/mcp" -e FASTMCP_FOODCARD_URL="http://host.docker.internal:8001/mcp" fastapi-client

#### 2. Client UI (STREAMLIT) \client\frontend

streamlit run frontend.py

OR

docker build -t streamlit-client .

docker run -p 8501:8501 -e BACKEND_URL="http://host.docker.internal:9000/interpret" streamlit-client

---

## Other Options to Add tool to Claud Desktop

#### Option 1 (with premium version of claud desktop) 
deploy code to fastmcp cloud through github, copy the url and add connector in cluad desktop

#### Option 2 (through local proxy server):

1. create expenseproxy.py file
2. test with mcp inspector uv run fastmcp dev expenseproxy.py (make sure server is running with python server.py) and then connect in mcp insppector with stdio
3. to deploy in claud-desktop run uv run fastmcp install claude-desktop expenseproxy.py
then go to claude desktop -> settings -> developers -> edit config -> open claude-desktop-config.json -> add the full path of uv (you can find the path by command where uv)
4. connect this in claud desktop as stdio
