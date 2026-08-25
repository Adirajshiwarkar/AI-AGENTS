# Build stage for React frontend
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY agent_project/frontend/package*.json ./
RUN npm ci
COPY agent_project/frontend/ ./
RUN npm run build

# Runtime stage for Python FastAPI
FROM python:3.11-slim
WORKDIR /app

# Install system dependencies (like curl for healthchecks)
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install
COPY agent_project/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY agent_project/ ./

# Copy built frontend assets from builder stage
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose Hugging Face Space port
EXPOSE 7860

# Run uvicorn server on port 7860
CMD ["python", "-m", "uvicorn", "app:app", "--host", "0.0.0.0", "--port", "7860"]
