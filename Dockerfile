FROM python:3.12-slim

WORKDIR /app

# Install dependencies first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Source code is bind-mounted at runtime, not copied
# This CMD is the default — docker-compose can override
CMD ["uvicorn", "src.dashboard.app:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]
