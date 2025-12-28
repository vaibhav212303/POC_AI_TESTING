import os
import sys
from mcp import StdioServerParameters
from mcp.client.stdio import stdio_client

def get_server_params():
    """
    Constructs the configuration to connect to the Node.js Playwright MCP Server.
    It automatically calculates the path relative to this file.
    """
    
    # 1. Determine the absolute path to the 'playwright-server' folder
    # logic: current_file -> core -> python-client -> root -> playwright-server
    current_dir = os.path.dirname(os.path.abspath(__file__))
    client_root = os.path.dirname(current_dir) # python-client
    project_root = os.path.dirname(client_root) # ai-browser-automation
    
    server_script_path = os.path.join(project_root, "playwright-server", "src", "index.ts")

    # 2. Verify the server file exists
    if not os.path.exists(server_script_path):
        print(f"❌ Error: Could not find Playwright Server at: {server_script_path}")
        print("Please ensure your folders are structured as:")
        print("  /ai-browser-automation")
        print("    /playwright-server/src/index.ts")
        print("    /python-client/...")
        sys.exit(1)

    # 3. Create the Connection Parameters
    # We use 'npx tsx' to execute the TypeScript server directly
    server_params = StdioServerParameters(
        command="npx",
        args=["tsx", server_script_path],
        env=os.environ # Pass current environment (API Keys etc) to the server
    )
    
    return server_params

def create_mcp_connection():
    """
    Helper to return the context manager for the connection.
    Usage:
        async with create_mcp_connection() as (read, write):
            async with ClientSession(read, write) as session:
                ...
    """
    params = get_server_params()
    return stdio_client(params)