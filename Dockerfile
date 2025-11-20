# Use official Python image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements first for caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

# Informational port (not required by platform)
EXPOSE 8080

# Default fallback port (overridden by platform)
ENV PORT=8080

# Start the app
CMD ["python", "app.py"]
