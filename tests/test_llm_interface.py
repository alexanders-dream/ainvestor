import pytest
from unittest.mock import patch, MagicMock, mock_open
import streamlit as st # Streamlit is imported in llm_interface

# Import functions/classes to test
from core.llm_interface import (
    get_llm,
    get_available_models,
    get_llm_response,
    SUPPORTED_PROVIDERS
)

# Mock Streamlit secrets
# This needs to be available before llm_interface is imported by the test runner if st.secrets is accessed at import time.
# However, in our llm_interface, st.secrets is accessed within functions, so patching it per test is fine.

@pytest.fixture(autouse=True)
def mock_st_secrets():
    """Auto-applied fixture to mock st.secrets for all tests in this module."""
    with patch('streamlit.secrets', new_callable=MagicMock) as mock_secrets:
        # Configure mock return values for secrets used in llm_interface
        mock_secrets.get.side_effect = lambda key: {
            "OPENAI_API_KEY": "fake_openai_key",
            "ANTHROPIC_API_KEY": "fake_anthropic_key",
            "OPENROUTER_API_KEY": "fake_openrouter_key",
            "GOOGLE_API_KEY": "fake_google_key",
            "GROQ_API_KEY": "fake_groq_key",
            "OLLAMA_BASE_URL": "http://mock-ollama:11434",
            "requesty_API_KEY": "fake_requesty_key" # For placeholder
        }.get(key)
        yield mock_secrets


# --- Tests for get_llm ---
@patch.dict(SUPPORTED_PROVIDERS) # Ensure we're using a controlled version of this dict
@patch('core.llm_interface.ChatOpenAI')
def test_get_llm_openai_success(MockChatOpenAI, mock_st_secrets):
    mock_instance = MockChatOpenAI.return_value
    llm = get_llm(provider_name="openai", model_name="gpt-4")
    assert llm == mock_instance
    MockChatOpenAI.assert_called_once_with(
        model_name="gpt-4",
        temperature=0.7, # Default temperature
        api_key="fake_openai_key"
    )

@patch.dict(SUPPORTED_PROVIDERS)
@patch('core.llm_interface.ChatAnthropic')
def test_get_llm_anthropic_success(MockChatAnthropic, mock_st_secrets):
    mock_instance = MockChatAnthropic.return_value
    llm = get_llm(provider_name="anthropic", model_name="claude-3-opus", temperature=0.5)
    assert llm == mock_instance
    MockChatAnthropic.assert_called_once_with(
        model_name="claude-3-opus",
        temperature=0.5,
        anthropic_api_key="fake_anthropic_key"
    )

@patch.dict(SUPPORTED_PROVIDERS)
@patch('core.llm_interface.ChatOllama')
def test_get_llm_ollama_success_with_secret_url(MockChatOllama, mock_st_secrets):
    mock_instance = MockChatOllama.return_value
    llm = get_llm(provider_name="ollama", model_name="llama3")
    assert llm == mock_instance
    MockChatOllama.assert_called_once_with(
        model_name="llama3",
        temperature=0.7,
        base_url="http://mock-ollama:11434" # From mocked st.secrets
    )

@patch.dict(SUPPORTED_PROVIDERS)
@patch('core.llm_interface.ChatOllama')
def test_get_llm_ollama_success_default_url(MockChatOllama, mock_st_secrets):
    # Simulate OLLAMA_BASE_URL not being in secrets
    mock_st_secrets.get.side_effect = lambda key: {
        "OPENAI_API_KEY": "fake_key" # other keys
    }.get(key, None) # Return None if OLLAMA_BASE_URL is requested

    mock_instance = MockChatOllama.return_value
    llm = get_llm(provider_name="ollama", model_name="llama2")
    assert llm == mock_instance
    MockChatOllama.assert_called_once_with(
        model_name="llama2",
        temperature=0.7,
        base_url="http://localhost:11434" # Default fallback
    )


def test_get_llm_unsupported_provider(mock_st_secrets):
    with pytest.raises(ValueError, match="Unsupported LLM provider: non_existent_provider"):
        get_llm(provider_name="non_existent_provider")

def test_get_llm_missing_api_key(mock_st_secrets):
    mock_st_secrets.get.side_effect = lambda key: None # Simulate no API keys found
    with pytest.raises(ValueError, match="API key \(OPENAI_API_KEY\) for openai not found"):
        get_llm(provider_name="openai")

@patch('core.llm_interface.ChatOpenAI')
def test_get_llm_initialization_failure(MockChatOpenAI, mock_st_secrets):
    MockChatOpenAI.side_effect = Exception("Initialization failed")
    # Mock st.error to check if it's called
    with patch('streamlit.error') as mock_st_error:
        llm = get_llm(provider_name="openai")
        assert llm is None
        mock_st_error.assert_called_once()
        assert "Failed to initialize LLM" in mock_st_error.call_args[0][0]


# --- Tests for get_available_models ---
# These tests will mock the `requests.get` and specific client library calls

@patch('core.llm_interface.requests.get')
def test_get_available_models_openrouter_success(mock_requests_get, mock_st_secrets):
    mock_response = MagicMock()
    mock_response.json.return_value = {"data": [{"id": "openai/gpt-3.5-turbo"}, {"id": "google/gemini-pro"}]}
    mock_response.raise_for_status.return_value = None # Simulate successful request
    mock_requests_get.return_value = mock_response

    models = get_available_models("openrouter")
    assert "openai/gpt-3.5-turbo" in models
    assert "google/gemini-pro" in models
    mock_requests_get.assert_called_once_with("https://openrouter.ai/api/v1/models")

@patch('core.llm_interface.requests.get')
def test_get_available_models_ollama_connection_error(mock_requests_get, mock_st_secrets):
    mock_requests_get.side_effect = requests.exceptions.ConnectionError("Failed to connect")
    models = get_available_models("ollama")
    assert models == [f"Ollama not reachable at http://mock-ollama:11434"] # From mocked secret

@patch('openai.OpenAI') # Patch the OpenAI client from the openai library
def test_get_available_models_openai_success(MockOpenAIClient, mock_st_secrets):
    mock_client_instance = MockOpenAIClient.return_value
    mock_model1 = MagicMock()
    mock_model1.id = "gpt-3.5-turbo"
    mock_model2 = MagicMock()
    mock_model2.id = "gpt-4"
    mock_client_instance.models.list.return_value.data = [mock_model1, mock_model2]

    models = get_available_models("openai")
    assert "gpt-3.5-turbo" in models
    assert "gpt-4" in models
    MockOpenAIClient.assert_called_once_with(api_key="fake_openai_key")


# --- Tests for get_llm_response ---
@patch('core.llm_interface.get_llm') # Mock our own get_llm function
def test_get_llm_response_success(mock_get_llm_internal, mock_st_secrets):
    mock_llm_instance = MagicMock()
    # Simulate Langchain >0.1.0 .invoke() and AIMessage style response
    mock_ai_message = MagicMock()
    mock_ai_message.content = "Test response content"
    mock_llm_instance.invoke.return_value = mock_ai_message # LLM part of chain returns AIMessage
    
    # Mock the chain: prompt | llm. The llm part is what we mock above.
    # The chain itself will be constructed with this mocked llm.
    # So, (prompt | mock_llm_instance).invoke should be called.
    
    mock_get_llm_internal.return_value = mock_llm_instance # get_llm returns the mocked LLM

    prompt_str = "Hello {name}"
    input_vars = {"name": "World"}
    
    response = get_llm_response(
        prompt_template_str=prompt_str,
        input_variables=input_vars,
        llm_provider="openai", # Provider doesn't matter much here as get_llm is mocked
        llm_model="gpt-test"
    )

    assert response == "Test response content"
    mock_get_llm_internal.assert_called_once()
    # Check that the invoke method on the llm_instance (which is part of the chain) was called
    # The actual call is chain.invoke(input_vars), where chain = prompt | llm_instance
    # We need to check if llm_instance.invoke was called with the input_vars after being piped from prompt.
    # This is tricky to assert directly on mock_llm_instance.invoke without more complex chain mocking.
    # For now, we trust that if get_llm is called and returns a mock that has an invoke method,
    # and that invoke method is called and returns our expected AIMessage, the chain worked.
    # A more robust test would involve checking the arguments to `chain.invoke`.
    # For Langchain's LCEL, the `prompt` object's `invoke` would be called first, then the `llm`'s `invoke`.
    # So, `mock_llm_instance.invoke` should be called with the output of `prompt.invoke(input_vars)`.
    
    # A simpler check: ensure the mocked LLM's invoke was called.
    mock_llm_instance.invoke.assert_called_once() 
    # We can inspect call_args if needed: print(mock_llm_instance.invoke.call_args)


@patch('core.llm_interface.get_llm', return_value=None) # Simulate get_llm failing
def test_get_llm_response_llm_init_fails(mock_get_llm_internal_fail, mock_st_secrets):
    response = get_llm_response("Hi", {}, "openai")
    assert "LLM initialization failed" in response

@patch('core.llm_interface.get_llm')
def test_get_llm_response_chain_execution_error(mock_get_llm_chain_fail, mock_st_secrets):
    mock_llm_instance = MagicMock()
    mock_llm_instance.invoke.side_effect = Exception("Chain execution error")
    mock_get_llm_chain_fail.return_value = mock_llm_instance

    with patch('streamlit.error') as mock_st_error:
        response = get_llm_response("Hi {var}", {"var":"test"}, "openai", llm_model="text-davinci-003") # model name for error msg
        assert "Error processing request: Chain execution error" in response
        mock_st_error.assert_called_once()
        assert "Error during LLM chain execution" in mock_st_error.call_args[0][0]

# Add more tests for different providers, edge cases, specific model behaviors if necessary.
