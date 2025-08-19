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




######### CustomApiLibBase Error Objects

class CustomApiLibBaseError(Exception):
    """
    A custom exception class to represent errors encountered when interacting with the Platform API.

    This class extends the base `Exception` class and is used to capture error information related to 
    failed API requests, including the error message, error code, and response from Platform.

    Attributes:
        class_name (str): The name of the class, which is 'CustomApiLibBaseError' for this class.
        message (str): The error message associated with the exception.
        error_code (int): The HTTP status code or error code returned by Platform in the response.
        response (str): The full response from the CustomApiLibBase API that triggered the error.

    Args:
        message (str): A description or message detailing the error.
        code (int): The error code or HTTP status code returned by Platform.
        response (str): The full response body or details returned by the Platform API.

    Methods:
        __str__(): Returns a string representation of the error, including class name, error code, 
                   message, and response details.

    Example:
        raise CustomApiLibBaseError("Invalid ticket ID", 404, "Ticket not found")
        # This would raise a CustomApiLibBaseError with the provided message, code, and response.

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


class AuthenticationError(CustomApiLibBaseError):
    """
    A specific exception class to represent authentication errors when interacting with the Platform API.

    This class extends the `CustomApiLibBaseError` class and is raised when the API returns an authentication-related error,
    such as invalid credentials or missing API key.

    Inherits from:
        CustomApiLibBaseError: The base class that captures the general structure and behavior of Platform-related errors.

    Example:
        raise AuthenticationError("Invalid API key", 401, "Unauthorized access")
        # This would raise an AuthenticationError with a message indicating an authentication failure.

    Notes:
        - This class can be caught separately to handle authentication issues specifically, 
          distinct from other Intercom API errors.
    """
    pass


class RateLimitError(CustomApiLibBaseError):
    """
    A specific exception class to represent rate-limiting errors encountered when interacting with the Platform API.

    This class extends the `CustomApiLibBaseError` class and is raised when the API returns an error indicating that 
    the rate limit has been exceeded, and further requests should be delayed.

    Inherits from:
        CustomApiLibBaseError: The base class that captures the general structure and behavior of Platform-related errors.

    Example:
        raise RateLimitError("Rate limit exceeded", 429, "Too many requests")
        # This would raise a RateLimitError with a message indicating the rate limit has been hit.

    Notes:
        - This class can be caught separately to handle rate-limiting issues specifically, 
          and apply backoff strategies to retry the request after the rate limit is reset.
    """
    pass






######### CustomApiLibBase Objects

class CustomApiLibBase(object):
    """
    Base class for CustomApiLibBase API calls.

    This class serves as a base interface for interacting with the Platform API. It contains methods to make API 
    requests to the CustomApiLibBase service, with support for common features like pagination, retries, and response customization.

    Notes:
        - This class is intended to be subclassed or extended in specific use cases for actual API calls.
        - The methods in this class do not directly interact with Platform but serve as a framework for API interactions.
    """

    def __init__(self):

        """
        Constructor method for the Platform class.

        This method initializes the class, but currently, it doesn't perform any specific initialization logic.

        Notes:
            - This method can be extended in subclasses to set up any specific configurations, 
              such as API credentials or custom settings.
        """

        pass


    def _handle_retry(self, resp):
        """
        Handles any exceptions during an API request or parsing its response status code.

        Args:
            resp (requests.Response): The response object returned from the Platform API.

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

        if issubclass(exc_t, CustomApiLibBaseError):
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
                return self.call_platformapi(
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
        Makes multiple API calls to Platform, supporting retry logic for failures.

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
        url = f'{self.ic_url}{path}'

        # Convert the data to json payload
        payload = json.loads(json.dumps(data))

        # Set the header parameter
        headers = {
            "Content-Type": "application/json",
        }

        # Use header bearer authentication
        #auth = HTTPBasicAuth(f'{self.ic_email}/token', self.ic_api_token)


        # Set the header parameter
        headers = {
            "Content-Type": "application/json",
        }

        # Use header bearer authentication
        headers = {
            "Authorization": f"Bearer {self.ic_api_token}"
        }

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
                    #auth=auth,
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
                        raise CustomApiLibBaseError(response.content, code, response)
            except CustomApiLibBaseError as intercom_error:
                if request_count <= self.max_retries:
                    self._handle_retry(response)
                    continue
                else:
                    raise intercom_error

            
            # Manage the json data deserialization and perform sanitation processing
            # Platform can return: ' ' strings and false non character strings (0, [], (), {})
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

                    # Handle all necessary information from Platform - for future data use
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
        Processes the response data from the Platform API.

        Args:
            data (dict): The data returned by the API.
            get_all_pages (bool): Whether to retrieve data across multiple pages.
            complete_response (bool): Whether to return the entire response or just the data.

        Returns:
            dict: The processed data, including handling for pagination or full response retrieval.
        
        If `get_all_pages` is True, this method will handle the pagination and return all the gathered results.
        """

        #################################
        # Process the data returned from the Platform API
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

        # Manage the different data type that can be returned from the Platform
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




    def call_platformapi(self, path, query = None, method = 'GET', data = None,
            get_all_pages = False, complete_response = False, retry_on = None, max_retries = 0, retval = None,
            **kwargs):

        """
        Make a REST call to the Platform web service.

        Args:
            path (str): The Platform API endpoint path.
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

        Makes an API call to Platform and handles retries, pagination, and response processing.
        """

        results = []

        # Launch the processing of getting Platform response for a single API call
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
        # (i.e., Platform API call with multiple page data return)
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









