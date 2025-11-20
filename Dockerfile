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

# Expose the port Cloud Run / Deployra will use
EXPOSE 8080

# Set environment variable for Flask inside the container
ENV PORT=8080

# Command to run the app
CMD ["python", "app.py"]
