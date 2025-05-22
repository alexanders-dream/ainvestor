import streamlit as st
from core.llm_interface import SUPPORTED_PROVIDERS, get_available_models

# --- Page Configuration ---
st.set_page_config(
    page_title="ainvestor - Dashboard",
    page_icon="🚀",
    layout="wide"
)

# --- Session State Initialization ---
def initialize_global_session_state():
    """Initializes global session state keys for AI configuration."""
    default_provider = "groq" if "groq" in SUPPORTED_PROVIDERS else (list(SUPPORTED_PROVIDERS.keys())[0] if SUPPORTED_PROVIDERS else None)

    if 'global_ai_provider' not in st.session_state:
        st.session_state.global_ai_provider = default_provider
    if 'global_ai_model' not in st.session_state:
        st.session_state.global_ai_model = None # Will be set after provider selection
    if 'global_api_key' not in st.session_state:
        st.session_state.global_api_key = ""
    if 'global_api_endpoint' not in st.session_state:
        st.session_state.global_api_endpoint = ""
    if 'global_temperature' not in st.session_state:
        st.session_state.global_temperature = 0.30
    if 'global_max_tokens' not in st.session_state:
        st.session_state.global_max_tokens = 4096
    if 'global_available_models' not in st.session_state:
        st.session_state.global_available_models = []

    # For cross-tool data sharing
    if 'global_startup_profile' not in st.session_state:
        st.session_state.global_startup_profile = {
            "name": "",
            "industry": "",
            "stage": "",
            "funding_needed": "",
            "usp": ""
        }
    if 'global_pitch_deck_raw_text' not in st.session_state: # Added for raw text
        st.session_state.global_pitch_deck_raw_text = ""
    # Initialize status for project tracking
    if 'pitch_deck_status' not in st.session_state:
        st.session_state.pitch_deck_status = "Not Started"
    if 'financial_model_status' not in st.session_state:
        st.session_state.financial_model_status = "Not Started"
    if 'investor_scout_status' not in st.session_state:
        st.session_state.investor_scout_status = "Not Started"
    if 'investor_strategy_status' not in st.session_state:
        st.session_state.investor_strategy_status = "Not Started"
    
    # For Tour feature
    if 'tour_step' not in st.session_state:
        st.session_state.tour_step = 0 # Start tour
    if 'tour_active' not in st.session_state:
        st.session_state.tour_active = True # Tour is active by default for new sessions


initialize_global_session_state()

# --- AI Configuration Sidebar ---
with st.sidebar:
    st.subheader("⚙️ AI Configuration", help="Configure your AI provider and model settings globally.")

    # 1. AI Provider Selection
    sorted_providers = sorted([p for p, conf in SUPPORTED_PROVIDERS.items() if conf.get("class")])
    current_provider_index = sorted_providers.index(st.session_state.global_ai_provider) if st.session_state.global_ai_provider in sorted_providers else 0
    
    selected_provider_name = st.selectbox(
        "AI Provider",
        options=sorted_providers,
        index=current_provider_index,
        key="sb_global_ai_provider_name", # Unique key for this widget
        help="Select the AI provider you want to use."
    )
    # Update session state if changed by the widget
    if selected_provider_name != st.session_state.global_ai_provider:
        st.session_state.global_ai_provider = selected_provider_name
        st.session_state.global_ai_model = None # Reset model when provider changes
        st.session_state.global_api_key = "" # Reset API key
        st.session_state.global_api_endpoint = "" # Reset API endpoint
        st.rerun() # Rerun to update model list and prefill endpoint/key

    provider_config = SUPPORTED_PROVIDERS.get(st.session_state.global_ai_provider, {})

    # 2. Provider Settings Expander
    with st.expander("Provider Settings", expanded=True):
        # API Endpoint - Load from secrets first, then config default, then allow user override
        base_url_secret_name = provider_config.get("base_url_secret")
        endpoint_from_secrets = st.secrets.get(base_url_secret_name) if base_url_secret_name else None
        default_endpoint_from_config = provider_config.get("base_url") # Hardcoded default in SUPPORTED_PROVIDERS
        
        # Determine the initial value for the text input
        initial_endpoint_value = st.session_state.global_api_endpoint # Keep current value if already set
        if not initial_endpoint_value: # If empty (e.g., provider just changed)
            initial_endpoint_value = endpoint_from_secrets or default_endpoint_from_config or ""
            # Special default for Ollama if still empty
            if st.session_state.global_ai_provider == "ollama" and not initial_endpoint_value:
                initial_endpoint_value = "http://localhost:11434"
            st.session_state.global_api_endpoint = initial_endpoint_value # Update state if prefilled

        st.session_state.global_api_endpoint = st.text_input(
            "API Endpoint",
            value=st.session_state.global_api_endpoint, # Use the potentially pre-filled value
            key="sb_global_api_endpoint",
            help=f"API endpoint for {st.session_state.global_ai_provider}. Loaded from secrets ('{base_url_secret_name}') if set, otherwise uses default or this value." if base_url_secret_name else f"API endpoint for {st.session_state.global_ai_provider}. Uses default or this value."
        )

        # API Key - Load from secrets first, then allow user override
        api_key_secret_name = provider_config.get("api_key_secret")
        key_from_secrets = st.secrets.get(api_key_secret_name) if api_key_secret_name else None
        
        # Determine initial value for API key input
        initial_api_key_value = st.session_state.global_api_key # Keep current value if already set
        if not initial_api_key_value and key_from_secrets: # If empty (e.g., provider changed), prefill from secrets
             initial_api_key_value = key_from_secrets
             st.session_state.global_api_key = initial_api_key_value # Update state if prefilled

        api_key_help_text = f"Your API Key for {st.session_state.global_ai_provider}."
        if api_key_secret_name:
            api_key_help_text += f" Loaded from secrets ('{api_key_secret_name}') if set and this field is empty."

        st.session_state.global_api_key = st.text_input(
            f"{st.session_state.global_ai_provider.capitalize()} API Key",
            type="password",
            value=st.session_state.global_api_key, # Use potentially pre-filled value
            key="sb_global_api_key",
            help=api_key_help_text
        )
        
        # Link to get API key (customize per provider)
        # This is a simplified example; a real app might have more specific links.
        api_key_link = f"https://{st.session_state.global_ai_provider}.com/docs/api" # Generic guess
        if st.session_state.global_ai_provider == "openai":
            api_key_link = "https://platform.openai.com/api-keys"
        elif st.session_state.global_ai_provider == "anthropic":
            api_key_link = "https://console.anthropic.com/settings/keys"
        elif st.session_state.global_ai_provider == "groq":
            api_key_link = "https://console.groq.com/keys"
        elif st.session_state.global_ai_provider == "openrouter":
            api_key_link = "https://openrouter.ai/keys"
        elif st.session_state.global_ai_provider == "google":
            api_key_link = "https://aistudio.google.com/app/apikey"

        if provider_config.get("class"): # Only show if it's a configurable provider
            st.markdown(f"<font size='small'>[Get {st.session_state.global_ai_provider.capitalize()} API Key]({api_key_link})</font>", unsafe_allow_html=True)


    # 3. Select AI Model
    if st.session_state.global_ai_provider and provider_config.get("class"):
        with st.spinner(f"Fetching models for {st.session_state.global_ai_provider}..."):
            st.session_state.global_available_models = get_available_models(st.session_state.global_ai_provider)
        
        if not st.session_state.global_available_models or "not found" in st.session_state.global_available_models[0].lower() or "not reachable" in st.session_state.global_available_models[0].lower():
            st.warning(f"Could not fetch models for {st.session_state.global_ai_provider}. Using default or previously selected. Error: {st.session_state.global_available_models[0] if st.session_state.global_available_models else 'Unknown error'}")
            # Fallback to default model from config if list is empty/error
            st.session_state.global_available_models = [provider_config.get("default_model", "default/not-found")]

        # Ensure current model is in the new list, or set to default/first
        if st.session_state.global_ai_model not in st.session_state.global_available_models:
            st.session_state.global_ai_model = provider_config.get("default_model")
            if st.session_state.global_ai_model not in st.session_state.global_available_models:
                 st.session_state.global_ai_model = st.session_state.global_available_models[0] if st.session_state.global_available_models else None
        
        current_model_index = st.session_state.global_available_models.index(st.session_state.global_ai_model) if st.session_state.global_ai_model in st.session_state.global_available_models else 0

        st.session_state.global_ai_model = st.selectbox(
            "Select AI Model",
            options=st.session_state.global_available_models,
            index=current_model_index,
            key="sb_global_ai_model",
            help="Choose the specific AI model to use."
        )
    else:
        st.info("Select a configured AI provider to see model options.")

    # 4. Advanced Settings Expander
    with st.expander("Advanced Settings"):
        st.session_state.global_temperature = st.slider(
            "Temperature",
            min_value=0.0, max_value=1.0,
            value=st.session_state.global_temperature,
            step=0.01,
            key="sb_global_temperature",
            help="Controls randomness. Lower is more deterministic, higher is more creative. Default: 0.30"
        )
        st.session_state.global_max_tokens = st.number_input(
            "Max Tokens",
            min_value=50, max_value=32000, # Adjust max based on typical model limits
            value=st.session_state.global_max_tokens,
            step=128, # Common step for token limits
            key="sb_global_max_tokens",
            help="Maximum number of tokens to generate in the response. Default: 4096"
        )
    
    st.sidebar.divider()

    # Project Status Sidebar
    st.sidebar.subheader("📊 Project Status")
    status_color_map = {
        "Not Started": "⚪",
        "In Progress": "🟡",
        "Completed": "🟢",
        "Error": "🔴"
    }
    st.sidebar.markdown(f"{status_color_map.get(st.session_state.pitch_deck_status, '⚪')} Pitch Deck Analysis: **{st.session_state.pitch_deck_status}**")
    st.sidebar.markdown(f"{status_color_map.get(st.session_state.financial_model_status, '⚪')} Financial Model: **{st.session_state.financial_model_status}**")
    st.sidebar.markdown(f"{status_color_map.get(st.session_state.investor_scout_status, '⚪')} Investor Matches: **{st.session_state.investor_scout_status}**")
    st.sidebar.markdown(f"{status_color_map.get(st.session_state.investor_strategy_status, '⚪')} Investor Strategy: **{st.session_state.investor_strategy_status}**")
    
    st.sidebar.divider()
    st.sidebar.info("Select an agent from the main panel or the navigation above.")


# --- Main Application ---
def main():
    # Custom CSS
    st.markdown("""
    <style>
    .main > div {max-width: 1200px;} /* Adjust main container width */
    h1 {margin-bottom: 1.5rem !important;}
    .stForm > div {border: 1px solid #eee; padding: 1.5rem; border-radius: 5px;}
    /* Add more custom styles as needed from rec.md */
    </style>
    """, unsafe_allow_html=True)

    st.title("Welcome to ainvestor Dashboard 🚀")
    st.markdown("---")

    # Tour Feature Logic
    if st.session_state.get('tour_active', False):
        if st.session_state.tour_step == 0:
            st.info(
                "👋 **Welcome to ainvestor!** Let's take a quick tour. First, please configure your AI Provider in the sidebar (⚙️ AI Configuration). This is essential for using the AI-powered features.",
                icon="🗺️"
            )
            if st.button("Next Tip (AI Config)", key="tour_next_0"):
                st.session_state.tour_step = 1
                st.rerun() # Rerun to show next tip immediately
        
        elif st.session_state.tour_step == 1:
            # Check if AI provider seems configured (basic check)
            ai_configured = st.session_state.get("global_ai_provider") and st.session_state.get("global_ai_model") and (st.session_state.get("global_api_key") or "mock" in st.session_state.get("global_ai_provider","")) # Allow mock provider without key
            if ai_configured:
                 st.success("✅ AI Provider looks configured!", icon="👍")
                 st.info(
                    "Great! Next, fill out your **Startup Profile** below. This information helps tailor the advice from our tools.",
                    icon="📝"
                )
                 if st.button("Next Tip (Startup Profile)", key="tour_next_1"):
                    st.session_state.tour_step = 2
                    st.rerun()
            else:
                st.warning(
                    "Please complete your **AI Configuration** in the sidebar (⚙️). You'll need to select a provider, model, and enter an API key/endpoint if required (unless using a local/mock provider that doesn't need one).",
                    icon="⚙️"
                )

        elif st.session_state.tour_step == 2:
            # Check if startup profile has some data (basic check)
            profile_started = st.session_state.global_startup_profile.get("name") or st.session_state.global_startup_profile.get("industry")
            if profile_started:
                st.success("✅ Startup Profile started!", icon="👍")
                st.info(
                    "Excellent! Now you can **Upload and Analyze your Pitch Deck** directly below on this dashboard.",
                    icon="🚀"
                )
                if st.button("Next Tip (Pitch Deck)", key="tour_next_2"):
                    st.session_state.tour_step = 3
                    st.rerun()
            else:
                 st.info(
                    "Now, please fill in your **Startup Profile** details below and click 'Save Startup Profile'.",
                    icon="📝"
                )
        
        elif st.session_state.tour_step == 3:
            deck_analyzed = st.session_state.get("pda_analysis_results") is not None
            if deck_analyzed:
                st.success("✅ Pitch Deck analyzed!", icon="👍")
                st.info(
                    "Fantastic! You can now explore other tools like **Financial Modeling** or **Investor Scout** from the sidebar/pages menu, or review detailed pitch deck feedback on the **Pitch Deck Advisor** page.",
                    icon="🧭"
                )
                if st.button("End Tour", key="tour_end"):
                    st.session_state.tour_active = False
                    st.session_state.tour_step = -1 # Mark as completed
                    st.success("🎉 Tour complete! You're all set to explore ainvestor.")
                    st.rerun()
            else:
                st.info(
                    "Next, **Upload your Pitch Deck** using the uploader below and click 'Analyze Pitch Deck on Dashboard'.",
                    icon="🚀"
                )
        
        if st.session_state.tour_step >= 0 and st.session_state.tour_active : # Show skip button only during active tour steps
            if st.button("Skip Tour", key="skip_tour_button"):
                st.session_state.tour_active = False
                st.session_state.tour_step = -1 # Mark as completed/skipped
                st.info("Tour skipped. You can always refer to the 'Getting Started' guide below.")
                st.rerun()
        st.markdown("---")


    # Getting Started Guide
    with st.expander("🚀 Getting Started with ainvestor!", expanded=not st.session_state.get('tour_active', True)): # Expand if tour is not active
        st.markdown("""
        ### Welcome to Your AI-Powered Investment Toolkit!
        
        ainvestor is designed to guide you through key stages of preparing for investment:
        
        1.  **Configure AI (⚙️ Sidebar)**:
            *   Select your AI Provider, Model, and enter API key/endpoint if needed. This is crucial for AI-powered features.

        2.  **Define Your Startup Profile (Here on the Dashboard)**:
            *   Fill in your startup's name, industry, stage, funding needs, and USP.
            *   This profile will be used by other tools. Click "Save Startup Profile".

        3.  **Upload & Analyze Pitch Deck (Here on the Dashboard)**:
            *   Use the "Pitch Deck Analysis" section below to upload your deck (PDF or PPTX).
            *   Click "Analyze Pitch Deck on Dashboard". A summary will appear here.
            *   Extracted info can pre-fill your Startup Profile.

        4.  **Review Detailed Feedback (Pitch Deck Advisor Page)**:
            *   Navigate to the "Pitch Deck Advisor" page from the sidebar/menu.
            *   View the full AI-driven feedback and refine sections if needed.
            
        5.  **Financial Modeling (Navigate via Sidebar/Pages Menu)**:
            *   Input key financial assumptions for your startup.
            *   Generate 3-year projections for P&L, Cash Flow, and Balance Sheet.
            *   Use the scenario analysis to see how changes in revenue affect your model.
            *   Your funding needs from the Startup Profile might pre-fill some assumptions.

        4.  **Investor Scout (Navigate via Sidebar/Pages Menu)**:
            *   Define criteria to search for potential investors (industry, stage, investment size).
            *   Search a local database and optionally scrape online platforms (requires AI config).
            *   Information from your pitch deck can pre-fill search criteria.

        5.  **Investor Strategy Agent (Navigate via Sidebar/Pages Menu)**:
            *   Develop an AI-driven strategy for investor outreach.
            *   Optionally use your Startup Profile and investor lists from the Scout tool as context.
            *   Execute the strategy to identify target investors and outreach points.

        **Global AI Configuration (⚙️ Sidebar)**:
        *   Before using AI-powered features in any tool, make sure to select your AI Provider (e.g., OpenAI, Groq, Anthropic), enter your API key/endpoint, and choose a model. These settings apply globally.

        **Project Status (📊 Sidebar)**:
        *   Keep an eye on the sidebar to track your progress through each module.

        Ready to begin? Start by filling out your **Startup Profile** below!
        """)
    st.markdown("---")

    # Pitch Deck Upload and Analysis Section (Moved from Pitch Deck Advisor page)
    st.subheader("🚀 Pitch Deck Analysis")
    
    # Initialize session state keys if they don't exist (might be redundant if already in initialize_global_session_state, but good for clarity here)
    if 'pda_uploaded_file' not in st.session_state:
        st.session_state.pda_uploaded_file = None
    if 'pda_analysis_results' not in st.session_state: # This will store the main feedback
        st.session_state.pda_analysis_results = None
    if 'global_pitch_deck_extracted_info' not in st.session_state: # For structured data
        st.session_state.global_pitch_deck_extracted_info = None

    uploaded_file_dashboard = st.file_uploader(
        "Upload Your Pitch Deck (PDF or PPTX)", 
        type=['pdf', 'pptx'], 
        key='pda_uploaded_file_dashboard_widget', # New key to avoid conflict if old page is cached
        help="Upload your pitch deck here to start the analysis. Results will be available on the 'Pitch Deck Advisor' page."
    )

    if uploaded_file_dashboard is not None:
        st.session_state.pda_uploaded_file = uploaded_file_dashboard # Store in the existing session state var

    if st.session_state.pda_uploaded_file is not None:
        st.success(f"Deck ready for analysis: {st.session_state.pda_uploaded_file.name}")
        
        if st.button("Analyze Pitch Deck on Dashboard", key="analyze_deck_dashboard_button", help="Click to analyze the uploaded pitch deck. This may take a few moments."):
            if not st.session_state.get("global_ai_provider") or not st.session_state.get("global_ai_model"):
                st.error("Please configure the AI Provider and Model in the sidebar under 'AI Configuration'.")
            else:
                with st.spinner(f"Analyzing '{st.session_state.pda_uploaded_file.name}' with {st.session_state.global_ai_provider}..."):
                    try:
                        # Import necessary functions locally within this action block
                        from core import utils as core_utils
                        from core import pitch_deck_logic as core_pitch_deck_logic

                        # 1. Extract text/structure
                        extracted_data = core_utils.parse_pitch_deck(st.session_state.pda_uploaded_file)
                        
                        # 2. Get feedback from LLM
                        # Store raw text globally
                        st.session_state.global_pitch_deck_raw_text = extracted_data.get('raw_full_text', "")

                        feedback = core_pitch_deck_logic.get_deck_feedback_from_llm(
                            extracted_sections_data=extracted_data,
                            provider=st.session_state.global_ai_provider,
                            model=st.session_state.global_ai_model,
                            temperature=st.session_state.get("global_temperature", 0.3),
                            max_tokens=st.session_state.get("global_max_tokens", 4096),
                            api_key=st.session_state.get("global_api_key") or None,
                            base_url=st.session_state.get("global_api_endpoint") or None
                        )
                        st.session_state.pda_analysis_results = feedback # Store full feedback
                        st.session_state.pitch_deck_status = "Analysis Ready" # Update status

                        # 3. Attempt to extract structured data for other agents
                        if extracted_data.get('raw_full_text'):
                            structured_info = core_pitch_deck_logic.extract_structured_data_from_deck_text(
                                full_deck_text=extracted_data['raw_full_text'],
                                provider=st.session_state.global_ai_provider,
                                model=st.session_state.global_ai_model,
                                temperature=st.session_state.get("global_temperature", 0.2),
                                max_tokens=st.session_state.get("global_max_tokens", 2048),
                                api_key=st.session_state.get("global_api_key") or None,
                                base_url=st.session_state.get("global_api_endpoint") or None
                            )
                            if structured_info:
                                st.session_state.global_pitch_deck_extracted_info = structured_info
                                # Auto-fill startup profile if fields are empty
                                profile_updated_by_deck = False
                                if not st.session_state.global_startup_profile.get("name") and structured_info.get("company_name"): # Corrected key
                                    st.session_state.global_startup_profile["name"] = structured_info["company_name"]
                                    profile_updated_by_deck = True
                                
                                if not st.session_state.global_startup_profile.get("industry") and structured_info.get("industry_sector"):
                                    st.session_state.global_startup_profile["industry"] = structured_info["industry_sector"]
                                    profile_updated_by_deck = True
                                if not st.session_state.global_startup_profile.get("stage") and structured_info.get("current_stage"):
                                    st.session_state.global_startup_profile["stage"] = structured_info["current_stage"]
                                    profile_updated_by_deck = True
                                if not st.session_state.global_startup_profile.get("funding_needed") and structured_info.get("funding_ask_amount"): 
                                    st.session_state.global_startup_profile["funding_needed"] = structured_info["funding_ask_amount"]
                                    profile_updated_by_deck = True
                                if not st.session_state.global_startup_profile.get("usp") and structured_info.get("usp"):
                                    st.session_state.global_startup_profile["usp"] = structured_info["usp"]
                                    profile_updated_by_deck = True

                                if profile_updated_by_deck:
                                    st.info("Startup Profile fields have been pre-filled from your pitch deck. Please review and save the profile. You may need to refresh the page or click 'Save Startup Profile' for changes to fully reflect in input fields if they were already rendered.")
                                    st.rerun() # Force a rerun to update the input field values immediately
                                st.success("Pitch deck analyzed successfully! View detailed feedback on the 'Pitch Deck Advisor' page.")
                            else:
                                st.warning("Could not extract structured information from the deck. Full analysis is still available.")
                                st.session_state.global_pitch_deck_extracted_info = None
                        else:
                            st.warning("No text content found in the deck to extract structured information. Full analysis is still available.")
                            st.session_state.global_pitch_deck_extracted_info = None
                        
                        # Display a summary of the analysis on the dashboard
                        if feedback:
                             # Simple summary: first few lines or a specific summary field if available
                            summary_text = feedback.split('\n\n')[0] # Example: take the first paragraph
                            if len(summary_text) > 300: summary_text = summary_text[:300] + "..."
                            st.info(f"**Analysis Summary:** {summary_text} (Full details on 'Pitch Deck Advisor' page)")


                    except ValueError as ve:
                        st.error(f"Error during analysis: {str(ve)}")
                        st.session_state.pda_analysis_results = None
                        st.session_state.global_pitch_deck_extracted_info = None
                        st.session_state.pitch_deck_status = "Error"
                    except Exception as e:
                        st.error(f"An unexpected error occurred: {e}")
                        st.session_state.pda_analysis_results = None
                        st.session_state.global_pitch_deck_extracted_info = None
                        st.session_state.pitch_deck_status = "Error"
    elif st.session_state.pda_analysis_results: # If analysis was done previously
        st.info("Pitch deck has been analyzed. View details on the 'Pitch Deck Advisor' page or upload a new deck.")


    st.markdown("---")

    # Startup Profile Section
    st.subheader("📝 Startup Profile")
    profile_cols = st.columns(2)
    with profile_cols[0]:
        st.session_state.global_startup_profile["name"] = st.text_input(
            "Startup Name", 
            value=st.session_state.global_startup_profile["name"],
            key="profile_name",
            help="Enter the official name of your startup."
        )
        st.session_state.global_startup_profile["industry"] = st.text_input(
            "Industry", 
            value=st.session_state.global_startup_profile["industry"],
            key="profile_industry",
            help="Specify the primary industry your startup operates in (e.g., Fintech, Healthcare, SaaS)."
        )
    with profile_cols[1]:
        st.session_state.global_startup_profile["stage"] = st.selectbox(
            "Startup Stage", 
            options=["Idea", "Pre-Seed", "Seed", "Series A", "Series B+", "Growth"],
            index=["Idea", "Pre-Seed", "Seed", "Series A", "Series B+", "Growth"].index(st.session_state.global_startup_profile["stage"]) if st.session_state.global_startup_profile["stage"] else 0,
            key="profile_stage",
            help="Select the current stage of your startup."
        )
        st.session_state.global_startup_profile["funding_needed"] = st.text_input(
            "Funding Needed (e.g., $500k)", 
            value=st.session_state.global_startup_profile["funding_needed"],
            key="profile_funding",
            help="How much capital are you seeking in this round? (e.g., $500k, €1M)"
        )
    st.session_state.global_startup_profile["usp"] = st.text_area(
        "Unique Selling Proposition (USP)",
        value=st.session_state.global_startup_profile["usp"],
        height=100,
        key="profile_usp",
        help="Briefly describe what makes your startup unique and compelling (1-2 sentences)."
    )
    if st.button("Save Startup Profile", key="save_profile_button", help="Click to save the profile details. This information will be used by other tools."):
        st.success("Startup profile saved!")
        # Potentially trigger updates in other tools or save to a file if needed
    st.markdown("---")


    # Dashboard Overview Section
    st.subheader("📊 Dashboard Overview")
    cols = st.columns(4)
    with cols[0]:
        st.metric("Pitch Deck Status", st.session_state.pitch_deck_status)
    with cols[1]:
        st.metric("Financial Model", st.session_state.financial_model_status) # Placeholder for key metric
    with cols[2]:
        st.metric("Investor Matches", st.session_state.investor_scout_status) # Placeholder for count
    with cols[3]:
        st.metric("Strategy Progress", st.session_state.investor_strategy_status) # Placeholder

    st.markdown("---")
    
    st.subheader("🛠️ Tools & Next Steps")
    st.markdown("""
        Navigate to the different tools using the sidebar or the page navigation above:
        - **Pitch Deck Advisor:** Upload and analyze your pitch deck.
        - **Financial Modeling:** Create and refine your financial projections.
        - **Investor Scout:** Discover and evaluate potential investors.
        - **Investor Strategy Agent:** Develop your investor outreach plan.

        Your AI configurations from the sidebar will be used by all agents.
        The Startup Profile you define here will be accessible across tools.
    """)

    # Display current AI config for user reference (optional)
    # with st.expander("Current AI Configuration (Global)", expanded=False):
    #     st.write(f"**Provider:** {st.session_state.get('global_ai_provider', 'Not set')}")
    #     st.write(f"**Model:** {st.session_state.get('global_ai_model', 'Not set')}")
    #     st.write(f"**Endpoint:** {st.session_state.get('global_api_endpoint', 'Default')}")
    #     st.write(f"**Temperature:** {st.session_state.get('global_temperature', 0.3)}")
    #     st.write(f"**Max Tokens:** {st.session_state.get('global_max_tokens', 4096)}")


if __name__ == "__main__":
    main()
