import streamlit as st
import requests
import json
import yaml
import time

class FirecrawlAPI:
    """
    A wrapper for the Firecrawl API to scrape websites and search for information.
    """
    DEFAULT_BASE_URL = "https://api.firecrawl.dev"

    def __init__(self, api_key: str = None, base_url: str = None):
        """
        Initializes the FirecrawlAPI client.

        Args:
            api_key (str, optional): The Firecrawl API key.
                                     If None, tries to fetch from st.secrets["FIRECRAWL_API_KEY"].
            base_url (str, optional): The base URL for the Firecrawl API.
                                      Defaults to "https://api.firecrawl.dev".
        """
        if api_key is None:
            try:
                self.api_key = st.secrets["FIRECRAWL_API_KEY"]
            except (AttributeError, KeyError): # Handle cases where st.secrets is not available or key is missing
                raise ValueError("Firecrawl API key not provided and not found in st.secrets['FIRECRAWL_API_KEY']")
        else:
            self.api_key = api_key

        self.base_url = base_url or self.DEFAULT_BASE_URL
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _request(self, method: str, endpoint: str, payload: dict = None, params: dict = None, max_retries: int = 2, timeout: int = 60):
        """
        Makes a request to the Firecrawl API with retry logic.

        Args:
            method (str): HTTP method (e.g., "GET", "POST").
            endpoint (str): API endpoint (e.g., "/v0/scrape").
            payload (dict, optional): JSON payload for POST requests.
            params (dict, optional): URL parameters for GET requests.
            max_retries (int, optional): Maximum number of retry attempts for transient errors.
            timeout (int, optional): Timeout in seconds for the request. Default is 60 seconds.

        Returns:
            dict: The JSON response from the API.

        Raises:
            requests.exceptions.HTTPError: If the API returns an error status code.
            requests.exceptions.RequestException: For other network or request-related issues.
        """
        url = f"{self.base_url}{endpoint}"
        response = None
        retry_count = 0

        # Debug logging
        st.write(f"Debug: Making {method} request to {endpoint}")

        while retry_count <= max_retries:
            try:
                if method.upper() == "POST":
                    response = requests.post(url, headers=self.headers, json=payload, params=params, timeout=timeout)
                elif method.upper() == "GET":
                    response = requests.get(url, headers=self.headers, params=params, timeout=timeout)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Check for server errors (5xx) which might be transient
                if 500 <= response.status_code < 600 and retry_count < max_retries:
                    retry_count += 1
                    st.warning(f"Server error ({response.status_code}) from Firecrawl API. Retrying ({retry_count}/{max_retries})...")
                    time.sleep(2 * retry_count)  # Exponential backoff
                    continue

                response.raise_for_status()  # Raises HTTPError for bad responses (4XX or 5XX)
                return response.json()

            except requests.exceptions.HTTPError as http_err:
                # Log or handle specific HTTP errors
                error_msg = f"HTTP error occurred: {http_err}"
                if response:
                    error_msg += f" - {response.text}"
                st.error(error_msg)

                # Check for specific error codes
                if response and response.status_code == 401:
                    st.error("Authentication error: Please check your Firecrawl API key")
                elif response and response.status_code == 403:
                    st.error("Authorization error: Your API key may not have permission to access this resource")
                elif response and response.status_code == 429:
                    st.error("Rate limit exceeded: Too many requests to the Firecrawl API")
                elif response and response.status_code >= 500:
                    st.error("Firecrawl server error: The service might be experiencing issues")

                # Return a structured error response instead of raising
                return {
                    "success": False,
                    "error": str(http_err),
                    "data": None,
                    "status_code": response.status_code if response else None,
                    "message": "Firecrawl API request failed. Check your API key and connection."
                }

            except requests.exceptions.Timeout:
                if retry_count < max_retries:
                    retry_count += 1
                    st.warning(f"Timeout error from Firecrawl API. Retrying ({retry_count}/{max_retries})...")
                    time.sleep(2 * retry_count)  # Exponential backoff
                    continue
                st.error(f"Timeout error from Firecrawl API after {max_retries} retries.")
                return {"success": False, "error": "Request timed out", "data": None}

            except requests.exceptions.RequestException as req_err:
                # Log or handle other request exceptions (network issues, etc.)
                st.error(f"Request error occurred: {req_err}")
                return {"success": False, "error": str(req_err), "data": None}

            except json.JSONDecodeError as json_err:
                # Try to parse as YAML if JSON parsing fails
                try:
                    if response and response.text:
                        yaml_data = yaml.safe_load(response.text)
                        return yaml_data
                except yaml.YAMLError as yaml_err:
                    st.error(f"YAML decode error after JSON decode error: {yaml_err} - Response: {response.text if response else 'No response'}")

                # If both JSON and YAML parsing fail, return error
                st.error(f"JSON/YAML decode error: {json_err} - Response: {response.text if response else 'No response'}")
                return {
                    "success": False,
                    "error": f"Invalid JSON/YAML response: {str(json_err)}",
                    "data": None,
                    "raw_response": response.text if response else None
                }

    def scrape_url(self, url: str, params: dict = None):
        """
        Scrapes a single URL.

        Args:
            url (str): The URL to scrape.
            params (dict, optional): Additional parameters for the scrape API.
                                     Refer to Firecrawl documentation for options.
                                     Example: {'pageOptions': {'onlyMainContent': True}}

        Returns:
            dict: The scrape result.
        """
        payload = {"url": url}
        if params:
            payload.update(params)

        # Debug logging
        st.write(f"Debug: Scraping URL: '{url}'")

        result = self._request("POST", "/v0/scrape", payload=payload)

        # Debug logging for result
        if result and isinstance(result, dict):
            if result.get("success") is False:
                st.error(f"Firecrawl scrape failed: {result.get('error', 'Unknown error')}")
            elif "content" in result:
                content_length = len(result.get("content", ""))
                st.write(f"Debug: Firecrawl scrape returned {content_length} characters of content")
            else:
                st.write(f"Debug: Firecrawl scrape returned unexpected structure: {list(result.keys())}")

        return result

    def search(self, query: str, params: dict = None):
        """
        Performs a search using Firecrawl's search capabilities.

        Args:
            query (str): The search query.
            params (dict, optional): Additional parameters for the search API.
                                     Refer to Firecrawl documentation for options.
                                     Example: {'pageOptions': {'limit': 5}}

        Returns:
            dict: The search results.
        """
        payload = {"query": query}
        if params:
            payload.update(params)

        # Debug logging
        st.write(f"Debug: Searching Firecrawl for: '{query}'")

        # Assuming search endpoint is /v0/search, adjust if different
        result = self._request("POST", "/v0/search", payload=payload)

        # Debug logging for result
        if result and isinstance(result, dict):
            if result.get("success") is False:
                st.error(f"Firecrawl search failed: {result.get('error', 'Unknown error')}")
            elif "data" in result and result.get("success") is True:
                data = result.get("data", [])
                if isinstance(data, list):
                    st.write(f"Debug: Firecrawl search returned {len(data)} results (new format)")
                else:
                    st.write(f"Debug: Firecrawl search returned data of type {type(data)}")
            elif "results" in result:
                st.write(f"Debug: Firecrawl search returned {len(result['results'])} results (original format)")
            else:
                st.write(f"Debug: Firecrawl search returned unexpected structure: {list(result.keys())}")

            # Add debug info about the first result if available
            if "data" in result and isinstance(result["data"], list) and len(result["data"]) > 0:
                first_item = result["data"][0]
                st.write(f"Debug: First result keys: {list(first_item.keys()) if isinstance(first_item, dict) else type(first_item)}")
            elif "results" in result and len(result["results"]) > 0:
                first_item = result["results"][0]
                st.write(f"Debug: First result keys: {list(first_item.keys()) if isinstance(first_item, dict) else type(first_item)}")

        return result

    def crawl_url(self, url: str, params: dict = None, wait_for_completion: bool = True):
        """
        Initiates a crawl job for a URL.

        Args:
            url (str): The URL to crawl.
            params (dict, optional): Additional parameters for the crawl API.
                                     Refer to Firecrawl documentation for options.
                                     Example: {'crawlerOptions': {'includes': ['blog/*']}}
            wait_for_completion (bool): If true, waits for job completion status. (Simplified, actual implementation might need polling)


        Returns:
            dict: The crawl job initiation response or status.
        """
        payload = {"url": url}
        if params:
            payload.update(params)

        response = self._request("POST", "/v0/crawl", payload=payload)
        job_id = response.get("jobId")

        if job_id and wait_for_completion:
            # This is a simplified wait. Real-world usage might need polling get_crawl_status.
            # For now, just returns the initial response.
            # Consider implementing polling or webhook handling for long-running crawls.
            st.info(f"Crawl job started with ID: {job_id}. Polling for status is not yet implemented in this wrapper.")
        return response

    def get_crawl_status(self, job_id: str):
        """
        Checks the status of a crawl job.

        Args:
            job_id (str): The ID of the crawl job.

        Returns:
            dict: The crawl job status.
        """
        return self._request("GET", f"/v0/crawl/{job_id}/status")

if __name__ == '__main__':
    # This is for basic testing and example usage.
    # Ensure FIRECRAWL_API_KEY is in your .streamlit/secrets.toml for this to run.
    # Or, pass it directly: FirecrawlAPI(api_key="your_key_here")

    st.set_page_config(page_title="Firecrawl API Test")
    st.title("Firecrawl API Test Interface")

    if 'firecrawl_api_key' not in st.session_state:
        st.session_state.firecrawl_api_key = ""
    if 'firecrawl_client' not in st.session_state:
        st.session_state.firecrawl_client = None

    api_key_input = st.text_input("Enter Firecrawl API Key (or set in secrets.toml)", value=st.session_state.firecrawl_api_key, type="password")

    if st.button("Initialize Client"):
        if api_key_input:
            st.session_state.firecrawl_api_key = api_key_input
            try:
                st.session_state.firecrawl_client = FirecrawlAPI(api_key=st.session_state.firecrawl_api_key)
                st.success("Firecrawl client initialized successfully!")
            except ValueError as e:
                st.error(str(e))
            except Exception as e:
                st.error(f"An unexpected error occurred during initialization: {e}")
        else:
            st.warning("Please enter an API key to initialize the client.")


    if st.session_state.get('firecrawl_client'):
        client = st.session_state.firecrawl_client
        st.subheader("Scrape URL")
        scrape_url_input = st.text_input("URL to scrape", "https://example.com")
        if st.button("Scrape"):
            if scrape_url_input:
                with st.spinner("Scraping URL..."):
                    try:
                        result = client.scrape_url(scrape_url_input, params={'pageOptions': {'onlyMainContent': False}})
                        st.json(result)
                    except Exception as e:
                        st.error(f"Scrape failed: {e}")
            else:
                st.warning("Please enter a URL to scrape.")

        st.subheader("Search (Illustrative - check Firecrawl docs for actual search functionality)")
        search_query_input = st.text_input("Search query", "latest AI startups")
        if st.button("Search"):
            if search_query_input:
                with st.spinner("Searching..."):
                    try:
                        # Note: The '/v0/search' endpoint and its parameters are illustrative.
                        # Verify the correct endpoint and payload structure from Firecrawl documentation.
                        result = client.search(search_query_input, params={'searchOptions': {'limit': 3}})
                        st.json(result)
                    except Exception as e:
                        st.error(f"Search failed: {e}")
            else:
                st.warning("Please enter a search query.")

        st.subheader("Crawl URL (Job Submission)")
        crawl_url_input = st.text_input("URL to crawl", "https://blog.google/")
        if st.button("Start Crawl"):
            if crawl_url_input:
                with st.spinner("Submitting crawl job..."):
                    try:
                        result = client.crawl_url(crawl_url_input, params={'crawlerOptions': {'includes': ['/*'], 'limit': 5}}, wait_for_completion=False)
                        st.json(result)
                        if result and result.get("jobId"):
                            st.session_state.last_job_id = result.get("jobId")
                            st.info(f"Job ID: {st.session_state.last_job_id}")
                    except Exception as e:
                        st.error(f"Crawl submission failed: {e}")
            else:
                st.warning("Please enter a URL to crawl.")

        if 'last_job_id' in st.session_state and st.session_state.last_job_id:
            st.subheader("Check Crawl Status")
            job_id_input = st.text_input("Job ID", value=st.session_state.last_job_id)
            if st.button("Get Status"):
                if job_id_input:
                    with st.spinner("Fetching crawl status..."):
                        try:
                            status = client.get_crawl_status(job_id_input)
                            st.json(status)
                        except Exception as e:
                            st.error(f"Failed to get crawl status: {e}")
                else:
                    st.warning("Please enter a Job ID.")
    else:
        st.info("Initialize the client with an API key to use the test interface.")
