# UPython slim image
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Run the app
CMD ["python", "papersMCP.py"]