import pytest
from unittest.mock import patch, MagicMock
import requests # For requests.exceptions

# Import the class to be tested
from core.firecrawl_api import FirecrawlAPI

# Mock st.secrets for testing purposes
@pytest.fixture(autouse=True)
def mock_streamlit_env_fc(monkeypatch):
    mock_secrets_data = {
        "FIRECRAWL_API_KEY": "test_api_key_from_secrets",
    }
    monkeypatch.setattr("streamlit.secrets", mock_secrets_data)
    # Mock streamlit messaging functions to avoid errors if called by API wrapper
    monkeypatch.setattr("streamlit.error", MagicMock())


class TestFirecrawlAPI:

    @pytest.fixture
    def api_key(self):
        return "test_api_key_direct"

    @pytest.fixture
    def base_url(self):
        return "https://test.firecrawl.dev"

    @pytest.fixture
    def firecrawl_client_direct_key(self, api_key, base_url):
        """Client initialized with a direct API key."""
        return FirecrawlAPI(api_key=api_key, base_url=base_url)

    @pytest.fixture
    def firecrawl_client_secrets_key(self, base_url):
        """Client initialized relying on st.secrets for API key."""
        return FirecrawlAPI(base_url=base_url) # API key from mock_streamlit_env_fc

    def test_init_with_direct_api_key(self, api_key, base_url):
        client = FirecrawlAPI(api_key=api_key, base_url=base_url)
        assert client.api_key == api_key
        assert client.base_url == base_url
        assert client.headers["Authorization"] == f"Bearer {api_key}"

    def test_init_with_secrets_api_key(self, base_url):
        client = FirecrawlAPI(base_url=base_url) # Relies on mocked st.secrets
        assert client.api_key == "test_api_key_from_secrets"
        assert client.base_url == base_url
        assert client.headers["Authorization"] == "Bearer test_api_key_from_secrets"

    def test_init_no_api_key_raises_error(self, monkeypatch, base_url):
        # Ensure st.secrets does not have the key for this specific test
        monkeypatch.setattr("streamlit.secrets", {})
        with pytest.raises(ValueError, match="Firecrawl API key not provided and not found"):
            FirecrawlAPI(base_url=base_url) # No direct key, and secrets won't provide it

    @patch('core.firecrawl_api.requests.post')
    def test_scrape_url_success(self, mock_post, firecrawl_client_direct_key):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": "scraped_content", "success": True}
        mock_post.return_value = mock_response

        scrape_params = {'pageOptions': {'onlyMainContent': True}}
        result = firecrawl_client_direct_key.scrape_url("http://example.com", params=scrape_params)

        expected_payload = {"url": "http://example.com"}
        expected_payload.update(scrape_params)

        mock_post.assert_called_once_with(
            f"{firecrawl_client_direct_key.base_url}/v0/scrape",
            headers=firecrawl_client_direct_key.headers,
            json=expected_payload
        )
        assert result == {"data": "scraped_content", "success": True}

    @patch('core.firecrawl_api.requests.post')
    def test_search_success(self, mock_post, firecrawl_client_direct_key):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": [{"id": "1", "name": "Result 1"}], "success": True}
        mock_post.return_value = mock_response

        search_params = {'searchOptions': {'limit': 5}}
        result = firecrawl_client_direct_key.search("test query", params=search_params)
        
        expected_payload = {"query": "test query"}
        expected_payload.update(search_params)

        mock_post.assert_called_once_with(
            f"{firecrawl_client_direct_key.base_url}/v0/search",
            headers=firecrawl_client_direct_key.headers,
            json=expected_payload
        )
        assert result == {"data": [{"id": "1", "name": "Result 1"}], "success": True}

    @patch('core.firecrawl_api.requests.post')
    def test_crawl_url_success(self, mock_post, firecrawl_client_direct_key):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"jobId": "job123", "status": "pending"}
        mock_post.return_value = mock_response

        crawl_params = {'crawlerOptions': {'includes': ['blog/*']}}
        result = firecrawl_client_direct_key.crawl_url("http://blog.example.com", params=crawl_params, wait_for_completion=False)

        expected_payload = {"url": "http://blog.example.com"}
        expected_payload.update(crawl_params)
        
        mock_post.assert_called_once_with(
            f"{firecrawl_client_direct_key.base_url}/v0/crawl",
            headers=firecrawl_client_direct_key.headers,
            json=expected_payload
        )
        assert result == {"jobId": "job123", "status": "pending"}

    @patch('core.firecrawl_api.requests.get')
    def test_get_crawl_status_success(self, mock_get, firecrawl_client_direct_key):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"jobId": "job123", "status": "completed", "data": "crawled_data"}
        mock_get.return_value = mock_response

        result = firecrawl_client_direct_key.get_crawl_status("job123")

        mock_get.assert_called_once_with(
            f"{firecrawl_client_direct_key.base_url}/v0/crawl/job123/status",
            headers=firecrawl_client_direct_key.headers,
            params=None
        )
        assert result == {"jobId": "job123", "status": "completed", "data": "crawled_data"}

    @patch('core.firecrawl_api.requests.post')
    def test_request_http_error(self, mock_post, firecrawl_client_direct_key):
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "Bad Request"
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("HTTP Error")
        mock_post.return_value = mock_response

        with pytest.raises(requests.exceptions.HTTPError):
            firecrawl_client_direct_key.scrape_url("http://example.com")
        
        # Check if st.error was called (it's mocked in mock_streamlit_env_fc)
        firecrawl_client_direct_key.st.error.assert_called_once()


    @patch('core.firecrawl_api.requests.post')
    def test_request_connection_error(self, mock_post, firecrawl_client_direct_key):
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection Failed")

        with pytest.raises(requests.exceptions.ConnectionError):
            firecrawl_client_direct_key.scrape_url("http://example.com")
        firecrawl_client_direct_key.st.error.assert_called_once()


    @patch('core.firecrawl_api.requests.post')
    def test_request_json_decode_error(self, mock_post, firecrawl_client_direct_key):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = "Not a valid JSON"
        mock_response.json.side_effect = requests.exceptions.JSONDecodeError("JSON Error", "doc", 0)
        # Some versions of requests might use json.JSONDecodeError directly
        # from json import JSONDecodeError
        # mock_response.json.side_effect = JSONDecodeError("JSON Error", "doc", 0)
        mock_post.return_value = mock_response
        
        with pytest.raises(requests.exceptions.JSONDecodeError):
            firecrawl_client_direct_key.scrape_url("http://example.com")
        firecrawl_client_direct_key.st.error.assert_called_once()

# To run: python -m pytest tests/test_firecrawl_api.py
