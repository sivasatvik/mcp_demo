from dash import Dash,dcc, html, Input, Output, State
import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_mcp_adapters.tools import load_mcp_tools
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent
# from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from dotenv import find_dotenv, load_dotenv

dotenv_path = find_dotenv()
if dotenv_path:
    print(f"Loading environment variables from {dotenv_path}")
    load_dotenv(dotenv_path)
else:
    print("Warning: No .env file found. Please ensure your environment variables are set.")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    print("Error: OPENAI_API_KEY not found in environment variables.")
    exit(1)

model = ChatOpenAI(model="gpt-5-mini", openai_api_key=OPENAI_API_KEY)

prompt = ChatPromptTemplate.from_messages(
    [
        ("system",
         "You are a helpful assistant that that knows how to access psotgres tables and run SQL queries",
        ),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        ("placeholder", "{agent_scratchpad}"),
    ]
)

PYTHON_EXECUTBLE_PATH = "/Users/sivasatvik/Documents/Github/mcp_demo/venv/bin/python"
POSTGRES_SERVER_SCRIPT_PATH = "postgresql_mcp.py"

if not os.path.exists(PYTHON_EXECUTBLE_PATH):
    print(f"Error: Python executable not found at {PYTHON_EXECUTBLE_PATH}")
    exit(1)
if not os.path.exists(POSTGRES_SERVER_SCRIPT_PATH):
    print(f"Error: Python server script not found at {POSTGRES_SERVER_SCRIPT_PATH}")
    exit(1)

servers_params = StdioServerParameters(
    command=PYTHON_EXECUTBLE_PATH,
    args=[POSTGRES_SERVER_SCRIPT_PATH],
)

async def run_agent_async(query: str) -> str:
    print(f"Starting MCP client with query: {query}")
    try:
        async with stdio_client(servers_params) as (read, write):
            print("stdio_client connected.")
            async with ClientSession(read, write) as session:
                print("ClientSession established.")

                await session.initialize()
                print("Session initialized.")

                tools = await load_mcp_tools(session)
                print(f"Loaded tools: {[tool.name for tool in tools]}")

                agent = create_tool_calling_agent(
                    llm=model,
                    tools=tools,
                    prompt=prompt,
                )

                agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

                print("Invoking agent executor...")
                agent_response = await agent_executor.ainvoke({"input": query, "chat_history": []})  # Add empty chat history for now
                print("Agent executor completed.")

                output = agent_response.get("output", "Error: No output from agent.")
                print(f"Agent execution result: {output}")
                return output
    except ConnectionRefusedError:
        error_msg = "Error: Connection refused. Please ensure the MCP server is running and accessible."
        print(error_msg)
        return error_msg
    except FileNotFoundError:
        error_msg = f"Error: Python executable not found at {PYTHON_EXECUTBLE_PATH} or server script not found at {POSTGRES_SERVER_SCRIPT_PATH}."
        print(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"An unexpected error occurred: {str(e)}"
        print(error_msg)
        return error_msg


## Dash App
app = Dash()
server = app.server


app.layout = html.Div(
    [
        html.H1("Langchain PostgreSQL Agent"),
        html.Label("Enter your Postgres table query:"),
        dcc.Input(
            id="user-query-input",
            type="text",
            placeholder="e.g. what are the unique values in my 'agency' column?",
            style={"width": "80%", 'marginBottom': '10px', 'display': 'block'},
        ),
        html.Button("Submit", id="submit-button", n_clicks=0),
        html.Hr(),
        html.H3("Agent Response:"),
        dcc.Loading(
            id="loading-output",
            type="default",
            children=html.Div(id="agent-response-output", children="Ask a question to see the answer here.", style={"whiteSpace": "pre-wrap"})
        )
    ]
)

@app.callback(
    Output("agent-response-output", "children"),
    Input("submit-button", "n_clicks"),
    State("user-query-input", "value"),
    prevent_initial_call=True  # Don't run callback on page load
)
def update_output(n_clicks, query):
    if not query:
        return "Please enter a query."
    
    print(f"Button clicked {n_clicks} times. Received query: {query}")
    
    try:
        print("Calling asyncio.run()...")
        result = asyncio.run(run_agent_async(query))
        print(f"Async function returned: {result}")
        return result
    except Exception as e:
        error_msg = f"An error occurred while processing the query: {str(e)}"
        print(error_msg)
        return error_msg

if __name__ == "__main__":
    app.run()
