FROM python:slim

RUN addgroup --system agc && adduser --system --home /app --ingroup agc agc


WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the project files into the container
COPY agent_guard_core /app/agent_guard_core
COPY *.md /app/
COPY requirements.txt /app/
COPY pyproject.toml /app/

# Install requirements directly (without editable mode)
RUN pip install --no-cache-dir .
RUN chown -R agc:agc /app
USER agc

# Set the entrypoint
ENTRYPOINT ["agc"]