import http.server
import json
import logging
import socketserver
import threading
import urllib.parse
import webbrowser
from dataclasses import dataclass
from typing import Any, Optional

import keyring
import pkce
import requests

from agent_guard_core.handlers.idp.consts import ACCESS_TOKEN, ID_TOKEN, REFRESH_TOKEN

logger = logging.getLogger(__name__)

@dataclass
class IDPConfig:
    """
    Generic Identity Provider configuration.
    """
    domain: str                     # e.g. dev-abc123.us.auth0.com
    client_id: str
    client_secret: Optional[str] = None  
    redirect_uri: str = "http://localhost:5005/callback"
    audience: str = ""
    resource: str = ""
    scope: str = ""
    service_name: str = "oidc-login"  # keyring service name
    authorize_endpoint: str = "authorize"
    token_endpoint: str = "token"

class OIDCLogin:
    def __init__(self, config: IDPConfig):
        self._config = config
        self._code_verifier, self._code_challenge = pkce.generate_pkce_pair()
        self._auth_code = None
        self._tokens: dict[str, Any] = {}

        # Try to load tokens from keyring
        self._load_tokens_from_keyring()

    def _load_tokens_from_keyring(self):
        raw = keyring.get_password(self._config.service_name, self._config.client_id)
        if raw:
            try:
                self._tokens = json.loads(raw)
                logger.debug("Tokens loaded from keyring.")
            except json.JSONDecodeError as e:
                logger.error("Failed to decode tokens from keyring.", e)

    def _save_tokens_to_keyring(self):
        if self._tokens:
            keyring.set_password(
                self._config.service_name,
                self._config.client_id,
                json.dumps(self._tokens)
            )
            logger.debug("Tokens securely stored in keyring.")

    def _start_local_server(self):
        class AuthHandler(http.server.SimpleHTTPRequestHandler):
            def do_GET(inner_self):
                query = urllib.parse.urlparse(inner_self.path).query
                params = urllib.parse.parse_qs(query)
                if "code" in params:
                    self._auth_code = params["code"][0]
                    inner_self.send_response(200)
                    inner_self.end_headers()
                    inner_self.wfile.write(b"<h1>Login complete. You may close this window.</h1>")
                else:
                    inner_self.send_response(400)
                    inner_self.end_headers()
                    inner_self.wfile.write(b"Missing code parameter.")

        httpd = socketserver.TCPServer(("", 5005), AuthHandler)
        thread = threading.Thread(target=httpd.handle_request)
        thread.daemon = True
        thread.start()
        return thread

    def login(self, force: bool = True) -> None:
        """
        Initiate login flow. If tokens already loaded from keyring and not forced,
        will reuse existing tokens.
        """
        if self._tokens and not force:
            logger.info("Using existing tokens from keyring. Use force=True to re-login.")
            return self._tokens

        # Build authorization URL
        params = {
            "response_type": "code",
            "redirect_uri": self._config.redirect_uri,
            "code_challenge": self._code_challenge,
            "code_challenge_method": "S256",
        }

        if self._config.audience:
            params["audience"] = self._config.audience
        if self._config.resource:
            params["resource"] = self._config.resource
        if self._config.client_secret:
            params["client_secret"] = self._config.client_secret
        if self._config.scope:
            params["scope"] = self._config.scope
        if self._config.client_id:
            params["client_id"] = self._config.client_id

        url = f"https://{self._config.domain}/{self._config.authorize_endpoint}?" + urllib.parse.urlencode(params)
        logger.info(f"Opening browser to: {url}")

        server_thread = self._start_local_server()
        logger.info("Opening browser with URL\n%s", url)
        webbrowser.open(url)

        server_thread.join()
        if not self._auth_code:
            raise Exception("Did not receive authorization code.")

        # Exchange code for tokens
        token_url = f"https://{self._config.domain}/{self._config.token_endpoint}"
        token_data = {
            "grant_type": "authorization_code",
            "client_id": self._config.client_id,
            "code_verifier": self._code_verifier,
            "code": self._auth_code,
            "redirect_uri": self._config.redirect_uri,
            "nonce": "abc",
        }
        response = requests.post(token_url, data=token_data)
        response.raise_for_status()
        self._tokens = response.json()
        self._save_tokens_to_keyring()

        logger.info("Login successful")

    def refresh_token(self):
        if not self._tokens or "refresh_token" not in self._tokens:
            raise Exception("No refresh token available. Ensure your IDP issues refresh tokens and scope includes 'offline_access'.")

        token_url = f"https://{self._config.domain}/{self._config.token_endpoint}"
        token_data = {
            "grant_type": "refresh_token",
            "client_id": self._config.client_id,
            "refresh_token": self._tokens["refresh_token"]
        }
        response = requests.post(token_url, json=token_data)
        response.raise_for_status()
        new_tokens = response.json()
        self._tokens.update(new_tokens)
        self._save_tokens_to_keyring()
        logger.debug("Access token refreshed!")
        return new_tokens

    @property
    def access_token(self):
        return self._tokens.get(ACCESS_TOKEN) if self._tokens else None

    @property
    def id_token(self):
        return self._tokens.get(ID_TOKEN) if self._tokens else None

    @property
    def refresh_token_value(self):
        return self._tokens.get(REFRESH_TOKEN) if self._tokens else None


# =====================================================
# Example usage
# =====================================================
if __name__ == "__main__":
    config = IDPConfig(
        domain="dev-4jacj8b580bps666.us.auth0.com",
        client_id="k7RrMA7YbQGaTe5uJsw8d7fZiHz6nU0w",
        audience=""  # or set resource for Azure
    )

    config = IDPConfig( # Creates an access token, but can't post to SIA SSO (unauthorized)
        domain="alr5172.id.integration-cyberark.cloud",
        client_id="agc",
        authorize_endpoint="oauth2/authorize/__agcapp",
        token_endpoint="oauth2/token/__agcapp",
        scope="api profile"#scope="dpa DPA adb"
    )

    config = IDPConfig(
        domain="alr5172.id.integration-cyberark.cloud",
        client_id="__idaptive_cybr_user_oidc",
        authorize_endpoint="oauth2/authorize/__idaptive_cybr_user_oidc",
        token_endpoint="oauth2/token/__idaptive_cybr_user_oidc",
        scope="openid api profile",
        redirect_uri="https://chat-sia.integration-cyberark.cloud/",
    )

    config = IDPConfig(
        domain="alr5172.id.integration-cyberark.cloud",
        client_id="0ded131f-a0ba-42c6-8c29-d1fee00cab91",
        authorize_endpoint="oauth2/authorize/__agcoid",
        token_endpoint="oauth2/token/__agcoid",
        scope="api profile"
    )

    config = IDPConfig( # WORKING AND I GET AUTHENTICATE
        domain="alr5172.id.integration-cyberark.cloud",
        client_id="agc",
        authorize_endpoint="oauth2/authorize/__agcserver",
        token_endpoint="oauth2/token/__agcserver",
        scope="full"#"full"#"full"
    )

    config = IDPConfig( 
        domain="alr5172.id.integration-cyberark.cloud",
        client_id="__idaptive_cybr_user_oidc",
        authorize_endpoint="oauth2/authorize/__agcserver",
        token_endpoint="oauth2/token/__agcserver",
        scope="api profile"#"full"#"full"
    )

    oidc = OIDCLogin(config)
    tokens = oidc.login()  # will reuse from keyring if present

    print("Access Token:", oidc.access_token)
    print("ID Token:", oidc.id_token)

    # # Refresh example
    # if oidc.refresh_token_value:
    #     oidc.refresh_token()
    #     print("New Access Token:", oidc.access_token)
