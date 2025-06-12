FROM python:3.9-slim

WORKDIR /app

# Copy the project files into the container
COPY . /app/

# Install the project
RUN pip install --no-cache-dir -e .

# Set the entrypoint
ENTRYPOINT ["agc"]