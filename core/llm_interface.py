# core/llm_interface.py
import streamlit as st
import requests # For fetching models from some APIs if Langchain doesn't support it directly
import json # For JSON handling
import yaml # For YAML handling
from typing import Optional # Added for Optional type hint
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_community.chat_models import ChatOllama # Or from langchain.chat_models
# For OpenRouter, it might use ChatOpenAI with a custom base URL or a dedicated class if available
# from langchain_community.chat_models import ChatOpenRouter
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import LLMChain
from .yaml_utils import load_yaml, dump_yaml, extract_yaml_from_text, create_default_investor_yaml

# core/llm_interface.py (continued)
SUPPORTED_PROVIDERS = {
    "openai": {
        "class": ChatOpenAI, "api_key_secret": "OPENAI_API_KEY",
        "default_model": "gpt-3.5-turbo", "api_key_param": "api_key"
    },
    "anthropic": {
        "class": ChatAnthropic, "api_key_secret": "ANTHROPIC_API_KEY",
        "default_model": "claude-3-haiku-20240307", "api_key_param": "anthropic_api_key" # Check exact param name
    },
    "openrouter": { # Uses OpenAI-compatible API structure
        "class": ChatOpenAI, "api_key_secret": "OPENROUTER_API_KEY",
        "default_model": "openai/gpt-3.5-turbo", # Example, specific model strings from OpenRouter
        "base_url": "https://openrouter.ai/api/v1", "api_key_param": "api_key"
    },
    "google": { # For Gemini models
        "class": ChatGoogleGenerativeAI, "api_key_secret": "GOOGLE_API_KEY",
        "default_model": "gemini-pro", "api_key_param": "google_api_key"
    },
    "groq": {
        "class": ChatGroq, "api_key_secret": "GROQ_API_KEY",
        "default_model": "mixtral-8x7b-32768", "api_key_param": "groq_api_key" # Check exact param name
    },
    "ollama": { # Typically local, may not need API key unless served remotely
        "class": ChatOllama, "api_key_secret": None, # Or specific key if remote Ollama is secured
        "default_model": "llama2",
        "base_url_env_var": "OLLAMA_ENDPOINT", # e.g. http://localhost:11434
        "notes": "Requires OLLAMA_ENDPOINT in secrets or config if not default localhost."
    },
    "requesty": { # Placeholder - details TBD based on requesty's API and Langchain support
        "class": None, "api_key_secret": "requesty_API_KEY",
        "default_model": "requesty-default", "api_key_param": "api_key",
        "notes": "Langchain integration for requesty needs to be defined."
    }
    # Add more providers as needed
}

def get_llm(provider_name: str, model_name: str = None, **kwargs):
    """
    Initializes and returns a Langchain LLM/ChatModel instance.
    API keys and base URLs (if applicable) are fetched from st.secrets or environment.
    """
    provider_key = provider_name.lower()
    provider_config = SUPPORTED_PROVIDERS.get(provider_key)
    if not provider_config or not provider_config.get("class"):
        raise ValueError(f"Unsupported or not yet configured LLM provider: {provider_name}")

    # Prioritize API key and base_url from kwargs (passed from session state if user set them)
    # Then try secrets, then config defaults.
    api_key = kwargs.pop("api_key", None) 
    base_url = kwargs.pop("base_url", None)

    if not api_key and provider_config.get("api_key_secret"):
        api_key_secret_name = provider_config["api_key_secret"]
        if api_key_secret_name:
            api_key = st.secrets.get(api_key_secret_name)
            # Only raise error if key is strictly required by provider config and still not found
            if not api_key and provider_key != "ollama": # Ollama might not need a key
                 raise ValueError(
                    f"API key ({api_key_secret_name}) for {provider_name} not found in st.secrets or provided manually. "
                    "Ensure it is set in .streamlit/secrets.toml or in the UI."
                )
    
    if not base_url: # If not passed via kwargs
        if provider_config.get("base_url"): # Check hardcoded base_url in SUPPORTED_PROVIDERS
            base_url = provider_config["base_url"]
        elif provider_config.get("base_url_env_var"): # Check secrets for base_url
            base_url_from_secrets = st.secrets.get(provider_config["base_url_env_var"])
            if base_url_from_secrets:
                base_url = base_url_from_secrets
        # For Ollama, Langchain's ChatOllama might default to http://localhost:11434 if base_url not provided

    model_to_use = model_name or provider_config["default_model"]
    llm_class = provider_config["class"]

    model_param_key = "model_name" # Default for OpenAI, Groq
    if provider_key in ["google", "anthropic", "ollama"]:
        model_param_key = "model"

    init_args = {model_param_key: model_to_use, **kwargs} # Pass remaining kwargs

    if api_key and provider_config.get("api_key_param"):
        init_args[provider_config["api_key_param"]] = api_key
    elif api_key: # Default to 'api_key' if not specified (might be wrong for some, but ChatOpenAI uses it)
        init_args["api_key"] = api_key
    
    if base_url: # If a base_url was determined
        # For ChatOpenAI (used by OpenAI and OpenRouter), the param is 'base_url' or 'openai_api_base'
        # Langchain's ChatOpenAI seems to prefer 'base_url' more recently.
        # For ChatOllama, it's also 'base_url'.
        init_args["base_url"] = base_url

    # Special handling for specific providers if needed
    if provider_key == "openrouter":
        # OpenRouter uses 'openai_api_base' if using ChatOpenAI class, or 'base_url'
        init_args["base_url"] = provider_config["base_url"] # Ensure this is passed correctly
        # If using ChatOpenAI, it might be init_args["openai_api_base"] = provider_config["base_url"]
        # For OpenRouter, the model name often includes the original provider, e.g., "openai/gpt-4"
        # The 'model_name' parameter for ChatOpenAI should be just the model part, e.g. "gpt-4"
        # This might require splitting model_to_use if it contains "/"
        if "/" in model_to_use and provider_key == "openrouter":
            # Example: "openai/gpt-3.5-turbo" -> "gpt-3.5-turbo" for ChatOpenAI model_name
            # The full "openai/gpt-3.5-turbo" is sent as 'model' in the actual API request by OpenRouter
            # Langchain's ChatOpenAI with a base_url for OpenRouter handles this.
            pass


    try:
        return llm_class(**init_args)
    except Exception as e:
        st.error(f"Failed to initialize LLM for {provider_name} with model {model_to_use}: {e}")
        return None

@st.cache_data(ttl=3600) # Cache for 1 hour
def get_available_models(provider_name: str):
    """
    Fetches available models for a given provider.
    API keys are handled internally if needed by the specific fetching logic.
    """
    provider_key = provider_name.lower()
    provider_config = SUPPORTED_PROVIDERS.get(provider_key)

    if not provider_config:
        return [f"Provider {provider_name} not supported"]

    default_model_list = [provider_config.get("default_model", "Default Model Not Set")]
    models = []
    api_key = None # Define api_key variable outside the blocks

    # --- OpenAI ---
    if provider_key == "openai":
        api_key_secret_name = provider_config.get("api_key_secret")
        if api_key_secret_name:
            api_key = st.secrets.get(api_key_secret_name)
        if api_key:
            try:
                from openai import OpenAI # Ensure openai library is installed
                client = OpenAI(api_key=api_key)
                # Fetch all models, then filter if needed (e.g., for chat models)
                all_openai_models = [model.id for model in client.models.list().data if "gpt" in model.id.lower()]
                models = sorted(list(set(all_openai_models)))
            except ImportError:
                print("OpenAI library not installed. Cannot fetch models dynamically for OpenAI.")
                st.sidebar.warning("OpenAI library not found. Install with `pip install openai` to see dynamic models.")
            except Exception as e:
                print(f"Could not fetch models for {provider_name}: {e}")
        else:
            print(f"API key for {provider_name} not found in secrets. Cannot fetch models.")
        if not models: models = default_model_list

    # --- OpenRouter ---
    elif provider_key == "openrouter":
        openrouter_endpoint = provider_config.get("base_url", "https://openrouter.ai/api/v1") + "/models"
        try:
            response = requests.get(openrouter_endpoint, timeout=10)
            response.raise_for_status()
            models_data = response.json().get('data', [])
            models = sorted(list(set([item['id'] for item in models_data])))
        except requests.exceptions.RequestException as e:
            print(f"Could not fetch models for {provider_name} from {openrouter_endpoint}: {e}")
        except Exception as e:
            print(f"Error processing response for {provider_name}: {e}")
        if not models: models = default_model_list

    # --- Ollama ---
    elif provider_key == "ollama":
        ollama_base_url_env_var = provider_config.get("base_url_env_var", "OLLAMA_ENDPOINT")
        ollama_base_url = st.secrets.get(ollama_base_url_env_var, "http://localhost:11434")
        ollama_endpoint = f"{ollama_base_url.rstrip('/')}/api/tags"
        try:
            response = requests.get(ollama_endpoint, timeout=5)
            response.raise_for_status()
            models_data = response.json().get('models', [])
            models = sorted(list(set([tag['name'] for tag in models_data])))
        except requests.exceptions.ConnectionError:
            print(f"Could not connect to Ollama at {ollama_base_url}. Is Ollama running?")
            models = [f"Ollama not reachable at {ollama_base_url}"]
        except requests.exceptions.Timeout:
            print(f"Connection to Ollama at {ollama_base_url} timed out.")
            models = [f"Ollama timed out at {ollama_base_url}"]
        except Exception as e:
            print(f"Could not fetch models for Ollama: {e}")
        if not models and not (models and ("Ollama not reachable" in models[0] or "Ollama timed out" in models[0])):
            models = default_model_list

    # --- Anthropic (Hardcoded List - Dynamic fetch requires SDK/API call & auth) ---
    elif provider_key == "anthropic":
        # Anthropic models are typically hardcoded or less frequently changed.
        # Dynamic fetching would require the anthropic SDK and API key.
        # For simplicity and to avoid forcing API key for just listing, using a common list.
        # Users can always type a model name if it's not listed.
        common_anthropic_models = [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229",
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2"
        ]
        models = common_anthropic_models
        default_model = provider_config.get("default_model")
        if default_model and default_model not in models:
            models.append(default_model)
        models = sorted(list(set(models)))

    # --- Google ---
    elif provider_key == "google":
        api_key_secret_name = provider_config.get("api_key_secret")
        if api_key_secret_name:
            api_key = st.secrets.get(api_key_secret_name)
        if api_key:
            try:
                import google.generativeai as genai # Ensure library is installed
                genai.configure(api_key=api_key)
                all_google_models = [m.name.replace("models/", "") for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                models = sorted(list(set(all_google_models)))
            except ImportError:
                print("google-generativeai library not installed. Cannot fetch models dynamically for Google.")
                st.sidebar.warning("google-generativeai library not found. Install with `pip install google-generativeai`.")
            except Exception as e:
                print(f"Could not fetch models for {provider_name}: {e}")
        else:
            print(f"API key for {provider_name} not found in secrets. Cannot fetch models.")
        if not models: models = default_model_list

    # --- Groq ---
    elif provider_key == "groq":
        api_key_secret_name = provider_config.get("api_key_secret")
        if api_key_secret_name:
            api_key = st.secrets.get(api_key_secret_name)
        if api_key:
            # Groq uses an OpenAI-compatible endpoint for listing models
            groq_models_url = "https://api.groq.com/openai/v1/models" # Standard endpoint
            try:
                headers = {"Authorization": f"Bearer {api_key}"}
                response = requests.get(groq_models_url, headers=headers, timeout=10)
                response.raise_for_status()
                models_data = response.json().get("data", [])
                all_groq_models = [model.get("id") for model in models_data if model.get("id")]
                models = sorted(list(set(all_groq_models)))
            except requests.exceptions.RequestException as e:
                print(f"Could not fetch models for {provider_name} from {groq_models_url}: {e}")
            except Exception as e:
                print(f"Error processing response for {provider_name}: {e}")
        else:
            print(f"API key for {provider_name} not found in secrets. Cannot fetch models.")
        if not models: models = default_model_list

    # --- requesty (Placeholder) ---
    elif provider_key == "requesty":
        models = [provider_config.get("default_model", "requesty-default")]

    # --- Fallback for other unhandled or misconfigured providers ---
    else:
        models = default_model_list

    # Final cleanup and return
    if not models or models == ["default"] or models == ["Default Model Not Set"]: # More robust check for empty/default
        final_models = [provider_config.get("default_model", "No models listed")] if provider_config else ["No models listed"]
    else:
        final_models = models

    return sorted(list(set(m for m in final_models if m and isinstance(m, str)))) # Ensure unique, filter out None/empty, ensure strings


def get_llm_response(prompt_template_str: str,
                        input_variables: dict,
                        llm_provider: str, # User selected or default
                        llm_model: str = None,  # User selected or default for provider
                        chain_type: str = "basic", # "basic" for PromptTemplate, "chat" for ChatPromptTemplate
                        **llm_kwargs):
    """
    Creates a Langchain prompt template, initializes the LLM,
    forms a chain, and runs it to get the response.
    """
    llm = get_llm(provider_name=llm_provider, model_name=llm_model, **llm_kwargs)

    if not llm: # Check if LLM initialization failed
        st.error(f"LLM ({llm_provider}/{llm_model or 'default'}) failed to initialize. Cannot proceed.")
        return f"Error: LLM ({llm_provider}/{llm_model or 'default'}) failed to initialize."

    if chain_type == "chat":
        # For chat models, ChatPromptTemplate is generally preferred.
        # The template string should be structured accordingly (e.g. system/human/ai messages).
        # For a simple single-message chat, from_template can work.
        prompt = ChatPromptTemplate.from_template(template=prompt_template_str)
    else: # basic LLM
        prompt = PromptTemplate.from_template(template=prompt_template_str)

    chain = LLMChain(llm=llm, prompt=prompt)
    # Langchain's .run() method can take a dictionary of variables or keyword arguments
    # Ensure input_variables matches the placeholders in prompt_template_str
    try: # Outer try for the whole process after chain initialization
        # The PromptTemplate itself will validate if all necessary input_variables are present
        # when the chain is run. The previous custom key checking logic was problematic.
        try:
            response = chain.run(input_variables)
            return response
        except KeyError as ke: # Specifically catch KeyError for missing keys in the prompt
            st.error(f"Missing key in prompt variables for {llm_provider}/{llm.model_name if hasattr(llm, 'model_name') else 'unknown model'}: {ke}")
            return f"Error: Missing key {ke} required by the prompt."
        except Exception as e_chain: # More general exception for other chain run issues
            st.error(f"Error during LLM chain execution with {llm_provider}/{llm.model_name if hasattr(llm, 'model_name') else 'unknown model'}: {e_chain}")
            return f"Error processing LLM request during chain execution: {e_chain}"
    except Exception as e_outer: # Catch errors in the key preparation or other logic
        st.error(f"Outer error in get_llm_response before chain execution: {e_outer}")
        return f"Error preparing LLM request: {e_outer}"

class LLMInterface:
    """
    A wrapper class to provide a consistent interface for LLM interactions,
    particularly for generating text as expected by various logic engines.
    """
    def __init__(self, provider: Optional[str] = None, model: Optional[str] = None):
        """
        Initializes the LLMInterface.
        If provider and model are not given, they should be available in st.session_state
        when generate_text is called (e.g., from a sidebar selection).
        """
        self.default_provider = provider
        self.default_model = model

    def generate_text(self, prompt_template_str: str, max_tokens: Optional[int] = None, **input_variables) -> str:
        """
        Generates text using the configured LLM.

        Args:
            prompt_template_str: The prompt template string.
            max_tokens: The maximum number of tokens to generate.
            **input_variables: Variables to fill into the prompt template.

        Returns:
            The LLM-generated text as a string, or an error message string.
        """
        # Determine provider and model to use from global session state,
        # falling back to instance defaults or hardcoded if necessary.
        default_provider_fallback = "openai" # A general fallback if nothing else is set
        if SUPPORTED_PROVIDERS:
            default_provider_fallback = list(SUPPORTED_PROVIDERS.keys())[0]


        current_provider = self.default_provider or st.session_state.get("global_ai_provider", default_provider_fallback)
        current_model = self.default_model or st.session_state.get("global_ai_model")
        # If current_model is still None, get_llm_response will use the provider's default.

        llm_kwargs = {}
        if max_tokens is not None:
            llm_kwargs["max_tokens"] = max_tokens
        
        # Temperature from global session state
        temperature = st.session_state.get("global_temperature", 0.7) # Default temperature
        llm_kwargs["temperature"] = temperature

        # API Key and Endpoint from global session state (if set by user in UI)
        # These will be passed to get_llm via get_llm_response's **llm_kwargs
        global_api_key = st.session_state.get("global_api_key")
        if global_api_key:
            llm_kwargs["api_key"] = global_api_key
        
        global_api_endpoint = st.session_state.get("global_api_endpoint")
        if global_api_endpoint:
            llm_kwargs["base_url"] = global_api_endpoint

        response = get_llm_response(
            prompt_template_str=prompt_template_str,
            input_variables=input_variables,
            llm_provider=current_provider,
            llm_model=current_model,
            **llm_kwargs # This will now include api_key and base_url if set globally
        )
        return response
