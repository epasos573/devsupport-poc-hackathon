import json
import copy
import inspect
from typing import Union


import requests
import six

if six.PY2:
    from httplib import responses
    from urlparse import urlsplit
else:
    from http.client import responses
    from urllib.parse import urlsplit

from requests.auth import HTTPBasicAuth


# Compatability with Python 3.10
try:
    from collections.abc import Iterable
except ImportError:
    from collections import Iterable




######### Zendesk Error Objects

class ZendeskError(Exception):
    """
    A custom exception class to represent errors encountered when interacting with the Zendesk API.

    This class extends the base `Exception` class and is used to capture error information related to 
    failed API requests, including the error message, error code, and response from Zendesk.

    Attributes:
        class_name (str): The name of the class, which is 'ZendeskError' for this class.
        message (str): The error message associated with the exception.
        error_code (int): The HTTP status code or error code returned by Zendesk in the response.
        response (str): The full response from the Zendesk API that triggered the error.

    Args:
        message (str): A description or message detailing the error.
        code (int): The error code or HTTP status code returned by Zendesk.
        response (str): The full response body or details returned by the Zendesk API.

    Methods:
        __str__(): Returns a string representation of the error, including class name, error code, 
                   message, and response details.

    Example:
        raise ZendeskError("Invalid ticket ID", 404, "Ticket not found")
        # This would raise a ZendeskError with the provided message, code, and response.

    Notes:
        - This class can be used as a base for creating more specific error types (e.g., `AuthenticationError`, 
          `RateLimitError`).
    """
    def __init__(self, message, code, response):
        # Initialize the error attributes
        self.class_name = self.__class__.__name__
        self.message = message
        self.error_code = code
        self.response = response

    def __str__(self):
        return repr('%s: %s - %s %s' % (self.class_name, self.error_code, self.message, self.response))


class AuthenticationError(ZendeskError):
    """
    A specific exception class to represent authentication errors when interacting with the Zendesk API.

    This class extends the `ZendeskError` class and is raised when the API returns an authentication-related error,
    such as invalid credentials or missing API key.

    Inherits from:
        ZendeskError: The base class that captures the general structure and behavior of Zendesk-related errors.

    Example:
        raise AuthenticationError("Invalid API key", 401, "Unauthorized access")
        # This would raise an AuthenticationError with a message indicating an authentication failure.

    Notes:
        - This class can be caught separately to handle authentication issues specifically, 
          distinct from other Zendesk API errors.
    """
    pass


class RateLimitError(ZendeskError):
    """
    A specific exception class to represent rate-limiting errors encountered when interacting with the Zendesk API.

    This class extends the `ZendeskError` class and is raised when the API returns an error indicating that 
    the rate limit has been exceeded, and further requests should be delayed.

    Inherits from:
        ZendeskError: The base class that captures the general structure and behavior of Zendesk-related errors.

    Example:
        raise RateLimitError("Rate limit exceeded", 429, "Too many requests")
        # This would raise a RateLimitError with a message indicating the rate limit has been hit.

    Notes:
        - This class can be caught separately to handle rate-limiting issues specifically, 
          and apply backoff strategies to retry the request after the rate limit is reset.
    """
    pass






######### Zendesk Interface Objects

class ZendeskInterface(object):
    """
    Interface class for Zendesk API calls.

    This class serves as a base interface for interacting with the Zendesk API. It contains methods to make API 
    requests to the Zendesk service, with support for common features like pagination, retries, and response customization.

    Notes:
        - This class is intended to be subclassed or extended in specific use cases for actual API calls.
        - The methods in this class do not directly interact with Zendesk but serve as a framework for API interactions.
    """

    def __init__(self):

        """
        Constructor method for the ZendeskInterface class.

        This method initializes the class, but currently, it doesn't perform any specific initialization logic.

        Notes:
            - This method can be extended in subclasses to set up any specific configurations, 
              such as API credentials or custom settings.
        """

        pass

    def call_zendeskapi(self, path, query = None, method = 'GET', data = None,
            get_all_pages = False, complete_response = False, retry_on = None, max_retries = 0, retval = None,
            **kwargs):
        
        """
        Makes API calls to the Zendesk service.

        This method is responsible for making HTTP requests to the Zendesk API. It supports various configurations 
        for handling query parameters, request methods (GET, POST, etc.), pagination, retries, and response handling.

        Args:
            path (str): The API endpoint to call. This is the relative URL path for the Zendesk API.
            query (dict, optional): A dictionary of query parameters to include in the request URL (default is None).
            method (str, optional): The HTTP method to use for the request (e.g., 'GET', 'POST', etc.; default is 'GET').
            data (dict, optional): The data to send with the request (used for methods like POST or PUT; default is None).
            get_all_pages (bool, optional): If True, will automatically handle pagination and retrieve all available pages 
                                             of results (default is False).
            complete_response (bool, optional): If True, returns the full response from the Zendesk API instead of just the data.
            retry_on (str or list, optional): A condition (e.g., HTTP error code) on which to retry the request (default is None).
            max_retries (int, optional): The maximum number of retries to attempt if the request fails (default is 0).
            retval (any, optional): A variable to store the return value of the request (default is None).
            **kwargs: Any additional keyword arguments that can be passed to customize the request.

        Returns:
            dict or None: The data returned by the Zendesk API in the response, or None if the request fails.
        
        Raises:
            Exception: If there is an error making the API call or if the response is invalid.
        
        Notes:
            - The method automatically retries the request if `retry_on` is provided and the response 
              meets the retry condition. The number of retries is limited by the `max_retries` argument.
            - If `get_all_pages` is set to True, the method will iterate over all pages of results and 
              return the combined data.
            - If `complete_response` is True, the method returns the full API response object, including headers and metadata.
            - This method is designed to be flexible for various types of API requests, but some functionality 
              (e.g., pagination or retry logic) may need to be adapted for specific use cases.
        
        Example:
            zendesk = ZendeskInterface()
            response = zendesk.call_zendeskapi(
                path='/tickets.json',
                query={'status': 'open'},
                method='GET',
                get_all_pages=True,
                retry_on='503',  # Retry on service unavailable errors
                max_retries=3
            )
            
            # This will print the list of open tickets, retrying up to 3 times on 503 errors, and retrieving all pages.
        """
        pass



    def ticket_create(self, data):
        """
        Reference: https://developer.zendesk.com/api-reference/ticketing/tickets/tickets/#create-ticket
        """
        api_path = "/api/v2/tickets"
        return self.call_zendeskapi(api_path, method="POST", data=data)

    def ticket_show(self, ticket_id):
        """
        Reference: https://developer.zendesk.com/api-reference/ticketing/tickets/tickets/#show-ticket
        """
        api_path = f'/api/v2/tickets/{ticket_id}'
        return self.call_zendeskapi(api_path, method="GET")

    def ticket_update(self, ticket_id, data):
        """
        Reference: https://developer.zendesk.com/api-reference/ticketing/tickets/tickets/#update-ticket
        """
        api_path = f'/api/v2/tickets/{ticket_id}'
        return self.call_zendeskapi(api_path, method="PUT", data=data)




    def ticket_list_comments(self, ticket_id):
        """
        Reference: https://developer.zendesk.com/api-reference/ticketing/tickets/ticket_comments/#list-comments
        """
        api_path = f'/api/v2/tickets/{ticket_id}/comments'
        return self.call_zendeskapi(api_path, method="GET")


    def ticket_show_user(self, user_id):
        """
        Reference: https://developer.zendesk.com/api-reference/ticketing/users/users/#show-user
        """
        api_path = f'/api/v2/users/{user_id}'
        return self.call_zendeskapi(api_path, method="GET")


    def ticket_show_users_by_author_ids(self, author_ids):
        """
        Reference: https://developer.zendesk.com/api-reference/ticketing/users/users/#show-many-users
        """
        api_path = f'/api/v2/users/show_many?ids={author_ids}'
        return self.call_zendeskapi(api_path, method="GET")    


    def ticket_show_users_by_ids(self, user_ids):
        """
        Reference: https://developer.zendesk.com/api-reference/ticketing/users/users/#show-many-users
        """
        api_path = f'/api/v2/users/show_many?ids={user_ids}'
        return self.call_zendeskapi(api_path, method="GET")    





######### Zendesk Client Object


ACCEPTED_ERROR_RETRIES = ZendeskError, requests.RequestException



class ZendeskClient(ZendeskInterface):
    """
    Wrapper class for the Zendesk Client application.

    This class extends `ZendeskInterface` and provides a more specific implementation of 
    Zendesk API interactions, including handling authentication, retry logic, and processing 
    of API responses. It is designed to manage communication with Zendesk’s API using various 
    authentication methods and providing additional convenience features for handling retries 
    and pagination.

    Attributes:
        _zd_url (str): The base URL of the Zendesk API.
        _zd_email (str): The email address used for authentication (if using email-based authentication).
        _zd_password (str): The password for email-based authentication.
        _zd_is_token (bool): A flag indicating if an API token is being used for authentication.
        _zd_oauth (str): The OAuth token used for authentication (if applicable).
        _zd_api_token (str): The API token used for authentication (if applicable).
        _retry_on (str): The condition on which to retry the request (e.g., '503', 'timeout').
        _max_retries (int): The maximum number of retries to attempt for a failed request.

    Args:
        zd_url (str): The URL of the Zendesk service.
        zd_email (str, optional): The email address used for basic authentication (default is None).
        zd_password (str, optional): The password for authentication (default is None).
        zd_is_token (bool, optional): Flag indicating if an API token is being used (default is False).
        zd_oauth (str, optional): OAuth token for authentication (default is None).
        zd_api_token (str, optional): API token for authentication (default is None).
        retry_on (str, optional): Condition on which to retry (e.g., '503', 'timeout'; default is None).
        max_retries (int, optional): Maximum number of retries in case of failure (default is 0).
    """

    def __init__(self, zd_url, zd_email = None, zd_password= None, zd_is_token = False, 
                       zd_oauth = None, zd_api_token = None, retry_on = None, max_retries = 0):
        """
        Instantiates an instance of ZendeskClient and configures optional authentication parameters.
        
        Args:
            zd_url (str): The base URL of the Zendesk service.
            zd_email (str, optional): The email for authentication if using basic authentication (default is None).
            zd_password (str, optional): The password for basic authentication (default is None).
            zd_is_token (bool, optional): Whether to use an API token for authentication (default is False).
            zd_oauth (str, optional): OAuth token for authentication (default is None).
            zd_api_token (str, optional): The API token for authentication (default is None).
            retry_on (str, optional): Condition under which to retry failed requests (default is None).
            max_retries (int, optional): Maximum retry attempts for failed requests (default is 0).
        
        Initializes the authentication parameters and other settings for the Zendesk client.
        """

        # Initialize all private properties
        self._zd_url        = None
        self._zd_email      = None
        self._zd_password   = None
        self._zd_is_token   = False
        self._zd_oauth      = None
        self._zd_api_token  = None
        self._retry_on      = {}
        self._max_retries   = 0
        

        # Set all the property values
        self.zd_url         = zd_url        # zd_url.rstrip('/')
        self.zd_email       = zd_email
        self.zd_password    = zd_password
        self.zd_is_token    = zd_is_token
        self.zd_oauth       = zd_oauth
        self.zd_api_token   = zd_api_token
        self.retry_on       = retry_on
        self.max_retries    = max_retries


    ###################################
    ### Property section

    @property
    def zd_url(self) -> Union[str, None]:
        """Getter for the private _zd_url attribute."""
        return self._zd_url

    @zd_url.setter
    def zd_url(self, value: str) -> None:
        """Setter for the private _zd_url attribute."""
        self._zd_url = value


    @property
    def zd_email(self) -> Union[str, None]:
        """Getter for the private _zd_email attribute."""
        return self._zd_email

    @zd_email.setter
    def zd_email(self, value: str) -> None:
        """Setter for the private _zd_email attribute."""
        self._zd_email = value


    @property
    def zd_password(self) -> Union[str, None]:
        """Getter for the private _zd_password attribute."""
        return self._zd_password

    @zd_password.setter
    def zd_password(self, value: str) -> None:
        """Setter for the private _zd_password attribute."""
        self._zd_password = value


    @property
    def zd_is_token(self) -> Union[str, None]:
        """Getter for the private _zd_is_token attribute."""
        return self._zd_is_token

    @zd_is_token.setter
    def zd_is_token(self, value: str) -> None:
        """Setter for the private _zd_is_token attribute."""
        self._zd_is_token = value


    @property
    def zd_oauth(self) -> Union[str, None]:
        """Getter for the private _zd_oauth attribute."""
        return self._zd_oauth

    @zd_oauth.setter
    def zd_oauth(self, value: str) -> None:
        """Setter for the private _zd_oauth attribute."""
        self._zd_oauth = value


    @property
    def zd_api_token(self) -> Union[str, None]:
        """Getter for the private _zd_api_token attribute."""
        return self._zd_api_token

    @zd_api_token.setter
    def zd_api_token(self, value: str) -> None:
        """Setter for the private _zd_api_token attribute."""
        self._zd_api_token = value


    @property
    def retry_on(self):
        """Getter for the private _retry_on attribute."""
        return self._retry_on

    @retry_on.setter
    def retry_on(self, value):
        """Setter for the private _zd_api_token attribute."""

        if value is None:
            self._retry_on = set()
            return

        def _validate(v):
            exc = ("retry_on property must contain only non-2xx HTTP codes"
                   "or members of %s" % (ACCEPTED_ERROR_RETRIES, ))

            if inspect.isclass(v):
                if not issubclass(v, ACCEPTED_ERROR_RETRIES):
                    raise ValueError(exc)
            elif isinstance(v, int):
                if 200 <= v < 300:
                    raise ValueError(exc)
            else:
                raise ValueError(exc)

        if isinstance(value, Iterable):
            for v in value:
                _validate(v)
            self._retry_on = set(value)
        else:
            _validate(value)
            self._retry_on = set([value])


    @property
    def max_retries(self):
        """Getter for the private _max_retries attribute."""
        return self._max_retries

    @max_retries.setter
    def max_retries(self, value):
        """Setter for the private _max_retries attribute."""
        try:
            value = int(value)
            if value < 0:
                raise ValueError
        except (TypeError, ValueError):
            raise ValueError("max_retries must be non-negative integer")

        self._max_retries = value








    ###################################
    ### Method section


    def _handle_retry(self, resp):
        """
        Handles any exceptions during an API request or parsing its response status code.

        Args:
            resp (requests.Response): The response object returned from the Zendesk API.

        This method is responsible for determining whether a request should be retried based on the response 
        status code or any other custom conditions defined by the `retry_on` attribute.
        """

        exc_t, exc_v, exc_tb = sys.exc_info()

        if exc_t is None:
            raise TypeError('Must be called in except block.')

        retry_on_exc = tuple(
            (x for x in self._retry_on if inspect.isclass(x)))
        retry_on_codes = tuple(
            (x for x in self._retry_on if isinstance(x, int)))

        if issubclass(exc_t, ZendeskError):
            code = exc_v.error_code
            if exc_t not in retry_on_exc and code not in retry_on_codes:
                six.reraise(exc_t, exc_v, exc_tb)
        else:
            if not issubclass(exc_t, retry_on_exc):
                six.reraise(exc_t, exc_v, exc_tb)

        if resp is not None:
            try:
                retry_after = float(resp.headers.get('Retry-After', 0))
                time.sleep(retry_after)
            except (TypeError, ValueError):
                pass

        return True
    

    def _process_single_api_call(self, retry_on, max_retries, path, query, method, data, get_all_pages, complete_response):
        """
        Processes a single API call with retry support.

        Args:
            retry_on (str): The condition on which to retry the API call (e.g., '503').
            max_retries (int): The maximum number of retries to attempt.
            path (str): The endpoint path for the API call.
            query (dict, optional): Query parameters to include in the API request.
            method (str): The HTTP method for the API request (e.g., 'GET', 'POST').
            data (dict, optional): Data to send with the request (for POST/PUT requests).
            get_all_pages (bool, optional): Whether to retrieve data across all pages (default is False).
            complete_response (bool, optional): Whether to return the full response or just the data.
        
        Processes the request, retries if necessary, and handles pagination if `get_all_pages` is True.
        """

        #################################
        # Support for the `retry_on` capability for a single API call
        # Parameters : retry_on=None, max_retries=0, retval=None
        if retry_on and max_retries:
            try:
                _retry_on = self._retry_on
                _max_retries = self._max_retries

                self.retry_on = retry_on
                self.max_retries = max_retries

                # Return the api call response value
                return self.call_zendeskapi(
                                    path=path,
                                    query=query,
                                    method=method,
                                    data=data,
                                    get_all_pages=get_all_pages,
                                    complete_response=complete_response)
            finally:
                self._retry_on = _retry_on
                self._max_retries = _max_retries

            # No data retrieved
            return None



    def _process_multiple_api_calls_with_retry(self, path, query = None, method = 'GET', data = None,
            get_all_pages = False, complete_response = False, retry_on = None, max_retries = 0, retval = None,
            **kwargs):
        
        """
        Makes multiple API calls to Zendesk, supporting retry logic for failures.

        Args:
            path (str): The API endpoint path.
            query (dict, optional): Query parameters to be included in the request.
            method (str, optional): The HTTP method to use (default is 'GET').
            data (dict, optional): Data to send with POST/PUT requests.
            get_all_pages (bool, optional): Whether to fetch all pages of data (default is False).
            complete_response (bool, optional): Whether to return the full API response (default is False).
            retry_on (str, optional): The condition on which to retry (e.g., '503', 'timeout').
            max_retries (int, optional): Maximum number of retries (default is 0).
            retval (any, optional): A variable to store the return value of the request (default is None).
            **kwargs: Any additional parameters for customization.
        
        Handles retries for API calls, particularly when the `retry_on` condition is met.
        """

        #################################
        # Process the requests
        # - perform the retry attempts when needed

        # Perform API call logic with retry and handle all responses

        # Set the target end point
        url = f'{self.zd_url}{path}'

        # Convert the data to json payload
        payload = json.loads(json.dumps(data))

        # Set the header parameter
        headers = {
            "Content-Type": "application/json",
        }

        # Use basic authentication
        auth = HTTPBasicAuth(f'{self.zd_email}/token', self.zd_api_token)

        response = None
        results = []
        all_requests_complete = False
        request_count = 0

        while not all_requests_complete:

            # Manage the retry attempts for the current http request
            request_count += 1
            try:
                response = requests.request(
                    method,
                    url,
                    auth=auth,
                    headers=headers,
                    json=payload
                )
            except requests.RequestException as requests_error:
                if request_count <= self.max_retries:
                    # Set the response to None when exception is encountered
                    # Else, save the previous requests.Response data when doing retries
                    response = None
                    self._handle_retry(response)
                    continue
                else:
                    raise requests_error

            # Manage the possible error codes returned from the api call request
            # and raise the corresponding error codes
            code = response.status_code
            try:
                if not 200 <= code < 300 and code != 422:
                    if code == 401:
                        raise AuthenticationError(response.content, code, response)
                    elif code == 429:
                        raise RateLimitError(response.content, code, response)
                    else:
                        raise ZendeskError(response.content, code, response)
            except ZendeskError as zendesk_error:
                if request_count <= self.max_retries:
                    self._handle_retry(response)
                    continue
                else:
                    raise zendesk_error

            
            # Manage the json data deserialization and perform sanitation processing
            # Zendesk can return: ' ' strings and false non character strings (0, [], (), {})
            if response.content.strip() and 'json' in response.headers['content-type']:
                content = response.json()

                # Manage the next page processing and set the url to the next page when it is returned in the response
                url = content.get('next_page', None)
                
                # The url above already contains the start_time appended with it; handle specific to incremental exports
                kwargs = {}

            elif response.content.strip() and 'text' in response.headers['content-type']:
                try:
                    content = response.json()
                    
                    # Manage the next page processing and set the url to the next page when it is returned in the response
                    url = content.get('next_page', None)
                    
                    # The url above already contains the start_time appended with it; handle specific to incremental exports
                    kwargs = {}
                except ValueError:
                    content = response.content
            else:
                content = response.content
                url = None

            if complete_response:
                results.append({
                    'response': response,
                    'content': content,
                    'status': response.status_code
                })

            else:
                if retval == 'content':
                    results.append(content)
                elif retval == 'code':
                    results.append(response.status_code)
                elif retval == 'location':
                    results.append(response.headers.get('location'))
                elif retval == 'headers':
                    results.append(response.headers)
                else:
                    # Attempt to automatically determine the value of
                    # most interest to return.

                    # Handle all necessary information from Zendesk - for future data use
                    if response.headers.get('location'):
                        # Update the location to use the expected value
                        results.append(response.headers.get('location'))
                    elif content:
                        results.append(content)
                    else:
                        results.append(responses[response.status_code])

            # Manage the incremental get response data and limit it 1000
            #   Condition: response code == 422 returned (this happens when the end_time < 5 minutes recent) OR count < 1000
            #
            # Check for non-incremental export endpoints
            #   Condition for non-incremental load end-points: 100 item/page limit AND return 'next_page = null' for last page
            #   and 10,000 items per page limit for the incremental/ticket_metric_events end-point
            url = None if (url is not None and
                           'incremental' in url and
                           content.get('count') < 1000) else url
            all_requests_complete = not (get_all_pages and url)
            request_count = 0

        return results
        


    def _process_response_data(self, data, get_all_pages, complete_response):
        """
        Processes the response data from the Zendesk API.

        Args:
            data (dict): The data returned by the API.
            get_all_pages (bool): Whether to retrieve data across multiple pages.
            complete_response (bool): Whether to return the entire response or just the data.

        Returns:
            dict: The processed data, including handling for pagination or full response retrieval.
        
        If `get_all_pages` is True, this method will handle the pagination and return all the gathered results.
        """

        #################################
        # Process the data returned from the Zendesk API
        results = data

        if get_all_pages and complete_response:
            # Return the gathered data when all pages and responses are already collected
            return results

        if len(results) == 1:
            # For multiple array data results, just return the first array that contains the actual response
            return results[0]


        # Process the resulting and combine all retrieved data from the next_page requests
        hashable = True
        try:
            if len(set(results)) == 1:
                # For multiple array data results, just return the first array that contains the actual response
                return results[0]
        except TypeError:
            # Manage the results with a dictionary data type
            hashable = False

        if hashable:
            # Return the hashable object (strings, etc)
            return results

        # Manage the different data type that can be returned from the Zendesk
        combined_dict_results = {}
        combined_list_results = []
        for result in results:
            if isinstance(result, list):
                # Handle the response with a list data type 
                combined_list_results.extend(result)
            elif isinstance(result, dict):
                # Handle the response with a dictionary data type 
                for k in result.keys():
                    v = result[k]
                    if isinstance(v, list):
                        try:
                            combined_dict_results[k].extend(v)
                        except KeyError:
                            combined_dict_results[k] = v
                    else:
                        combined_dict_results[k] = v
            else:
                # Return the response of other data type format
                return results

        if combined_list_results and combined_dict_results:
            # Return the combination of data types being returned (mix of list and dict data types)
            return results

        if combined_dict_results:
            return combined_dict_results

        if combined_list_results:
            return combined_list_results

        # Just sending the undefined data types
        return results



    def call_zendeskapi(self, path, query = None, method = 'GET', data = None,
            get_all_pages = False, complete_response = False, retry_on = None, max_retries = 0, retval = None,
            **kwargs):

        """
        Make a REST call to the Zendesk web service.

        Args:
            path (str): The API endpoint path.
            query (dict, optional): The query parameters for the request (default is None).
            method (str, optional): The HTTP method to use ('GET', 'POST', etc.; default is 'GET').
            data (dict, optional): The data for POST/PUT requests (default is None).
            get_all_pages (bool, optional): Whether to handle pagination (default is False).
            complete_response (bool, optional): Whether to return the full response object (default is False).
            retry_on (str, optional): The condition to retry on (default is None).
            max_retries (int, optional): The maximum number of retries (default is 0).
            retval (any, optional): A variable to store the result of the request (default is None).
            **kwargs: Any additional parameters for customization.

        Returns:
            dict or None: The response data, or None if the request fails.

        Makes an API call to Zendesk and handles retries, pagination, and response processing.
        """

        results = []

        # Launch the processing of getting Zendesk response for a single API call
        # Parameters : retry_on=None, max_retries=0, retval=None
        try:
            response = self._process_single_api_call(retry_on, 
                                                    max_retries, 
                                                    path, query, 
                                                    method, 
                                                    data, 
                                                    get_all_pages, 
                                                    complete_response)
        
        except Exception as error:
            raise error
        except:
            raise Exception("Unhandled exception while executing _process_single_api_call()")

        # If data is retrieved, return the value to the caller
        if response is not None:
            return response


        # Else, process the request using the multiple calls to handle the next page
        # (i.e., Zendesk API call with multiple page data return)
        try:
            results = self._process_multiple_api_calls_with_retry(path, 
                                                                  query, 
                                                                  method, 
                                                                  data, 
                                                                  get_all_pages, 
                                                                  complete_response, 
                                                                  retry_on, 
                                                                  max_retries, 
                                                                  retval, 
                                                                  **kwargs)
        except Exception as error:
            raise Exception(error)
        except:
            raise Exception("Unhandled exception while executing _process_multiple_api_calls_with_retry()")

        return self._process_response_data(results, get_all_pages, complete_response)

