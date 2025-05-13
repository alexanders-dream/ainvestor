# core/llm_interface.py
import streamlit as st
import requests # For fetching models from some APIs if Langchain doesn't support it directly
import json # For JSON handling
import yaml # For YAML handling
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

    api_key = None
    if provider_config.get("api_key_secret"): # Check if 'api_key_secret' key exists
        api_key_secret_name = provider_config["api_key_secret"]
        if api_key_secret_name: # Check if the value of 'api_key_secret' is not None
            api_key = st.secrets.get(api_key_secret_name)
            if not api_key:
                raise ValueError(
                    f"API key ({provider_config['api_key_secret']}) for {provider_name} not found in st.secrets. "
                    "Ensure it is set in .streamlit/secrets.toml."
                )
    elif provider_key != "ollama": # If api_key_secret is not defined or is None, and it's not ollama
        # This case might indicate a configuration issue for providers that DO require keys
        # but it's handled by the check within the 'if api_key_secret_name:' block mostly.
        # Ollama is a special case that might not need an API key.
        pass


    model_to_use = model_name or provider_config["default_model"]
    llm_class = provider_config["class"]

    init_args = {"model_name": model_to_use, **kwargs}

    # Handle API key parameter name
    if api_key and provider_config.get("api_key_param"):
        init_args[provider_config["api_key_param"]] = api_key
    elif api_key: # Default to 'api_key' if not specified, but might be wrong for some
            init_args["api_key"] = api_key


    # Handle base URL for providers like OpenRouter or Ollama
    if provider_config.get("base_url"):
        init_args["base_url"] = provider_config["base_url"]
    elif provider_config.get("base_url_env_var"):
        base_url_from_secrets = st.secrets.get(provider_config["base_url_env_var"])
        if base_url_from_secrets:
            init_args["base_url"] = base_url_from_secrets
        # For Ollama, Langchain's ChatOllama might default to http://localhost:11434 if base_url not provided

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
    try:
        # Ensure all required keys are present in input_variables
        # This is a common issue with LangChain chains
        required_keys = []
        for key in prompt_template_str.split("{"):
            if "}" in key:
                required_key = key.split("}")[0].strip()
                if required_key and required_key not in required_keys:
                    required_keys.append(required_key)

        # Check if any required keys are missing from input_variables
        missing_keys = [key for key in required_keys if key not in input_variables]
        if missing_keys:
            # Add missing keys with empty values to prevent chain execution errors
            for key in missing_keys:
                if key == "extracted_profiles":
                    input_variables[key] = []
                else:
                    input_variables[key] = ""
            st.warning(f"Added missing keys to prevent chain execution errors: {missing_keys}")

        # Add special handling for the "extracted_profiles" key which seems to cause issues
        if "extracted_profiles" not in input_variables and "extracted_profiles" not in missing_keys:
            input_variables["extracted_profiles"] = []
            st.warning("Added 'extracted_profiles' key as a precaution to prevent chain execution errors")

        # Use a try-except block specifically for the chain.run call
        try:
            response = chain.run(input_variables)
            return response
        except KeyError as key_err:
            # If we still get a KeyError, try to add the missing key and retry
            missing_key = str(key_err).strip("'")
            st.warning(f"KeyError during chain execution: {key_err}. Adding missing key and retrying.")
            if missing_key == "extracted_profiles":
                input_variables[missing_key] = []
            else:
                input_variables[missing_key] = ""

            # Try one more time
            response = chain.run(input_variables)
            return response

    except Exception as e:
        st.error(f"Error during LLM chain execution with {llm_provider}/{llm.model_name if hasattr(llm, 'model_name') else 'unknown model'}: {e}")
        # Return a more useful error message that won't break YAML parsing
        return dump_yaml({"extracted_profiles": [], "error": f"Error processing LLM request: {e}"})
