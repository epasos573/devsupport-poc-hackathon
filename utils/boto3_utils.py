import boto3
import logging
import os
from botocore.exceptions import ClientError
from typing import Dict, Optional

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class SSM:
    # Class attributes to store secrets and paths
    _SECRETS: Dict[str, Optional[str]] = {}
    _PATHS: Dict[str, Optional[str]] = {
        "auth_token": os.environ.get("AUTH_KEY"),
        "openai_token": os.environ.get("OPENAI_TOKEN"),
        "rds_username": os.environ.get("RDS_USERNAME"),
        "rds_password": os.environ.get("RDS_PASSWORD"),
        "rds_host": os.environ.get("RDS_HOST"),
        "rds_scheme": os.environ.get("RDS_SCHEME"),
        "zendesk_client_url": os.environ.get("ZENDESK_CLIENT_URL"),
        "zendesk_client_email": os.environ.get("ZENDESK_CLIENT_EMAIL"),
        "zendesk_client_api_token": os.environ.get("ZENDESK_CLIENT_API_TOKEN"),
        "gspread_project_id": os.environ.get("GSPREAD_PROJECT_ID"),
        "gspread_private_key_id": os.environ.get("GSPREAD_PRIVATE_KEY_ID"),
        "gspread_private_key": os.environ.get("GSPREAD_PRIVATE_KEY"),
        "gspread_client_id": os.environ.get("GSPREAD_CLIENT_ID"),
        "intercom_client_url": os.environ.get("INTERCOM_CLIENT_URL"),
        "intercom_client_api_token": os.environ.get("INTERCOM_CLIENT_API_TOKEN"),
        "domain_providers_to_remove": os.environ.get("DOMAIN_PROVIDERS_TO_REMOVE"),
    }

    @classmethod
    def get_secret(cls, key: str) -> Optional[str]:
        """
        Retrieves the secret value from the SECRETS dictionary or environment variables.

        Args:
            key (str): The key for the secret to retrieve.

        Returns:
            Optional[str]: The secret value or None if not found.
        """
        return cls._SECRETS.get(key, os.environ.get(key.upper()))

    @classmethod
    def _retrieve_secrets_from_aws_secrets_manager(cls, parameter_path: str) -> str:
        """
        Retrieves a secret value from AWS Secrets Manager.

        Args:
            parameter_path (str): The path of the parameter in AWS Secrets Manager.

        Returns:
            str: The secret value retrieved from AWS Secrets Manager.

        Raises:
            ClientError: If there is an error retrieving the parameter from AWS Secrets Manager.
        """
        # Create a Secrets Manager client
        session = boto3.session.Session()
        client = session.client(service_name='ssm', region_name='us-east-1')

        try:
            # Get the parameter value with decryption
            parameter_value = client.get_parameter(Name=parameter_path, WithDecryption=True)['Parameter']['Value']
        except ClientError as e:
            # Log the error and re-raise the exception
            logger.error(f"Failed to get parameter: {parameter_path}. Error: {e}")
            raise e

        return parameter_value

    @classmethod
    def _set_secrets(cls, secrets: Dict[str, Optional[str]]) -> None:
        """
        Sets the SECRETS class attribute.

        Args:
            secrets (Dict[str, Optional[str]]): A dictionary of secrets to set.
        """
        cls._SECRETS = secrets

    @classmethod
    def _set_paths(cls, paths: Dict[str, Optional[str]]) -> None:
        """
        Sets the PATHS class attribute.

        Args:
            paths (Dict[str, Optional[str]]): A dictionary of paths to set.
        """
        cls._PATHS = paths

    @classmethod
    def get_secrets(cls) -> Dict[str, Optional[str]]:
        """
        Gets the SECRETS class attribute.

        Returns:
            Dict[str, Optional[str]]: The dictionary of secrets.
        """
        return cls._SECRETS

    @classmethod
    def get_paths(cls) -> Dict[str, Optional[str]]:
        """
        Gets the PATHS class attribute.

        Returns:
            Dict[str, Optional[str]]: The dictionary of paths.
        """
        return cls._PATHS

    @staticmethod
    def load_secrets() -> None:
        """
        Loads secrets from AWS Secrets Manager into the SECRETS class attribute.
        """
        secrets = {}
        for param in SSM.get_paths():
            print(f"Loading param: {param}")
            if SSM.get_paths().get(param):
                #secrets[param] = SSM._retrieve_secrets_from_aws_secrets_manager(SSM.get_paths().get(param))
                #secrets[param] = SSM.get_paths().get(param)
                print(f"value: {SSM.get_paths().get(param)}")
        SSM._set_secrets(secrets)

# Load secrets into the SECRETS class attribute
#SSM.load_secrets()
