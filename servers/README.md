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
virtualenv .venv
source .venv/bin/activate 
pip install -r requirements.txt 
```

#### Install dependencies using uv

uv installation documentation can be found [here](https://docs.astral.sh/uv/getting-started/installation/)

```bash
uv venv
uv sync
```



### 2. Run the Admin UI Landing Page
Open a new terminal.
Assuming you are at the root directory of the project, start the landing page (Main UX) on port 8080 using these commands:
```bash
python  -m streamlit run servers/admin_ui/landing.py --server.port 8080 &
```

### 3. Run the API Server
Open a new terminal.
Assuming you are at the root directory of the project, start the API server on port 8081 using these commands:
```bash
python -m uvicorn servers.api_servers.main:app --host 0.0.0.0 --port 8081
```

#### Invoke the API to Get All Secrets
```bash
curl http://localhost:8081/secrets/
```

**Notes:**
- The secret provider is defined in the server configuration via the [UI](http://localhost:8080) (configuration page).
- The OpenAPI documentation is available [here](http://localhost:8081/docs).
- This method abstracts the secret providers.

#### Get All Environment Variables
Retrieve all environment variables:
```bash
curl http://localhost:8081/environment_variables/
```

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
