FROM python:slim

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
# Copy the project files into the container
COPY agent_guard_core /app/agent_guard_core
COPY *.md /app/
COPY requirements.txt /app/
COPY pyproject.toml /app/
RUN ls -al /app/

# Install requirements directly (without editable mode)
RUN pip install --no-cache-dir .

# Set the entrypoint
ENTRYPOINT ["agc"]