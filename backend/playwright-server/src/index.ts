import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { chromium, Browser, Page } from "playwright";

let browser: Browser | null = null;
let page: Page | null = null;

const server = new Server(
  {
    name: "playwright-server",
    version: "0.1.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "launch_browser",
        description: "Launches a visible browser window. Must be called first.",
        inputSchema: { type: "object", properties: {} },
      },
      {
        name: "navigate",
        description: "Navigate to a URL",
        inputSchema: {
          type: "object",
          properties: {
            url: { type: "string", description: "The full URL to visit" },
          },
          required: ["url"],
        },
      },
      {
        name: "click",
        description: "Click an element on the page using a CSS selector",
        inputSchema: {
          type: "object",
          properties: {
            selector: { type: "string", description: "CSS selector (e.g., #login-button)" },
          },
          required: ["selector"],
        },
      },
      {
        name: "fill",
        description: "Fill a text input field",
        inputSchema: {
          type: "object",
          properties: {
            selector: { type: "string", description: "CSS selector (e.g., #username)" },
            value: { type: "string", description: "The text to type" },
          },
          required: ["selector", "value"],
        },
      },
      {
        name: "get_content",
        description: "Get text content of the page to verify results",
        inputSchema: { type: "object", properties: {} },
      },
      {
        name: "screenshot",
        description: "Take a screenshot. Returns the image for AI analysis.",
        inputSchema: {
          type: "object",
          properties: {
            name: { type: "string", description: "Filename (e.g., 'error.png')" },
            fullPage: { type: "boolean", description: "True for full scrollable page" }
          },
          required: ["name"],
        },
      },
    ],
  };
});

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  try {
    const { name, arguments: args } = request.params;
    if (name === "launch_browser") {
        if (browser) await browser.close();
        browser = await chromium.launch({ headless: false }); // Visible window
        page = await browser.newPage();
        return { content: [{ type: "text", text: "Browser launched successfully." }] };
    }
    if (!page) {
      return { 
        content: [{ type: "text", text: "Error: Browser not running. Call launch_browser first." }],
        isError: true 
      };
    }
    switch (name) {
      case "navigate": {
        const url = String(args?.url);
        await page.goto(url);
        return { content: [{ type: "text", text: `Navigated to ${url}` }] };
      }
      case "click": {
        const selector = String(args?.selector);
        await page.click(selector);
        return { content: [{ type: "text", text: `Clicked element: ${selector}` }] };
      }
      case "fill": {
        const selector = String(args?.selector);
        const value = String(args?.value);
        await page.fill(selector, value);
        return { content: [{ type: "text", text: `Filled ${selector} with '${value}'` }] };
      }
      case "get_content": {
        const text = await page.innerText("body");
        const cleanText = text.slice(0, 2000); 
        return { content: [{ type: "text", text: cleanText }] };
      }
      case "screenshot": {
        const name = String(args?.name || "screenshot.png");
        const fullPage = Boolean(args?.fullPage);
        const path = process.cwd() + "/" + name;
        const buffer = await page.screenshot({ path: path, fullPage: fullPage });
        const base64Image = buffer.toString("base64");
        return { 
            content: [
                { type: "text", text: `Screenshot saved locally to: ${path}` },
                { type: "text", text: `IMAGE_BASE64:${base64Image}` } 
            ] 
        };
      }
      default:
        throw new Error(`Unknown tool: ${name}`);
    }
  } catch (error: any) {
    return { 
      content: [{ type: "text", text: `Playwright Error: ${error.message}` }],
      isError: true
    };
  }
});
const transport = new StdioServerTransport();
await server.connect(transport);
console.error("Playwright MCP Server started on STDIO");