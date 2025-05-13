# ainvestor 🚀

**ainvestor** is an AI-powered toolkit designed to assist startup founders and entrepreneurs with critical aspects of their investment journey. It provides intelligent agents for pitch deck analysis, financial modeling, and investor scouting.

This project is built with Python, Streamlit, and Langchain.

## Table of Contents

- [Features](#features)
- [Project Structure](#project-structure)
- [Setup](#setup)
- [Running the Application](#running-the-application)
- [Configuration](#configuration)
  - [API Keys](#api-keys)
  - [LLM Providers](#llm-providers)
- [Development](#development)
  - [Core Principles](#core-principles)
  - [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Features

The MVP (Minimum Viable Product) includes the following AI agents:

1.  **Pitch Deck Advisor (v1):**
    *   Upload existing pitch deck (PDF/PPTX - parsing is currently mocked).
    *   NLP analysis for clarity, conciseness, keyword density (via LLM).
    *   Compares structure against successful templates (general best practices).
    *   Provides actionable feedback points.
    *   Offers downloadable pitch deck templates (placeholder).
2.  **Financial Modeling Agent (v1):**
    *   Guided input for key financial assumptions.
    *   Generates basic 3-year Profit & Loss, Cash Flow, and Balance Sheet statements.
    *   Simple scenario analysis (e.g., +/- revenue sensitivity - UI placeholder).
    *   Excel export of financial models (logic implemented, UI placeholder).
3.  **Investor Scout (v1):**
    *   User inputs industry, stage, and desired investment range.
    *   Matches against a curated local CSV database (`data/investor_db.csv`).
    *   (Future: API integration with Crunchbase/PitchBook or LLM-enhanced matching).
4.  **Unified Dashboard (v1.0):**
    *   Integrates these agents, allows navigation, and shows status.

## Project Structure

The project follows a modular structure:

```
ainvestor/
├── app.py                     # Main Streamlit app entry point
├── pages/                     # Streamlit multi-page app structure
│   ├── 1_Pitch_Deck_Advisor.py
│   ├── 2_Financial_Modeling.py
│   └── 3_Investor_Scout.py
├── core/                      # Core business logic (non-Streamlit specific)
│   ├── __init__.py
│   ├── pitch_deck_logic.py
│   ├── financial_model_logic.py
│   ├── investor_scout_logic.py
│   ├── llm_interface.py       # Handles all LLM interactions via Langchain
│   └── utils.py               # Common utility functions (file parsing, etc.)
├── prompts/                   # LLM prompt templates
│   ├── __init__.py
│   ├── pitch_deck_advisor_prompts.py
│   ├── financial_modeling_prompts.py
│   └── investor_scout_prompts.py
├── assets/                    # Static assets (images, downloadable templates)
│   └── pitch_deck_template_v1.pptx # Placeholder
├── data/                      # Local data files
│   └── investor_db.csv        # Sample investor database
├── tests/                     # Unit tests for core logic
│   ├── __init__.py
│   ├── test_pitch_deck_logic.py
│   ├── test_financial_model_logic.py
│   └── test_llm_interface.py
├── .streamlit/                # Streamlit configuration
│   ├── secrets.toml           # API keys and sensitive config (DO NOT COMMIT REAL SECRETS)
│   └── config.toml            # General Streamlit app config
├── requirements.txt           # Python dependencies
├── vision.md                  # Project vision and implementation guidelines (this was the source doc)
└── README.md                  # This file
```

## Setup

1.  **Clone the repository:**
    ```bash
    git clone <repository_url>
    cd ainvestor
    ```

2.  **Create a virtual environment (recommended):**
    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
    *Note: Some dependencies in `requirements.txt` for file parsing (like `PyPDF2`, `python-pptx`) and testing (`pytest`) are commented out. Uncomment and install them if you plan to implement or run those specific parts.*

4.  **Configure API Keys:**
    *   Copy the example secrets file: `cp .streamlit/secrets.toml.example .streamlit/secrets.toml` (if an example is provided) or create `.streamlit/secrets.toml`.
    *   Edit `.streamlit/secrets.toml` and add your API keys for the LLM providers you intend to use (OpenAI, Anthropic, OpenRouter, Google, Groq, etc.). See the `SUPPORTED_PROVIDERS` dictionary in `core/llm_interface.py` for required secret names.
    *   Example for OpenAI: `OPENAI_API_KEY = "sk-..."`
    *   For Ollama, if it's not running on `http://localhost:11434`, set `OLLAMA_BASE_URL` in `secrets.toml`.

## Running the Application

Once the setup is complete, run the Streamlit application from the project root directory:

```bash
streamlit run app.py
```

The application should open in your default web browser.

## Configuration

### API Keys

API keys for LLM providers are managed via Streamlit's secrets mechanism. Store them in `.streamlit/secrets.toml`. This file should **not** be committed to version control if it contains real secrets.

### LLM Providers

The application uses Langchain to interact with various LLM providers. Supported providers and their configurations are defined in `core/llm_interface.py` in the `SUPPORTED_PROVIDERS` dictionary. Users can select their preferred provider and model through the UI on relevant pages (Pitch Deck Advisor, potentially others).

The `core/llm_interface.py` module also includes a function `get_available_models(provider_name)` which attempts to dynamically fetch model lists for configured providers. This functionality depends on the provider's API and correct API key setup.

## Development

### Core Principles

*   **Modularity:** UI (Streamlit pages) is kept separate from business logic (`core/` modules).
*   **Readability:** Clean, well-commented Python code (PEP 8).
*   **State Management:** `st.session_state` is used for managing state within Streamlit pages.
*   **Error Handling:** `try-except` blocks and user-friendly error messages (`st.error()`).
*   **Configuration:** `st.secrets` for sensitive data; constants or `config.py` for non-sensitive config.
*   **Reusability:** Common functions in `core/utils.py`.

Refer to `vision.md` for detailed implementation guidelines that were followed.

### Testing

Unit tests are located in the `tests/` directory and use `pytest`.
To run tests:

```bash
pip install pytest pytest-mock # If not already installed
pytest
```
Tests primarily focus on the `core/` logic modules and `llm_interface.py`. Mocking is used for external API calls.

## Contributing

Contributions are welcome! Please follow standard Git practices (fork, feature branch, pull request). Ensure your code adheres to the project's style and includes tests for new functionality.

(Further details on contribution process can be added here).

## License

(Specify a license, e.g., MIT, Apache 2.0, or leave as TBD).
This project is currently unlicensed (TBD).
