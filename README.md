# MCP Demo

## Setup Instructions

1. **Create virtual environment and install pip requirements**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install -r requirements.txt
    ```

2. **Export environment variables**
    ```bash
    export PGDATABASE=mcp_demo
    export PGUSER=mcp_agent
    export PGPASSWORD='your-secure-password'
    export PGHOST=localhost
    export PGPORT=5432
    export PGSEARCHPATH=agent
    ```

3. **Add the OpenAI API key**
    Create a `.env` file in the root directory of your project and add the following line:
    ```env
    export OPENAI_API_KEY='your-openai-api-key'
    ```

4. **Start the application**
    ```bash
    python app.py
    ```
    ```bash
    python app.py
    ```

4. **Access the application**
    Open your browser and navigate to `http://localhost:8050`. Enter your request in the input field and click the submit button to see the agent in action.