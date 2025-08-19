import os
import logging
import json
import openai
from typing import Any, Dict, Union

from utils.boto3_utils import SSM

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenAiClient:
    def __init__(self) -> None:
        """
        Initializes the OpenAiClient by setting up the OpenAI client with the API token.
        Retrieves the token from AWS Systems Manager.
        """
        self._api = None  # Private attribute for API name
        self._endpoint = None  # Private attribute for endpoint name
        self._method = None  # Private attribute for method name

        # Get the OpenAI API token from AWS Secrets Manager
        api_token = SSM.get_secret('openai_token')

        try:
            # Initialize the OpenAI client with the retrieved API token
            self.client = openai.OpenAI(api_key=api_token)
        except Exception as e:
            # Handle exceptions during client initialization
            self.openai_exception_handler(e)

    @property
    def api(self) -> Union[str, None]:
        """Getter for the private _api attribute."""
        return self._api

    @api.setter
    def api(self, value: str) -> None:
        """Setter for the private _api attribute."""
        self._api = value

    @property
    def endpoint(self) -> Union[str, None]:
        """Getter for the private _endpoint attribute."""
        return self._endpoint

    @endpoint.setter
    def endpoint(self, value: str) -> None:
        """Setter for the private _endpoint attribute."""
        self._endpoint = value

    @property
    def method(self) -> Union[str, None]:
        """Getter for the private _method attribute."""
        return self._method

    @method.setter
    def method(self, value: str) -> None:
        """Setter for the private _method attribute."""
        self._method = value

    def call_openai(self, api: str = 'chat', endpoint: str = 'completions', method: str = 'create', **kwargs: Any) -> Dict[str, Any]:
        """
        Calls the OpenAI API based on the specified API and action.
        
        Args:
            api (str): The API within the OpenAI client (e.g., 'chat').
            endpoint (str): The API endpoint to call (e.g., 'completions').
            method (str): The method to execute on the API (e.g., 'create').
            **kwargs: Additional arguments to pass to the API action.

        Returns:
            Dict[str, Any]: The response from the OpenAI API or the error response.
        """
        self.api = api
        self.endpoint = endpoint
        self.method = method

        # Dynamically retrieve the API, endpoint and method from the OpenAI client
        client_api = getattr(self.client, api)
        client_endpoint = getattr(client_api, endpoint)
        client_method = getattr(client_endpoint, method)

        try:
            # Call the specified method with provided keyword arguments
            return client_method(**kwargs)
        except Exception as e:
            # Handle exceptions during API call
            return self.openai_exception_handler(e)

    def send_prompt(self, context: str, prompt: str, model: str = 'gpt-4o') -> dict:
        """
        Sends a prompt to the OpenAI API and retrieves the first choice message.

        Args:
            context (str): The context for the prompt (e.g., system messages or instructions).
            prompt (str): The user prompt to send to OpenAI.
            model (str): The model to use (default is 'gpt-4o-mini').

        Returns:
            dict: The response from the OpenAI API or an error response.
        """
        # Validate context and prompt types
        if not isinstance(context, str) or not isinstance(prompt, str):
            return {
                'statusCode': 400,
                'body': json.dumps({'error': "Both 'context' and 'prompt' must be strings."})
            }

        # Check if context and prompt are not empty
        if not context or not prompt:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': "'context' and 'prompt' cannot be empty strings."})
            }

        # Prepare the messages for the API call
        messages = [
            {'role': 'system', 'content': context},
            {'role': 'user', 'content': prompt}
        ]

        try:
            # Call the OpenAI API with the provided messages and model
            response = self.call_openai(api='chat', endpoint='completions', method='create', messages=messages, model=model)
            logger.info(f"OpenAI response: {response}")

            # Check if the response contains choices
            if hasattr(response, 'choices') and len(response.choices) > 0:
                # Extract the first choice message
                first_choice_message = response.choices[0].message.content
                token_usage = self.serialize(response.usage)
                return {
                    'statusCode': 200,
                    'body': json.dumps({
                        'openai_response': first_choice_message,
                        'token_usage': token_usage
                    })
                }
            else:
                return {
                    'statusCode': 500,
                    'body': json.dumps({'error': "No choices were returned in the response."})
                }
        except Exception as e:
            # Handle exceptions during prompt sending
            return self.openai_exception_handler(e)

    def openai_exception_handler(self, exception: Exception) -> Dict[str, Any]:
        """
        Handles OpenAI API exceptions and returns an appropriate error response.

        Args:
            exception (Exception): The exception raised by the OpenAI API.

        Returns:
            Dict[str, Any]: A dictionary containing the status code and error message.
        """
        if isinstance(exception, openai.APIConnectionError):
            logger.error("Could not connect to OpenAI servers. Reason: {}".format(exception.__cause__))
            return {
                'statusCode': 503,
                'body': json.dumps({'error': "Could not connect to OpenAI servers. Please contact the CS-Dev team."})
            }
        elif isinstance(exception, openai.RateLimitError):
            logger.error("A 429 status code was received; we should back off a bit.")
            return {
                'statusCode': 429,
                'body': json.dumps({'error': "Too many requests. Please try again later."})
            }
        else:
            # Handle general OpenAI errors
            logger.error("An error code was returned from OpenAI. Reason: {}".format(exception))
            return {
                'statusCode': 400,
                'body': json.dumps({'error': f"Error from OpenAI: {str(exception)}. Please contact CS-Dev for further details."})
            }

    # Convert response.usage.__dict__ into a JSON-serializable format
    def serialize(self, obj: Any) -> Union[dict, list, str, int, float, bool, None]:
        """
        Recursively serialize an object into a JSON-serializable structure.

        :param obj: The object to serialize. Can be any type.
        :return: A JSON-serializable structure (dict, list, or primitive type).
        """
        if hasattr(obj, '__dict__'):  # Handle custom objects
            return {key: self.serialize(value) for key, value in obj.__dict__.items()}  # Use self.serialize
        elif isinstance(obj, list):  # Handle lists
            return [self.serialize(item) for item in obj]  # Use self.serialize
        elif isinstance(obj, dict):  # Handle dictionaries
            return {key: self.serialize(value) for key, value in obj.items()}  # Use self.serialize
        else:  # Return primitive types as-is
            return obj
