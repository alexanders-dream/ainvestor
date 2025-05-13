Key AI Agents (MVP versions):
1. Pitch Deck Advisor (v1):
    - Functionality: Upload existing deck (PDF/PPTX). NLP analysis for clarity, conciseness, keyword density. Compares structure against successful templates (general best practices). Provides actionable feedback points. Offers 2-3 customizable templates.
UI/UX: Clean uploader, clear feedback annotations, template browser.
2. Financial Modeling Agent (v1):
    - Functionality: Guided input for key assumptions (revenue drivers, COGS, OpEx). Generates basic 3-year P&L, Cash Flow, Balance Sheet. Simple scenario analysis (e.g., +/- 20% revenue). Excel export.
    UI/UX: Step-by-step wizard for inputs, clear chart visualizations.
3. Investor Scout (v1):
    - Functionality: User inputs industry, stage, desired investment. Matches against a curated (initially smaller, perhaps manually supplemented) database or via API to Crunchbase/PitchBook (if budget allows for API access early). Integrates with Firecrawl API to search the web for investors and their information, enabling more comprehensive investor discovery beyond static databases.
    UI/UX: Simple search interface, filterable results list, web search results visualization.
4. Investor Strategy Agent (v1):
    - Functionality: AI agent that develops and implements strategies for finding relevant investors. Analyzes startup profile, market trends, and investor preferences to create targeted investor discovery plans. Executes search strategies using Firecrawl API and other data sources. Provides actionable insights and prioritized investor lists.
    UI/UX: Strategy builder interface, execution dashboard with progress tracking, results visualization.
5. Unified Dashboard v1.0:
    - Integrates these agents, allows navigation, shows status.


ainvestor/
├── app.py # Main Streamlit app entry point (Dashboard/Landing Page)
├── pages/ # Streamlit's multi-page app structure
│ ├── 1_Pitch_Deck_Advisor.py
│ ├── 2_Financial_Modeling.py
│ ├── 3_Investor_Scout.py
│ └── 4_Investor_Strategy_Agent.py
├── core/ # Core logic, non-Streamlit specific
│ ├── init.py
│ ├── pitch_deck_logic.py
│ ├── financial_model_logic.py
│ ├── investor_scout_logic.py
│ ├── investor_strategy_logic.py
│ ├── firecrawl_api.py # Interface for Firecrawl API
│ ├── llm_interface.py # Renamed from llm_integration for clarity
│ └── utils.py # Common utility functions (file parsing, etc.)
├── prompts/ # Folder for LLM prompt templates
│ ├── init.py
│ ├── pitch_deck_advisor_prompts.py
│ ├── financial_modeling_prompts.py
│ ├── investor_scout_prompts.py
│ └── investor_strategy_prompts.py
├── assets/ # Static assets (images, downloadable templates)
│ └── pitch_deck_template_v1.pptx
├── data/ # Local data files (e.g., investor_db.csv)
│ └── investor_db.csv
├── tests/ # Unit tests for core logic
│ ├── init.py
│ ├── test_pitch_deck_logic.py
│ ├── test_financial_model_logic.py
│ ├── test_investor_scout_logic.py
│ ├── test_investor_strategy_logic.py
│ ├── test_firecrawl_api.py
│ └── test_llm_interface.py # Example test for prompt formatting
├── .streamlit/
│ ├── secrets.toml # For API keys (DO NOT COMMIT if public repo)
│ └── config.toml # Streamlit app config
├── requirements.txt # Python dependencies
└── IMPLEMENTATION_GUIDELINES.md # This file
└── README.md # Project overview, setup, and run instructions

## 2. Core Principles

*   **Modularity:** Keep UI (Streamlit pages) separate from business logic (`core/` modules).
*   **Readability:** Write clean, well-commented Python code. Follow PEP 8 guidelines.
*   **State Management:** Utilize `st.session_state` judiciously and predictably. Initialize keys at the top of each page or globally in `app.py` if needed. Prefix session state keys specific to a page (e.g., `pda_uploaded_file` for Pitch Deck Advisor).
*   **Error Handling:** Implement robust `try-except` blocks in `core/` logic and around external calls. Display user-friendly errors in the UI using `st.error()`. Log detailed errors for debugging.
*   **Configuration:** Use `st.secrets` for all sensitive information (API keys, etc.). Non-sensitive configurations can be constants in relevant modules or a dedicated `config.py`.
*   **Reusability:** Create utility functions in `core/utils.py` for common tasks.

## 3. Agent Implementation Workflow (General)

For each agent (e.g., Pitch Deck Advisor):

1.  **Define Prompts (`prompts/`):**
    *   Create a dedicated Python file (e.g., `pitch_deck_advisor_prompts.py`).
    *   Store prompt templates as multi-line strings or functions that return formatted strings.
    *   Use f-strings or `.format()` for dynamic variable substitution.
2.  **Implement Core Logic (`core/`):**
    *   Create a module (e.g., `pitch_deck_logic.py`).
    *   Write functions that perform the agent's tasks (data extraction, NLP, calculations).
    *   These functions should NOT contain Streamlit UI code.
    *   Import and use prompts from the `prompts/` directory via the `llm_interface.py`.
    *   The `llm_interface.py` module will handle:
        *   Loading prompts.
        *   Substituting placeholder variables into prompts.
        *   Making the actual API call to the LLM.
        *   Basic parsing of LLM responses (if necessary, e.g., expecting JSON).
3.  **Develop Streamlit Page (`pages/`):**
    *   Create the UI using Streamlit widgets.
    *   Manage page-specific state using `st.session_state`.
    *   **UI for LLM Selection:** Include UI elements (e.g., `st.selectbox`) for the user to choose the LLM provider (from `SUPPORTED_PROVIDERS` in `llm_interface.py`) and a dynamically populated list of available models for that provider. The selection (provider and model name) should be stored in `st.session_state` (e.g., `st.session_state.selected_llm_provider`, `st.session_state.selected_llm_model`) and passed to the `core` logic functions when invoking LLM-dependent operations.
    *   On user action (e.g., button click):
        *   Retrieve inputs from `st.session_state`, including selected LLM provider and model.
        *   Call functions from the corresponding `core/` logic module, passing provider/model info.
        *   Use `st.spinner()` for long-running operations.
        *   Store results back into `st.session_state`.
        *   Display results or errors.
4.  **Unit Testing (`tests/`):**
    *   Write unit tests for functions in `core/` modules, especially logic and prompt formatting/filling in `llm_interface.py`.
    *   Mock external API calls (e.g., LLM APIs, dynamic model fetching) during tests.

## 4. LLM Interaction with Langchain (`core/llm_interface.py` and `prompts/`)

To ensure the application is AI model agnostic and can leverage various providers, all LLM interactions will be managed through `core/llm_interface.py` using the Langchain library. Users will be able to select their preferred provider and model through the UI.

*   **Langchain-based Centralized Interface (`core/llm_interface.py`):**
    *   This module is responsible for abstracting LLM provider specifics.
    *   It will import necessary Langchain modules. Example imports:
        ```python
        # core/llm_interface.py
        import streamlit as st
        import requests # For fetching models from some APIs if Langchain doesn't support it directly
        from langchain_openai import ChatOpenAI
        from langchain_anthropic import ChatAnthropic
        from langchain_google_genai import ChatGoogleGenerativeAI
        from langchain_groq import ChatGroq
        from langchain_community.chat_models import ChatOllama # Or from langchain.chat_models
        # For OpenRouter, it might use ChatOpenAI with a custom base URL or a dedicated class if available
        # from langchain_community.chat_models import ChatOpenRouter
        from langchain.prompts import PromptTemplate, ChatPromptTemplate
        from langchain.chains import LLMChain
        ```
    *   It will contain functions to initialize and return Langchain LLM/ChatModel instances.
    *   **Supported Providers Configuration:**
        ```python
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
            if provider_config["api_key_secret"]:
                api_key = st.secrets.get(provider_config["api_key_secret"])
                if not api_key:
                    raise ValueError(
                        f"API key ({provider_config['api_key_secret']}) for {provider_name} not found in st.secrets. "
                        "Ensure it is set in .streamlit/secrets.toml."
                    )

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

        # Placeholder for dynamic model fetching logic
        @st.cache_data(ttl=3600) # Cache for 1 hour
        def get_available_models(provider_name: str):
            """
            Fetches available models for a given provider.
            This is a placeholder and needs actual implementation for each provider.
            The API key should be handled within this function or passed carefully.
            """
            provider_key = provider_name.lower()
            provider_config = SUPPORTED_PROVIDERS.get(provider_key)
            models = [provider_config.get("default_model", "default")] if provider_config else ["default"]

            # Example for OpenAI (requires 'openai' client library and API key)
            # if provider_key == "openai" and st.secrets.get(provider_config["api_key_secret"]):
            #     try:
            #         from openai import OpenAI
            #         client = OpenAI(api_key=st.secrets.get(provider_config["api_key_secret"]))
            #         models = [model.id for model in client.models.list().data]
            #     except Exception as e:
            #         print(f"Could not fetch models for {provider_name}: {e}")
            #         models = [provider_config.get("default_model", "default")]

            # Example for OpenRouter (API endpoint: https://openrouter.ai/api/v1/models)
            # if provider_key == "openrouter":
            #     try:
            #         response = requests.get("https://openrouter.ai/api/v1/models")
            #         response.raise_for_status()
            #         models = [item['id'] for item in response.json()['data']]
            #     except Exception as e:
            #         print(f"Could not fetch models for {provider_name}: {e}")
            #         models = [provider_config.get("default_model", "default")]

            # For Ollama, one might call its API endpoint (e.g., GET /api/tags)
            # if provider_key == "ollama":
            #    ollama_base_url = st.secrets.get(provider_config.get("base_url_env_var"), "http://localhost:11434")
            #    try:
            #        response = requests.get(f"{ollama_base_url}/api/tags")
            #        response.raise_for_status()
            #        models = [tag['name'] for tag in response.json()['models']]
            #    except Exception as e:
            #        print(f"Could not fetch models for Ollama: {e}")
            #        models = [provider_config.get("default_model", "default")]

            # Implement similar logic for Anthropic, Google, Groq, requesty based on their APIs

            if not models or models == ["default"]: # Fallback if fetching fails or not implemented
                 return [provider_config.get("default_model", "No models listed")] if provider_config else ["No models listed"]
            return sorted(list(set(m for m in models if m))) # Ensure unique and filter out None/empty


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
            response = chain.run(input_variables)
            return response
        ```
    *   API keys for different providers (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`) must be stored in `.streamlit/secrets.toml`.
    *   The `get_llm` function handles basic error catching for API key retrieval and model initialization. Further error handling for API calls within chains should be considered.

*   **Prompt Management for Langchain:**
    *   Prompts remain in their respective files within the `prompts/` directory (e.g., `prompts/pitch_deck_advisor_prompts.py`).
    *   Prompt strings should be designed to be compatible with Langchain's `PromptTemplate` or `ChatPromptTemplate` (e.g., using `{variable_name}` for placeholders).
    *   Example `prompts/pitch_deck_advisor_prompts.py`:
        ```python
        # prompts/pitch_deck_advisor_prompts.py
        PROMPT_OVERALL_FEEDBACK = """
        **Role:** You are an expert pitch deck analyst...
        **Pitch Deck Content:**
        ---
        [Problem Section Text: {problem_section_text}]
        [Solution Section Text: {solution_section_text}]
        ---
        ...
        **Task:** Analyze the provided pitch deck sections.
        **Output Format:**
        Provide your feedback in well-structured markdown...
        """ # Ensure all {variables} are defined

        def get_messaging_refinement_prompt_template(): # Renamed for clarity
            """
            Returns a template string for messaging refinement.
            Placeholders {section_name}, {section_text}, {startup_usp} should be filled by Langchain.
            """
            return """
            **Role:** You are a master storyteller...
            **Task:** Refine the following text from the "{section_name}" section of a pitch deck.
            **Original Text:**
            ```
            {section_text}
            ```
            **Startup's Stated USP (if provided, otherwise infer):** "{startup_usp}"
            **Instructions:** Rewrite the text to be more clear, concise, and impactful.
            Focus on strong verbs and compelling language.
            **Refined Text:**
            """
        ```
        *Note: Functions generating prompts should return template strings. The calling code will pass the actual values for placeholders to `get_llm_response` via the `input_variables` dictionary.*

*   **Using Langchain Prompts in Core Logic (e.g., `core/pitch_deck_logic.py`):**
    ```python
    # core/pitch_deck_logic.py
    from .llm_interface import get_llm_response
    from prompts import pitch_deck_advisor_prompts

    def get_deck_feedback_from_llm(extracted_sections_data, provider="openai", model=None):
        # Variables for the PROMPT_OVERALL_FEEDBACK template
        prompt_variables = {
            "problem_section_text": extracted_sections_data.get('problem', ''),
            "solution_section_text": extracted_sections_data.get('solution', ''),
            # ... ensure all other variables used in PROMPT_OVERALL_FEEDBACK are included
        }
        response = get_llm_response(
            prompt_template_str=pitch_deck_advisor_prompts.PROMPT_OVERALL_FEEDBACK,
            input_variables=prompt_variables,
            llm_provider=provider,
            llm_model=model
            # chain_type can be specified if needed, default is "basic"
        )
        return response # Or parse it further

    def get_section_refinement_from_llm(section_name, section_text, usp, provider="openai", model=None):
        prompt_template = pitch_deck_advisor_prompts.get_messaging_refinement_prompt_template()

        input_vars = {
            "section_name": section_name,
            "section_text": section_text,
            "startup_usp": usp
        }

        response = get_llm_response(
            prompt_template_str=prompt_template,
            input_variables=input_vars,
            llm_provider=provider,
            llm_model=model
        )
        return response
    ```
*   The `core` logic modules will specify the `llm_provider` and optionally `llm_model` when calling `get_llm_response`. This allows flexibility in choosing the LLM for different tasks, which could be based on user selection in the UI, application configuration, or specific needs of an agent.

This revised section emphasizes Langchain's role in abstraction, prompt templating, and chain execution, making the system more flexible and robust in its use of different AI model providers.

## 5. State Management (`st.session_state`)

*   Initialize all `st.session_state` keys used on a page at the beginning of the page script to avoid `KeyError`.
*   Use clear and consistent naming for keys (e.g., `pda_uploaded_file`, `fm_financial_inputs`).
*   Avoid overly complex nested structures in `st.session_state` if possible.
*   Ensure state is reset or cleared appropriately (e.g., when a new file is uploaded, clear old analysis results).

## 6. File Handling

*   For uploaded files (e.g., pitch decks):
    *   Use `st.file_uploader`.
    *   Process file bytes in memory or save temporarily if needed for external tools.
    *   Gracefully handle file parsing errors (e.g., corrupted PDF/PPTX).
*   For downloadable files (e.g., financial models as Excel, templates):
    *   Use `st.download_button`.
    *   Prepare data in the correct format (e.g., BytesIO object for Excel).

## 7. Dependencies (`requirements.txt`)

*   Keep `requirements.txt` up-to-date with all necessary packages.
*   Specify versions to ensure consistent environments (e.g., `streamlit==1.28.0`, `openai==0.28.0`).
*   Include linters and testing frameworks (`flake8`, `black`, `pytest`).

## 8. Code Style and Quality

*   **PEP 8:** Follow PEP 8 style guidelines. Use linters (`flake8`) and formatters (`black`).
*   **Comments:** Add comments to explain complex logic, assumptions, or "why" something is done a certain way.
*   **Docstrings:** Use docstrings for modules, classes, and functions.
*   **Keep Functions Short:** Aim for functions that do one thing well.
*   **Avoid Hardcoding:** Use configuration files or constants for values that might change.

## 9. Testing

*   Prioritize unit testing for `core/` modules and the `llm_interface.py`.
*   Test data parsing, calculations, prompt formatting, and basic business logic.
*   Use `pytest` as the testing framework.
*   Mock external dependencies (LLM APIs, file system access where appropriate) to make tests fast and reliable.

## 10. User Experience (UX) Considerations

*   Provide clear instructions and guidance to the user.
*   Use `st.spinner()` to indicate background processing.
*   Ensure responsive layout.
*   Present information clearly and concisely. Use `st.info()`, `st.success()`, `st.warning()`, `st.error()` appropriately.
*   Offer clear calls to action.

---
This document is a living document and may be updated as the project evolves.
