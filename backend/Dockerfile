# Use the official Playwright image (includes Python + Browsers)
# This is crucial. Standard Python images will crash because they lack browser deps.
FROM mcr.microsoft.com/playwright/python:v1.44.0-jammy

WORKDIR /app

# 1. Install Python Dependencies
# We assume you have a requirements.txt. If not, we generate it below.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Install Chromium (Redundant with base image but good for safety)
RUN playwright install chromium

# 3. Copy Application Code
COPY . .

# 4. Create Video Directory with Permissions
RUN mkdir -p videos && chmod 777 videos

# 5. Run the Server
# Railway sets the PORT env var automatically.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]