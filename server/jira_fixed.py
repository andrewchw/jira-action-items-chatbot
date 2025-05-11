def _make_request(self, method: str, endpoint: str, params: Dict = None, data: Dict = None,
                 use_cache: bool = True, cache_ttl: int = None) -> Dict:
    """
    Make a request to the Jira API.
    
    Args:
        method: HTTP method
        endpoint: API endpoint
        params: Query parameters
        data: Request body data
        use_cache: Whether to use cache
        cache_ttl: Cache TTL in minutes
        
    Returns:
        Response data
    """
    # Generate cache key if using cache
    cache_key = None
    if use_cache and method.upper() == "GET":
        cache_key = self._generate_cache_key(method, endpoint, params, data)
        
        # Check cache
        cached_data = self._check_jira_cache(cache_key, cache_ttl or 15)
        if cached_data:
            logger.debug(f"Using cached response for {method} {endpoint}")
            return cached_data
    
    # Construct URL
    url = f"{self.base_url}{endpoint}"
    
    # Prepare request
    auth = self.get_auth()
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    
    # Log auth type
    if isinstance(auth, tuple):
        logger.debug(f"Using Basic authentication for Jira API request with username: {auth[0]}")
    else:
        logger.debug("Using OAuth authentication for Jira API request")
    
    # Log request details for debugging
    if data:
        logger.debug(f"Request data: {json.dumps(data)} ")
    
    logger.info(f"Making Jira API request: {method} {url}")
    
    # Make request
    try:
        if method.upper() == "GET":
            response = requests.get(url, auth=auth, headers=headers, params=params, timeout=30)
        elif method.upper() == "POST":
            response = requests.post(url, auth=auth, headers=headers, params=params, json=data, timeout=30)
        elif method.upper() == "PUT":
            response = requests.put(url, auth=auth, headers=headers, params=params, json=data, timeout=30)
        elif method.upper() == "DELETE":
            response = requests.delete(url, auth=auth, headers=headers, params=params, timeout=30)
        else:
            raise ValueError(f"Unsupported HTTP method: {method}")
        
        # Log response status
        logger.debug(f"Jira API response status: {response.status_code}")
        logger.debug(f"Jira API response headers: {response.headers}")
        
        # Check for errors
        if response.status_code >= 400:
            try:
                error_data = response.json()
                
                # Handle both errorMessages array and errors object
                if "errorMessages" in error_data and error_data["errorMessages"]:
                    error_message = error_data["errorMessages"][0]
                elif "errors" in error_data and error_data["errors"]:
                    # For structured error objects, format them
                    error_parts = []
                    for field, msg in error_data["errors"].items():
                        error_parts.append(f"{field}: {msg}")
                    error_message = ", ".join(error_parts)
                else:
                    error_message = f"HTTP error {response.status_code}"
                    
                logger.error(f"Jira API error: {response.status_code} - {json.dumps(error_data)}")
                raise ValueError(error_message)
            except ValueError as ve:
                # Re-raise the formatted error
                raise ve
            except Exception as e:
                # Handle JSON parsing errors
                logger.error(f"Error parsing Jira API error response: {str(e)}")
                raise ValueError(f"HTTP error {response.status_code}: {response.text}")
        
        # Parse response
        if response.content:
            response_data = response.json()
            
            # Cache response if appropriate
            if cache_key and method.upper() == "GET":
                self._save_to_jira_cache(cache_key, response_data)
            
            return response_data
        else:
            return {"success": True}
        
    except ValueError as e:
        # Re-raise value errors (validation errors)
        raise
    except Exception as e:
        # Handle other errors
        logger.error(f"Error making Jira API request: {str(e)}")
        raise ValueError(f"Unexpected error: {str(e)}") 