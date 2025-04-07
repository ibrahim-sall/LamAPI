FROM python:3.10-slim

# Install necessary system packages (if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy the source code
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir flask requests pillow tqdm numpy pyproj os laspy

# Expose port
EXPOSE 5000

# Make sure the script is executable
RUN chmod +x ./run-oscp-gpp-server.sh

# Run the server
CMD ["./run-oscp-gpp-server.sh"]
