import google.generativeai as genai
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    print("❌ Error: GOOGLE_API_KEY not found in .env file.")
    exit()

genai.configure(api_key=api_key)

print("\n🔎 Scanning available Google Models...\n")

# Define column headers
header = f"{'MODEL ID':<35} | {'DISPLAY NAME':<22} | {'IN LIMIT':<10} | {'OUT LIMIT':<10} | {'DESCRIPTION'}"
print(header)
print("-" * len(header))

try:
    # Get iterator and convert to list to sort alphabetically
    models = list(genai.list_models())
    models.sort(key=lambda x: x.name)

    for m in models:
        # We only care about models that can generate content (Chat/Text/Vision)
        if 'generateContent' in m.supported_generation_methods:
            
            # Extract attributes safely
            model_id = m.name
            display_name = m.display_name or "Unknown"
            
            # Token limits are integers, convert to string
            input_limit = str(m.input_token_limit)
            output_limit = str(m.output_token_limit)
            
            # Truncate description to keep table clean
            desc = m.description.replace("\n", " ")
            if len(desc) > 50:
                desc = desc[:47] + "..."

            # Print formatted row
            print(f"{model_id:<35} | {display_name:<22} | {input_limit:<10} | {output_limit:<10} | {desc}")

except Exception as e:
    print(f"\n❌ Error fetching models: {e}")
    print("Check your API Key and ensure the Generative AI API is enabled in Google Cloud Console.")