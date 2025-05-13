import pytest
from unittest.mock import patch, MagicMock

# Import the functions or classes to be tested
from core import investor_strategy_logic
# from core.firecrawl_api import FirecrawlAPI # If used by strategy logic
# from core.llm_interface import get_llm_response # If used by strategy logic

# Mock st.secrets and st.info/st.warning for testing purposes
@pytest.fixture(autouse=True)
def mock_streamlit_env(monkeypatch):
    mock_secrets_data = {
        "FIRECRAWL_API_KEY": "fake_firecrawl_key_for_testing_strategy",
        "OPENAI_API_KEY": "fake_openai_key_for_testing_strategy",
    }
    # Mock st.secrets
    monkeypatch.setattr("streamlit.secrets", mock_secrets_data)

    # Mock streamlit messaging functions to avoid errors during tests
    monkeypatch.setattr("streamlit.info", MagicMock())
    monkeypatch.setattr("streamlit.warning", MagicMock())
    monkeypatch.setattr("streamlit.error", MagicMock())
    monkeypatch.setattr("streamlit.write", MagicMock()) # If your logic uses st.write

class TestInvestorStrategyLogic:

    @pytest.fixture
    def mock_startup_profile(self):
        return {
            "industry": "TestTech",
            "stage": "Seed",
            "funding_needed": "$500k",
            "usp": "Unique Test Proposition"
        }

    @pytest.fixture
    def mock_firecrawl_client_strategy(self):
        client = MagicMock() # spec=FirecrawlAPI
        client.search.return_value = {
            "data": [{"name": "Searched Investor from Strategy", "url": "http://test.com"}],
            "success": True
        }
        return client

    @patch('core.investor_strategy_logic.st') # Mock streamlit module used within the logic
    def test_develop_strategy_with_llm_mocked(self, mock_st, mock_startup_profile):
        """
        Tests the develop_strategy_with_llm function with mocked LLM responses.
        Since the actual LLM call is commented out in the provided logic,
        this test will focus on the mock data generation part.
        """
        # The actual llm_interface.get_llm_response is not called by the current mock implementation
        # If it were, we'd patch it here:
        # @patch('core.investor_strategy_logic.get_llm_response')
        # def test_develop_strategy_with_llm_mocked(self, mock_get_llm_resp, mock_st, mock_startup_profile):
        #     mock_get_llm_resp.return_value = '{"summary": "LLM summary", "keywords_for_search": ["llm_keyword"], ...}'

        strategy = investor_strategy_logic.develop_strategy_with_llm(
            profile=mock_startup_profile,
            market_trends="Test Trends",
            investor_preferences="Test Preferences",
            llm_provider="openai",
            llm_model="gpt-3.5-turbo"
        )

        assert "summary" in strategy
        assert "keywords_for_search" in strategy
        assert "data_sources_to_check" in strategy
        assert "outreach_angle" in strategy
        assert mock_startup_profile["industry"] in strategy["summary"]
        assert len(strategy["keywords_for_search"]) > 0
        mock_st.info.assert_called() # Check if st.info was called as in the mocked function

    @patch('core.investor_strategy_logic.st') # Mock streamlit module
    def test_execute_investor_search_no_firecrawl_client(self, mock_st, mock_startup_profile):
        """
        Tests execute_investor_search when no Firecrawl client is provided.
        """
        strategy = {
            "keywords_for_search": ["keyword1", "keyword2"],
            # ... other strategy elements
        }
        results = investor_strategy_logic.execute_investor_search(
            strategy=strategy,
            firecrawl_client=None # Explicitly pass None
        )

        assert len(results) > 0
        assert "Mock Investor 1" in results[0]["name"]
        mock_st.warning.assert_called_with("Firecrawl client not provided to execute_investor_search. Mocking results without web search.")

    @patch('core.investor_strategy_logic.st') # Mock streamlit module
    @patch('core.investor_strategy_logic.FirecrawlAPI') # Mock FirecrawlAPI class if it's instantiated inside
    def test_execute_investor_search_with_mock_firecrawl(self, MockFirecrawlAPI, mock_st, mock_startup_profile, mock_firecrawl_client_strategy):
        """
        Tests execute_investor_search with a mocked Firecrawl client.
        This assumes FirecrawlAPI might be instantiated if client is None, or client is passed.
        """
        # If FirecrawlAPI is instantiated inside the function when client is None:
        # MockFirecrawlAPI.return_value = mock_firecrawl_client_strategy
        # For this test, we pass the client directly.

        strategy = {
            "keywords_for_search": ["test keyword search"],
            "data_sources_to_check": ["Firecrawl"],
            # ...
        }
        results = investor_strategy_logic.execute_investor_search(
            strategy=strategy,
            firecrawl_client=mock_firecrawl_client_strategy # Pass the mock client
        )

        assert len(results) > 0
        # Based on the current mock logic in investor_strategy_logic.py:
        # It simulates Firecrawl search if client is present.
        assert "Investor Site for test keyword search" in results[0]["name"]
        mock_firecrawl_client_strategy.search.assert_not_called() # The current mock logic in investor_strategy_logic.py does not call client.search
                                                                # It directly constructs mock_firecrawl_data.
                                                                # This assertion needs to align with actual implementation.
                                                                # If it *were* to call search:
                                                                # mock_firecrawl_client_strategy.search.assert_called_with(query="test keyword search", params={"pageOptions": {"limit": 2}})
        mock_st.write.assert_any_call("Simulating Firecrawl search for: 'test keyword search'")


    @patch('core.investor_strategy_logic.st')
    # @patch('core.investor_strategy_logic.get_llm_response') # If LLM refinement was active
    def test_execute_investor_search_llm_refinement_mocked(self, mock_st, mock_startup_profile):
        # mock_get_llm_resp.return_value = '[{"name": "Refined Investor", ...}]' # Mock LLM response for refinement
        strategy = {"keywords_for_search": ["keyword for refinement"]}
        
        results = investor_strategy_logic.execute_investor_search(
            strategy=strategy,
            firecrawl_client=None, # Mock without firecrawl for simplicity here
            llm_provider="openai", # Activate mock LLM refinement path
            llm_model="gpt-3.5-turbo"
        )
        # The current mock logic for LLM refinement is just a st.write and pass.
        # So we check if st.write was called.
        mock_st.write.assert_any_call("Simulating LLM refinement of 1 results using openai...")
        assert len(results) == 1 # Should still return the mock results before refinement
        assert "Mock Investor 1" in results[0]["name"]


    def test_module_importable(self):
        """ Checks if the module can be imported. """
        assert investor_strategy_logic is not None

# To run: python -m pytest tests/test_investor_strategy_logic.py
