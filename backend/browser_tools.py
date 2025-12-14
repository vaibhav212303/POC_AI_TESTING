import base64
from playwright.async_api import Page

# --- TOOL DEFINITIONS ---
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "navigate",
            "description": "Navigate to a specific URL",
            "parameters": {
                "type": "object",
                "properties": {"url": {"type": "string"}},
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "click",
            "description": "Click an element. Use inspect_page first to find selectors.",
            "parameters": {
                "type": "object",
                "properties": {"selector": {"type": "string"}},
                "required": ["selector"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fill",
            "description": "Fill a text input.",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {"type": "string"},
                    "value": {"type": "string"}
                },
                "required": ["selector", "value"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_text",
            "description": "Get text from an element.",
            "parameters": {
                "type": "object",
                "properties": {"selector": {"type": "string"}},
                "required": ["selector"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_page",
            "description": "Analyze the page to find IDs, Classes, and Text of interactive elements.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "take_screenshot",
            "description": "Capture a screenshot of the current page state for visual verification.",
            "parameters": {"type": "object", "properties": {}, "required": []}
        }
    }
]

# --- IMPLEMENTATION ---
class BrowserTools:
    def __init__(self, page: Page):
        self.page = page

    async def navigate(self, url: str):
        try:
            await self.page.goto(url, timeout=15000)
            return f"✅ Navigated to {url}"
        except Exception as e:
            return f"❌ Navigation failed: {str(e)}"

    async def click(self, selector: str):
        try:
            await self.page.wait_for_selector(selector, state="visible", timeout=5000)
            await self.page.click(selector)
            return f"✅ Clicked '{selector}'"
        except Exception as e:
            return f"❌ Click failed: {str(e)}"

    async def fill(self, selector: str, value: str):
        try:
            await self.page.wait_for_selector(selector, state="visible", timeout=5000)
            await self.page.fill(selector, value)
            return f"✅ Filled '{selector}' with '{value}'"
        except Exception as e:
            return f"❌ Fill failed: {str(e)}"

    async def get_text(self, selector: str):
        try:
            element = await self.page.query_selector(selector)
            if element:
                text = await element.text_content()
                return text.strip()
            return "❌ Element not found"
        except Exception as e:
            return f"❌ Error getting text: {str(e)}"

    async def inspect_page(self):
        js_script = """
        (() => {
            const elements = document.querySelectorAll('button, input, a, textarea, select, h1, h2, h3, p');
            return Array.from(elements).map(el => {
                let info = el.tagName.toLowerCase();
                if (el.id) info += ` id='${el.id}'`;
                if (el.className) info += ` class='${el.className.split(' ').slice(0,2).join('.')}'`;
                if (el.getAttribute('placeholder')) info += ` placeholder='${el.getAttribute('placeholder')}'`;
                if (el.innerText && el.innerText.trim().length > 0) info += ` text='${el.innerText.substring(0, 30).replace(/\\n/g, " ")}'`;
                return info;
            }).filter(info => !info.includes("script") && !info.includes("style")).slice(0, 50).join('\\n');
        })()
        """
        try:
            result = await self.page.evaluate(js_script)
            return f"🔍 Page Elements:\n{result}"
        except Exception as e:
            return f"❌ Inspection failed: {str(e)}"

    async def take_screenshot(self):
        try:
            screenshot_bytes = await self.page.screenshot(full_page=False)
            b64_string = base64.b64encode(screenshot_bytes).decode('utf-8')
            return f"IMAGE_DATA:{b64_string}"
        except Exception as e:
            return f"❌ Screenshot failed: {str(e)}"