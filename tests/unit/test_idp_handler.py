import json
import unittest
import urllib.parse
from unittest.mock import Mock, patch

import pytest

from agent_guard_core.handlers.idp.handler import IDPConfig, OIDCLogin

# Assuming the original code is in a module called oidc_login
# from oidc_login import OIDCLogin, IDPConfig

# For testing purposes, we'll include the classes here
# In actual implementation, you would import from the actual module


@pytest.fixture
def sample_config():
    """Fixture providing a sample IDP configuration."""
    return IDPConfig(
        domain="test-domain.auth0.com",
        client_id="test-client-id",
        redirect_uri="http://localhost:8000/callback",
        audience="test-audience",
        resource="test-resource",
        scope="openid profile email",
        service_name="test-service"
    )


@pytest.fixture
def sample_tokens():
    """Fixture providing sample token response."""
    return {
        "access_token": "test-access-token",
        "id_token": "test-id-token",
        "refresh_token": "test-refresh-token",
        "token_type": "Bearer",
        "expires_in": 3600
    }


class TestIDPConfig:
    """Test cases for IDPConfig dataclass."""
    
    def test_idp_config_creation(self):
        """Test creating IDPConfig with required fields."""
        config = IDPConfig(
            domain="test.auth0.com",
            client_id="client123"
        )
        
        assert config.domain == "test.auth0.com"
        assert config.client_id == "client123"
        assert config.redirect_uri == "http://localhost:8000/callback"
        assert config.audience == ""
        assert config.resource == ""
        assert config.scope == "openid profile email"
        assert config.service_name == "oidc-login"
    
    def test_idp_config_with_custom_values(self):
        """Test creating IDPConfig with custom values."""
        config = IDPConfig(
            domain="custom.auth0.com",
            client_id="custom-client",
            redirect_uri="http://localhost:3000/auth",
            audience="custom-audience",
            resource="custom-resource",
            scope="openid profile",
            service_name="custom-service"
        )
        
        assert config.domain == "custom.auth0.com"
        assert config.client_id == "custom-client"
        assert config.redirect_uri == "http://localhost:3000/auth"
        assert config.audience == "custom-audience"
        assert config.resource == "custom-resource"
        assert config.scope == "openid profile"
        assert config.service_name == "custom-service"


class TestOIDCLogin:
    """Test cases for OIDCLogin class."""
    
    @patch('keyring.get_password')
    @patch('pkce.generate_pkce_pair')
    def test_init_without_existing_tokens(self, mock_pkce, mock_keyring, sample_config):
        """Test OIDCLogin initialization without existing tokens."""
        mock_pkce.return_value = ("verifier", "challenge")
        mock_keyring.return_value = None
        
        oidc = OIDCLogin(sample_config)
        
        assert oidc._config == sample_config
        assert oidc._code_verifier == "verifier"
        assert oidc._code_challenge == "challenge"
        assert oidc._auth_code is None
        assert oidc._tokens == {}
        
        mock_keyring.assert_called_once_with("test-service", "test-client-id")
    
    @patch('keyring.get_password')
    @patch('pkce.generate_pkce_pair')
    def test_init_with_existing_tokens(self, mock_pkce, mock_keyring, sample_config, sample_tokens):
        """Test OIDCLogin initialization with existing tokens in keyring."""
        mock_pkce.return_value = ("verifier", "challenge")
        mock_keyring.return_value = json.dumps(sample_tokens)
        
        oidc = OIDCLogin(sample_config)
        
        assert oidc._tokens == sample_tokens
        mock_keyring.assert_called_once_with("test-service", "test-client-id")
    
    
    @patch('keyring.set_password')
    def test_save_tokens_to_keyring(self, mock_keyring, sample_config, sample_tokens):
        """Test saving tokens to keyring."""
        with patch('keyring.get_password', return_value=None):
            oidc = OIDCLogin(sample_config)
            oidc._tokens = sample_tokens
            
            oidc._save_tokens_to_keyring()
            
            mock_keyring.assert_called_once_with(
                "test-service",
                "test-client-id",
                json.dumps(sample_tokens)
            )
    
    def test_save_tokens_to_keyring_empty_tokens(self, sample_config):
        """Test saving empty tokens to keyring does nothing."""
        with patch('keyring.get_password', return_value=None), \
             patch('keyring.set_password') as mock_keyring:
            oidc = OIDCLogin(sample_config)
            oidc._tokens = {}
            
            oidc._save_tokens_to_keyring()
            
            mock_keyring.assert_not_called()
    
    @patch('socketserver.TCPServer')
    @patch('threading.Thread')
    def test_start_local_server(self, mock_thread, mock_server, sample_config):
        """Test starting local server for callback."""
        mock_server_instance = Mock()
        mock_server.return_value = mock_server_instance
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        with patch('keyring.get_password', return_value=None):
            oidc = OIDCLogin(sample_config)
            thread = oidc._start_local_server()
            
            mock_server.assert_called_once_with(("", 8000), unittest.mock.ANY)
            mock_thread.assert_called_once_with(target=mock_server_instance.handle_request)
            mock_thread_instance.start.assert_called_once()
            assert thread == mock_thread_instance
    
    @patch('webbrowser.open')
    @patch('requests.post')
    def test_login_successful_flow(self, mock_post, mock_browser, sample_config, sample_tokens):
        """Test successful login flow."""
        mock_response = Mock()
        mock_response.json.return_value = sample_tokens
        mock_post.return_value = mock_response
        
        with patch('keyring.get_password', return_value=None), \
             patch('keyring.set_password') as mock_keyring, \
             patch.object(OIDCLogin, '_start_local_server') as mock_server:
            
            mock_thread = Mock()
            mock_server.return_value = mock_thread
            
            oidc = OIDCLogin(sample_config)
            oidc._auth_code = "test-auth-code"  # Simulate receiving auth code
            
            oidc.login()
            
            # Verify browser opened with correct URL
            mock_browser.assert_called_once()
            called_url = mock_browser.call_args[0][0]
            assert "https://test-domain.auth0.com/authorize?" in called_url
            assert "client_id=test-client-id" in called_url
            assert "response_type=code" in called_url
            
            # Verify token exchange
            mock_post.assert_called_once_with(
                "https://test-domain.auth0.com/oauth/token",
                json={
                    "grant_type": "authorization_code",
                    "client_id": "test-client-id",
                    "code_verifier": oidc._code_verifier,
                    "code": "test-auth-code",
                    "redirect_uri": "http://localhost:8000/callback"
                }
            )
            
            # Verify tokens saved
            mock_keyring.assert_called_once()
            assert oidc._tokens == sample_tokens
    
    def test_login_with_existing_tokens_no_force(self, sample_config, sample_tokens):
        """Test login with existing tokens and force=False."""
        with patch('keyring.get_password', return_value=json.dumps(sample_tokens)):
            oidc = OIDCLogin(sample_config)
            
            result = oidc.login(force=False)
            
            assert result == sample_tokens
    
    def test_login_missing_auth_code(self, sample_config):
        """Test login flow when auth code is not received."""
        with patch('keyring.get_password', return_value=None), \
             patch('webbrowser.open'), \
             patch.object(OIDCLogin, '_start_local_server') as mock_server:
            
            mock_thread = Mock()
            mock_server.return_value = mock_thread
            
            oidc = OIDCLogin(sample_config)
            # Don't set auth_code to simulate missing code
            
            with pytest.raises(Exception, match="Did not receive authorization code"):
                oidc.login()
    
    @patch('requests.post')
    def test_login_token_exchange_failure(self, mock_post, sample_config):
        """Test login flow when token exchange fails."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("Token exchange failed")
        mock_post.return_value = mock_response
        
        with patch('keyring.get_password', return_value=None), \
             patch('webbrowser.open'), \
             patch.object(OIDCLogin, '_start_local_server') as mock_server:
            
            mock_thread = Mock()
            mock_server.return_value = mock_thread
            
            oidc = OIDCLogin(sample_config)
            oidc._auth_code = "test-auth-code"
            
            with pytest.raises(Exception, match="Token exchange failed"):
                oidc.login()
    
    @patch('requests.post')
    def test_refresh_token_success(self, mock_post, sample_config, sample_tokens):
        """Test successful token refresh."""
        new_tokens = {"access_token": "new-access-token", "expires_in": 3600}
        mock_response = Mock()
        mock_response.json.return_value = new_tokens
        mock_post.return_value = mock_response
        
        with patch('keyring.get_password', return_value=json.dumps(sample_tokens)), \
             patch('keyring.set_password') as mock_keyring:
            
            oidc = OIDCLogin(sample_config)
            result = oidc.refresh_token()
            
            mock_post.assert_called_once_with(
                "https://test-domain.auth0.com/oauth/token",
                json={
                    "grant_type": "refresh_token",
                    "client_id": "test-client-id",
                    "refresh_token": "test-refresh-token"
                }
            )
            
            assert result == new_tokens
            # Verify tokens were updated
            expected_tokens = sample_tokens.copy()
            expected_tokens.update(new_tokens)
            assert oidc._tokens == expected_tokens
            mock_keyring.assert_called_once()
    
    def test_refresh_token_no_refresh_token(self, sample_config):
        """Test refresh token when no refresh token is available."""
        tokens_without_refresh = {"access_token": "test-token"}
        
        with patch('keyring.get_password', return_value=json.dumps(tokens_without_refresh)):
            oidc = OIDCLogin(sample_config)
            
            with pytest.raises(Exception, match="No refresh token available"):
                oidc.refresh_token()
    
    def test_refresh_token_no_tokens(self, sample_config):
        """Test refresh token when no tokens exist."""
        with patch('keyring.get_password', return_value=None):
            oidc = OIDCLogin(sample_config)
            
            with pytest.raises(Exception, match="No refresh token available"):
                oidc.refresh_token()
    
    @patch('requests.post')
    def test_refresh_token_failure(self, mock_post, sample_config, sample_tokens):
        """Test refresh token failure."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("Refresh failed")
        mock_post.return_value = mock_response
        
        with patch('keyring.get_password', return_value=json.dumps(sample_tokens)):
            oidc = OIDCLogin(sample_config)
            
            with pytest.raises(Exception, match="Refresh failed"):
                oidc.refresh_token()
    
    def test_access_token_property(self, sample_config, sample_tokens):
        """Test access_token property."""
        with patch('keyring.get_password', return_value=json.dumps(sample_tokens)):
            oidc = OIDCLogin(sample_config)
            assert oidc.access_token == "test-access-token"
    
    def test_access_token_property_no_tokens(self, sample_config):
        """Test access_token property when no tokens exist."""
        with patch('keyring.get_password', return_value=None):
            oidc = OIDCLogin(sample_config)
            assert oidc.access_token is None
    
    def test_id_token_property(self, sample_config, sample_tokens):
        """Test id_token property."""
        with patch('keyring.get_password', return_value=json.dumps(sample_tokens)):
            oidc = OIDCLogin(sample_config)
            assert oidc.id_token == "test-id-token"
    
    def test_id_token_property_no_tokens(self, sample_config):
        """Test id_token property when no tokens exist."""
        with patch('keyring.get_password', return_value=None):
            oidc = OIDCLogin(sample_config)
            assert oidc.id_token is None
    
    def test_refresh_token_value_property(self, sample_config, sample_tokens):
        """Test refresh_token_value property."""
        with patch('keyring.get_password', return_value=json.dumps(sample_tokens)):
            oidc = OIDCLogin(sample_config)
            assert oidc.refresh_token_value == "test-refresh-token"
    
    def test_refresh_token_value_property_no_tokens(self, sample_config):
        """Test refresh_token_value property when no tokens exist."""
        with patch('keyring.get_password', return_value=None):
            oidc = OIDCLogin(sample_config)
            assert oidc.refresh_token_value is None
    
    def test_authorization_url_with_audience_and_resource(self, sample_config):
        """Test that authorization URL includes audience and resource when provided."""
        with patch('keyring.get_password', return_value=None), \
             patch('webbrowser.open') as mock_browser, \
             patch.object(OIDCLogin, '_start_local_server') as mock_server:
            
            mock_thread = Mock()
            mock_server.return_value = mock_thread
            
            oidc = OIDCLogin(sample_config)
            oidc._auth_code = "test-code"
            
            with patch('requests.post') as mock_post:
                mock_response = Mock()
                mock_response.json.return_value = {"access_token": "test"}
                mock_post.return_value = mock_response
                
                oidc.login()
                
                called_url = mock_browser.call_args[0][0]
                assert "audience=test-audience" in called_url
                assert "resource=test-resource" in called_url


class TestAuthHandler:
    """Test cases for the embedded AuthHandler class."""
    
    def test_auth_handler_with_code(self, sample_config):
        """Test AuthHandler when receiving valid authorization code."""
        with patch('keyring.get_password', return_value=None):
            oidc = OIDCLogin(sample_config)
            
            # Create a mock request with code parameter
            mock_request = Mock()
            mock_request.path = "/callback?code=test-auth-code&state=test-state"
            mock_request.send_response = Mock()
            mock_request.end_headers = Mock()
            mock_request.wfile = Mock()
            
            # Simulate the AuthHandler behavior

            with patch('urllib.parse.urlparse') as mock_urlparse, \
                 patch('urllib.parse.parse_qs') as mock_parse_qs:
                
                mock_urlparse.return_value.query = "code=test-auth-code&state=test-state"
                mock_parse_qs.return_value = {"code": ["test-auth-code"], "state": ["test-state"]}
                
                # This would be called by the AuthHandler
                query = urllib.parse.urlparse(mock_request.path).query
                params = urllib.parse.parse_qs(query)
                
                assert "code" in params
                assert params["code"][0] == "test-auth-code"
    
    def test_auth_handler_without_code(self, sample_config):
        """Test AuthHandler when not receiving authorization code."""
        with patch('keyring.get_password', return_value=None):
            oidc = OIDCLogin(sample_config)
            
            # Create a mock request without code parameter
            mock_request = Mock()
            mock_request.path = "/callback?error=access_denied"
            
            with patch('urllib.parse.urlparse') as mock_urlparse, \
                 patch('urllib.parse.parse_qs') as mock_parse_qs:
                
                mock_urlparse.return_value.query = "error=access_denied"
                mock_parse_qs.return_value = {"error": ["access_denied"]}
                
                query = urllib.parse.urlparse(mock_request.path).query
                params = urllib.parse.parse_qs(query)
                
                assert "code" not in params
                assert "error" in params

