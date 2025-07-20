from enum import Enum

class EnhancedStrEnum(str, Enum):
    """Base class for string enums with enhanced string behavior"""
    
    def __str__(self):
        return self.value
    
    def __repr__(self):
        return self.value

class CredentialsProvider(EnhancedStrEnum):
    AWS_SECRETS_MANAGER = "aws"
    CONJUR = "conjur"
    FILE_DOTENV = "file-dotenv"
    GCP_SECRETS_MANAGER = "gcp"
    
class ConjurEnvVars(EnhancedStrEnum):
    CONJUR_AUTHN_LOGIN = "CONJUR_AUTHN_LOGIN" 
    CONJUR_APPLIANCE_URL = "CONJUR_APPLIANCE_URL" 
    CONJUR_AUTHENTICATOR_ID = "CONJUR_AUTHENTICATOR_ID" 
    CONJUR_ACCOUNT = "CONJUR_ACCOUNT" 
    CONJUR_API_KEY = "CONJUR_API_KEY"
    CONJUR_AUTHN_IAM_REGION = "CONJUR_AUTHN_IAM_REGION" 
    CONJUR_AUTHN_API_KEY = "CONJUR_AUTHN_API_KEY" 
    CONJUR_AUTHN_JWT = "CONJUR_AUTHN_JWT"

class AwsEnvVars(EnhancedStrEnum):
    AWS_REGION = "AWS_REGION"
    AWS_ACCESS_KEY_ID = "AWS_ACCESS_KEY_ID"
    AWS_SECRET_ACCESS_KEY = "AWS_SECRET_ACCESS_KEY"

class GcpEnvVars(EnhancedStrEnum):
    GCP_PROJECT_ID = "GCP_PROJECT_ID"
    GCP_SECRET_ID = "GCP_SECRET_ID"
    GCP_REGION = "GCP_REGION"
    GCP_REPLICATION_TYPE = "GCP_REPLICATION_TYPE"