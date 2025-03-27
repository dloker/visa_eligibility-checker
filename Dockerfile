# Use an Alpine-based Python image
FROM python:3.10-alpine

# Set environment variables to prevent Python from writing .pyc files and buffering stdout.
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install build dependencies and git (if needed)
RUN apk update && apk add --no-cache gcc musl-dev libffi-dev openssl-dev

# Set working directory
WORKDIR /app

# Copy requirements.txt first to leverage Docker cache for dependencies.
COPY requirements.txt .

# Install Python dependencies.
RUN pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code.
COPY . .

# Expose port 8000
EXPOSE 8000

# Command to run the FastAPI application using Uvicorn.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
