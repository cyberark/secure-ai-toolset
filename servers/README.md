# Servers Directory

This directory contains the server-side components of the Agent Guard project. Each server is responsible for handling specific functionalities and services required by the application.

## Structure

The `servers` directory includes the following:

- **Admin UI Server**: Provides a web-based interface for administrators to manage the API server.
- **API Server**: Handles RESTful or GraphQL API requests and serves as the main entry point for client-server communication.

## Getting Started

1. **Install Dependencies**:  
   Navigate to the specific server directory and create a virtual environment:
   ```bash
   poetry env activate
   poetry install --with servers
   ```

2. **Run the Landing Page**:
    Assuming you are at the root directory of the project:
    Start the landing page (Main UX) using Streamlit on port 8080:
    ```bash
    streamlit run servers/admin_ui/landing.py --server.port 8080
    ```

3. **Run the API Server**:  
    Start the API server using Uvicorn on port 8081:
    ```bash
    cd servers/api_servers 
    python -m uvicorn main:app --host 0.0.0.0 --port 8081
    ```
    To invoke the API to get all secrets. 


    ```bash
    curl http://localhost:8081/secrets/
    ```
    Notes:
    - The secret provider is defined at the server configuration the [UI](http://localhost:8080) (configuration page)
    - The OpenAPI documentation is [here](http://localhost:8081/docs) 
    - This method abstracts the secret providers


    

## Contributing

- Follow the coding standards and guidelines outlined in the main project.
- Document any changes or additions to the servers in this README.

## Support

For issues or questions, please contact the project maintainers or open an issue in the repository.
