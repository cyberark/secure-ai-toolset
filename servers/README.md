# Servers Directory

This directory contains the server-side components of the Agent Guard project. Each server is responsible for handling specific functionalities and services required by the application.

## Structure

The `servers` directory includes the following:

- **Admin UI Server**: Provides a web-based interface for administrators to manage the API server.
- **REST API Server**: Handles REST API requests to fetch secrets.

## Getting Started

### 1. Install Dependencies
Navigate to the specific server directory and create a virtual environment:

#### Install dependencies using pip
```bash
python -m venv .venv
source .venv/bin/activate 
pip install -r requirements.txt 
pip install -r requirements-dev.txt  # optional dev dependencies
```

#### Install dependencies using uv

uv installation documentation can be found [here](https://docs.astral.sh/uv/getting-started/installation/)

```bash
uv venv
uv sync
```

### 2. Run the Admin UI and API Server
Open a new terminal.
Run this command, assuming your virtual env is created and installed
```bash
./run_servers
```

#### Invoke the API to get environment variables
```bash
curl http://localhost:8081/environment_variables/
```

**Notes:**
- The secret provider is configured via this page [UI](http://localhost:8080) (configuration page).
- The OpenAPI documentation is available [here](http://localhost:8081/docs).
- The server configuration is available [here](http://localhost:8081/config).
- This method abstracts the secret providers

#### Add an Environment Variable
Add a new environment variable:
```bash
curl -X POST "http://localhost:8081/environment_variables/MY_ENV_KEY4" \
-H "Content-Type: application/json" \
-d '{"value": "AA"}'
```

#### Get a specific environment variable
Get a new environment variable by key:
```bash
curl http://localhost:8081/environment_variables/MY_ENV_KEY4
```

## Contributing

- Follow the coding standards and guidelines outlined in the main project.
- Document any changes or additions to the servers in this README.

## Support

For issues or questions, please contact the project maintainers or open an issue in the repository.