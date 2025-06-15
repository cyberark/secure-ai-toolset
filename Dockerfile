FROM python:3.11-slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
# Copy the project files into the container
COPY . /app/

# Install requirements directly (without editable mode)
RUN pip install --no-cache-dir .

# Set the entrypoint
ENTRYPOINT ["agc"]