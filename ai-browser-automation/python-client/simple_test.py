import asyncio
import os
# Use 'npm install -g tsx' if 'npx' causes path issues, but npx usually works
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def run():
    # 1. configuration: Point to your Node.js server file
    # We assume folders are siblings: ai-browser-automation/playwright-server
    server_script_path = os.path.abspath(
        os.path.join(os.getcwd(), "../playwright-server/src/index.ts")
    )
    
    print(f"Looking for server at: {server_script_path}")
    if not os.path.exists(server_script_path):
        print("Error: Could not find the server file. Check directory structure.")
        return

    # 2. Define how to launch the server
    # We use 'npx tsx' to run the TypeScript file directly
    server_params = StdioServerParameters(
        command="npx", # Ensure you have Node.js installed and in PATH
        args=["tsx", server_script_path],
        env=os.environ
    )

    print("Starting MCP Client...")
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize connection
                await session.initialize()
                
                # List available tools
                tools = await session.list_tools()
                tool_names = [t.name for t in tools.tools]
                print(f"\n✅ Connected! Tools available: {tool_names}")

                # TEST 1: Launch Browser
                print("\n🔹 Calling Tool: launch_browser")
                await session.call_tool("launch_browser")
                print("Browser launched.")

                # TEST 2: Navigate
                print("🔹 Calling Tool: navigate -> google.com")
                result = await session.call_tool("navigate", arguments={"url": "https://www.google.com"})
                print(f"Server Response: {result.content[0].text}")

                print("\nWaiting 5 seconds so you can see the browser...")
                await asyncio.sleep(5)
                print("Done.")

    except Exception as e:
        print(f"\n❌ Error connecting to server: {e}")
        print("Tip: Make sure you ran 'npm install' in the playwright-server folder.")

if __name__ == "__main__":
    asyncio.run(run())