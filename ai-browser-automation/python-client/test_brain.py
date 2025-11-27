from ai_handler import get_ai_response

# Mock tool definition just to test schema conversion
dummy_tools = [{
    "name": "navigate", 
    "description": "Go to a url", 
    "inputSchema": {"type": "object", "properties": {"url": {"type": "string"}}}
}]

# Mock history
messages = [{"role": "user", "content": "I want to navigate to google.com"}]

try:
    print("Sending request...")
    response = get_ai_response(messages, dummy_tools)
    print("\n✅ Success! Model Response Received:")
    print(response)
except Exception as e:
    print(f"\n❌ Error: {e}")
    print("Did you set your API Key?")