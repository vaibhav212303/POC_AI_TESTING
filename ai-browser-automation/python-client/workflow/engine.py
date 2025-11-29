import asyncio
import os
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from workflow.state import WorkflowContext

class WorkflowEngine:
    def __init__(self):
        self.nodes = []
        self.context = WorkflowContext()
        
        # CONFIGURATION: Point to the Playwright Server
        # Ensure you have run: npm install -g @modelcontextprotocol/server-playwright
        # Server Config
    server_script_path = os.path.abspath(os.path.join(os.getcwd(), "../playwright-server/src/index.ts"))
    server_params = StdioServerParameters(command="npx", args=["tsx", server_script_path], env=os.environ)

    def add_node(self, node):
        self.nodes.append(node)
        return self

    async def run(self):
        print("\n🚀 Starting Autonomous Test Run...")
        
        # Connect to the Playwright MCP Server
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                # Run the Pipeline
                for node in self.nodes:
                    await node.execute(self.context, session=session)
                    
                    # Stop if a node failed the workflow
                    if self.context.failed:
                        print(f"\n⛔ Workflow Halted: {self.context.error_message}")
                        break
        
        if not self.context.failed:
            print("\n✅ Test Run Completed Successfully.")