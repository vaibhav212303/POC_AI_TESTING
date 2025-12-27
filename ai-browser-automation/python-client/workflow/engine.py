import asyncio
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from workflow.state import WorkflowContext

class WorkflowEngine:
    def __init__(self):
        self.nodes = []
        self.context = WorkflowContext()
        
        # 1. Robustly find the server path relative to this script
        # This handles running from 'python-client/' or root folder
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) # python-client root
        server_script_path = os.path.join(base_dir, "../playwright-server/src/index.ts")
        self.server_path = os.path.abspath(server_script_path)

        # 2. Safety Check
        if not os.path.exists(self.server_path):
            # Fallback try for different cwd
            self.server_path = os.path.abspath(os.path.join(os.getcwd(), "../playwright-server/src/index.ts"))
            
        if not os.path.exists(self.server_path):
            print(f"❌ Critical Error: Cannot find Playwright Server at: {self.server_path}")

    def add_node(self, node):
        self.nodes.append(node)
        return self

    async def run(self):
        print("\n🚀 Starting Autonomous Test Run...")
        
        # 3. Define Server Parameters (using 'npx tsx' to run TypeScript directly)
        server_params = StdioServerParameters(
            command="npx",
            args=["tsx", self.server_path],
            env=os.environ # Pass API keys to server if needed
        )

        try:
            # 4. Connect to MCP Server
            async with stdio_client(server_params) as (read, write):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    
                    # 5. Run the Pipeline Nodes
                    for node in self.nodes:
                        # Execute the node logic
                        await node.execute(self.context, session=session)
                        
                        # Stop immediately if a node marks the context as failed
                        if self.context.failed:
                            print(f"\n⛔ Workflow Halted: {self.context.error_message}")
                            break
                            
            if not self.context.failed:
                print("\n✅ Test Run Completed Successfully.")
                return self.context

        except Exception as e:
            print(f"\n🔥 Engine Critical Error: {e}")
            self.context.mark_failed(str(e))