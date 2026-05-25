import streamlit as st
import pandas as pd # Import pandas for DataFrame check
from core import investor_strategy_logic
from core.utils import styled_card # Import styled_card
from core.yaml_utils import parse_uploaded_yaml_file, create_investor_strategy_template
from prompts import investor_strategy_prompts

st.set_page_config(page_title="Investor Strategy Agent", layout="wide")

st.title("🤖 Investor Strategy Agent")
st.caption("Develop and execute AI-driven strategies to find relevant investors.")

# --- Session State Initialization ---
def initialize_investor_strategy_state():
    if 'isa_strategy_defined' not in st.session_state:
        st.session_state.isa_strategy_defined = False
    if 'isa_execution_results' not in st.session_state:
        st.session_state.isa_execution_results = None

    default_profile = {
        "industry": "", "stage": "Seed", "funding_needed": "", "usp": ""
    }
    default_market_trends = ""
    default_investor_preferences = ""

    if 'global_pitch_deck_extracted_info' in st.session_state and st.session_state.global_pitch_deck_extracted_info:
        extracted = st.session_state.global_pitch_deck_extracted_info
        default_profile["industry"] = extracted.get("industry_sector", default_profile["industry"])
        default_profile["stage"] = extracted.get("current_stage", default_profile["stage"])
        default_profile["funding_needed"] = extracted.get("funding_ask_amount", default_profile["funding_needed"])
        default_profile["usp"] = extracted.get("usp", default_profile["usp"])

        # Use extracted keywords for market trends as a starting point
        extracted_keywords = extracted.get("keywords_for_investor_search")
        if isinstance(extracted_keywords, list):
            default_market_trends = "Considered keywords from pitch deck: " + ", ".join(extracted_keywords)
        elif isinstance(extracted_keywords, str) and extracted_keywords:
            default_market_trends = "Considered keywords from pitch deck: " + extracted_keywords


    if 'isa_startup_profile' not in st.session_state:
        st.session_state.isa_startup_profile = default_profile
    else: # If already exists, update with defaults if empty (e.g. after a reset or if user clears them)
        for key, value in default_profile.items():
            st.session_state.isa_startup_profile.setdefault(key, value)

    if 'isa_market_trends' not in st.session_state:
        st.session_state.isa_market_trends = default_market_trends
    else:
        st.session_state.isa_market_trends = st.session_state.isa_market_trends or default_market_trends


    if 'isa_investor_preferences' not in st.session_state:
        st.session_state.isa_investor_preferences = default_investor_preferences

initialize_investor_strategy_state()

st.info("The Investor Strategy Agent helps you define a plan to find investors and then executes it using AI and web search capabilities. Configure your AI provider globally in the sidebar (⚙️ AI Configuration).", icon="💡")

# --- 1. Define Strategy ---
with st.expander("1. Define Your Investor Search Strategy", expanded=True):
    styled_card(
        title="Strategy Definition Inputs",
        content="<p>Define your startup profile and market focus below. You can also autofill details from your analyzed pitch deck.</p>", 
        icon="📝"
    )
    
    # Autofill from Pitch Deck button (now primary way to autofill this section)
    has_pitch_deck_data = 'global_pitch_deck_extracted_info' in st.session_state and st.session_state.global_pitch_deck_extracted_info is not None
    if st.button(
        "Autofill from Pitch Deck Analysis", 
        disabled=not has_pitch_deck_data,
        help="Populate strategy inputs using information extracted from your pitch deck (if analyzed on the Dashboard)."
    ):
        if has_pitch_deck_data:
            extracted = st.session_state.global_pitch_deck_extracted_info
            st.session_state.isa_startup_profile["industry"] = extracted.get("industry_sector", st.session_state.isa_startup_profile.get("industry", ""))
            st.session_state.isa_startup_profile["stage"] = extracted.get("current_stage", st.session_state.isa_startup_profile.get("stage", "Seed"))
            st.session_state.isa_startup_profile["funding_needed"] = extracted.get("funding_ask_amount", st.session_state.isa_startup_profile.get("funding_needed", ""))
            st.session_state.isa_startup_profile["usp"] = extracted.get("usp", st.session_state.isa_startup_profile.get("usp", ""))
            extracted_keywords = extracted.get("keywords_for_investor_search")
            if isinstance(extracted_keywords, list) and extracted_keywords:
                st.session_state.isa_market_trends = "Considered keywords from pitch deck: " + ", ".join(extracted_keywords)
            elif isinstance(extracted_keywords, str) and extracted_keywords:
                st.session_state.isa_market_trends = "Considered keywords from pitch deck: " + extracted_keywords
            st.success("Form autofilled with data from your pitch deck analysis!")
            st.rerun() # Rerun to update widget values
        else:
            st.warning("No pitch deck data available. Please upload and analyze a pitch deck on the Dashboard first.")

    st.subheader("Startup Profile")
    col1, col2 = st.columns(2)
    # Define STAGES list once
    STAGES_LIST = ["Pre-Seed", "Seed", "Series A", "Series B+", "Growth", "Idea", "MVP", "Other"]

    with col1:
        st.session_state.isa_startup_profile['industry'] = st.text_input(
            "Industry/Sector",
            value=st.session_state.isa_startup_profile.get('industry', ""), 
            key="isa_profile_industry_ti",
            help="Your startup's primary industry or sector."
        )

        current_stage_isa = st.session_state.isa_startup_profile.get('stage', "Seed")
        if current_stage_isa not in STAGES_LIST and current_stage_isa: 
            STAGES_LIST.append(current_stage_isa) 
            STAGES_LIST = sorted(list(set(STAGES_LIST))) 

        stage_index_isa = STAGES_LIST.index(current_stage_isa) if current_stage_isa in STAGES_LIST else 0

        st.session_state.isa_startup_profile['stage'] = st.selectbox(
            "Startup Stage",
            options=STAGES_LIST, 
            index=stage_index_isa,
            key="isa_profile_stage_sb",
            help="Current stage of your startup (e.g., Seed, Series A)."
        )
    with col2:
        st.session_state.isa_startup_profile['funding_needed'] = st.text_input(
            "Desired Investment (e.g., $500k - $2M)",
            value=st.session_state.isa_startup_profile.get('funding_needed', ""), 
            key="isa_profile_funding_ti",
            help="The range or amount of funding you are seeking."
        )
        st.session_state.isa_startup_profile['usp'] = st.text_area(
            "Unique Selling Proposition (USP) / Key Differentiators",
            value=st.session_state.isa_startup_profile.get('usp', ""), 
            height=100,
            key="isa_profile_usp_ta",
            help="What makes your startup stand out? What are your key competitive advantages?"
        )

    st.subheader("Market & Investor Focus")

    # Display selected investors from Investor Scout if available
    if 'selected_investors_df' in st.session_state and \
       st.session_state.selected_investors_df is not None and \
       not st.session_state.selected_investors_df.empty:
        # This section is no longer an expander to avoid nesting issues
        st.markdown("---") # Add a separator
        st.markdown("##### Investors Identified by Investor Scout")
        st.markdown("The following investors were identified by the Investor Scout tool and can be considered in your strategy:")
        st.dataframe(st.session_state.selected_investors_df, height=200)
        st.caption("This list will be provided as context to the AI when developing the strategy.")
        st.markdown("---") # Add a separator

    st.session_state.isa_market_trends = st.text_area(
        "Key Market Trends to Consider (Optional)",
        value=st.session_state.isa_market_trends, 
        height=100,
        key="isa_market_trends_input_ta",
        help="List any significant market trends that might influence investor interest or your strategy."
    )
    st.session_state.isa_investor_preferences = st.text_area(
        "Specific Investor Preferences or Exclusions (Optional, e.g., 'focus on impact investors', 'exclude VCs from X region')",
        value=st.session_state.isa_investor_preferences, 
        height=100,
        key="isa_investor_preferences_input_ta",
        help="Specify any types of investors you are particularly targeting or wish to avoid."
    )

    if st.button("🧠 Develop Strategy with AI", type="primary", help="Click to use AI to generate a tailored investor search strategy based on your inputs."):
        if not st.session_state.isa_startup_profile.get('industry') or not st.session_state.isa_startup_profile.get('stage'):
            st.warning("Please provide at least Industry and Startup Stage.")
        else:
            with st.spinner("AI is crafting your investor search strategy..."):
                if not st.session_state.get("global_ai_provider") or not st.session_state.get("global_ai_model"):
                    st.error("Please configure the AI Provider and Model in the sidebar under 'AI Configuration'.")
                else:
                    try:
                        selected_investors_context = None
                        if 'selected_investors_df' in st.session_state and \
                           st.session_state.selected_investors_df is not None and \
                           not st.session_state.selected_investors_df.empty:
                            selected_investors_context = st.session_state.selected_investors_df.to_dict(orient='records')

                        st.session_state.isa_generated_strategy = investor_strategy_logic.develop_strategy_with_llm(
                            profile=st.session_state.isa_startup_profile,
                            market_trends=st.session_state.isa_market_trends,
                            investor_preferences=st.session_state.isa_investor_preferences,
                            # Pass selected investors as new context if available
                            selected_investors=selected_investors_context, 
                            llm_provider=st.session_state.global_ai_provider,
                            llm_model=st.session_state.global_ai_model,
                            temperature=st.session_state.get("global_temperature", 0.3),
                            max_tokens=st.session_state.get("global_max_tokens", 4096),
                            api_key=st.session_state.get("global_api_key") or None,
                            base_url=st.session_state.get("global_api_endpoint") or None
                        )
                        st.session_state.isa_strategy_defined = True
                        st.success("Investor search strategy developed!")
                    except Exception as e:
                        st.error(f"Error developing strategy: {e}")
                        st.session_state.isa_generated_strategy = None

if st.session_state.isa_strategy_defined and "isa_generated_strategy" in st.session_state:
    strategy = st.session_state.isa_generated_strategy
    
    # Display Summary and Outreach Angle (Editable Text Areas for refinement)
    st.subheader("Review & Refine Strategy")
    
    col_strat_1, col_strat_2 = st.columns(2)
    with col_strat_1:
        st.markdown("**Strategy Summary**")
        st.info(strategy.get('summary', 'Not available.'))
    with col_strat_2:
        new_outreach = st.text_area("Outreach Angle", value=strategy.get('outreach_angle', ''))
        strategy['outreach_angle'] = new_outreach

    # Editable Keywords and Data Sources
    col_edit_1, col_edit_2 = st.columns(2)
    with col_edit_1:
         st.markdown("**Search Keywords (Editable)**")
         KEYWORDS_KEY = "isa_editable_keywords"
         # Initialize session state for data editor if needed, or just use key
         current_keywords = strategy.get('keywords_for_search', [])
         if not isinstance(current_keywords, list): current_keywords = []
         
         # Using a simple text area for easier list editing by user (lines) or data_editor
         # Data editor is cleaner for lists
         df_keywords = pd.DataFrame({"Keywords": current_keywords})
         edited_df_keywords = st.data_editor(df_keywords, num_rows="dynamic", key="keywords_editor", use_container_width=True)
         strategy['keywords_for_search'] = edited_df_keywords["Keywords"].tolist() # Update strategy

    with col_edit_2:
        st.markdown("**Data Sources (Editable)**")
        current_sources = strategy.get('data_sources_to_check', [])
        if not isinstance(current_sources, list): current_sources = []
        
        df_sources = pd.DataFrame({"Data Sources": current_sources})
        edited_df_sources = st.data_editor(df_sources, num_rows="dynamic", key="sources_editor", use_container_width=True)
        strategy['data_sources_to_check'] = edited_df_sources["Data Sources"].tolist()

    # Update session state
    st.session_state.isa_generated_strategy = strategy

    # --- 2. Execute Strategy ---
    st.header("2. Execute Strategy & Find Investors")
    
    # Configuration for execution
    with st.expander("Search Configuration", expanded=False):
        max_scrapes = st.slider("Max Search Results to Scrape per Keyword", min_value=1, max_value=5, value=2, help="Higher values check more results but cost more credits and take longer.")
    
    if st.button("🚀 Execute Strategy", type="primary", disabled=not st.session_state.isa_strategy_defined, help="Click to execute the strategy using the refined keywords above."):
        with st.spinner(f"AI is searching for investors (checking top {max_scrapes} results per keyword)..."):
            if not st.session_state.get("global_ai_provider") or not st.session_state.get("global_ai_model"):
                 st.error("Please configure the AI Provider and Model in the sidebar under 'AI Configuration' to use AI for search execution.")
            else:
                try:
                    st.session_state.isa_execution_results = investor_strategy_logic.execute_investor_search(
                        strategy=st.session_state.isa_generated_strategy,
                        firecrawl_client=None, # Will be initialized in logic
                        llm_provider=st.session_state.global_ai_provider,
                        llm_model=st.session_state.global_ai_model,
                        max_scrapes_per_keyword=max_scrapes,
                        temperature=st.session_state.get("global_temperature", 0.3),
                        max_tokens=st.session_state.get("global_max_tokens", 4096),
                        api_key=st.session_state.get("global_api_key") or None,
                        base_url=st.session_state.get("global_api_endpoint") or None
                    )
                    st.success("Investor search complete!")
                except Exception as e:
                    st.error(f"Error executing search: {e}")
                    st.session_state.isa_execution_results = None

# --- 3. Review Results ---
if st.session_state.isa_execution_results:
    results_df_isa = pd.DataFrame(st.session_state.isa_execution_results) if isinstance(st.session_state.isa_execution_results, list) else st.session_state.isa_execution_results
    
    results_content = f"<p>Found {len(results_df_isa) if results_df_isa is not None else 0} potential investors.</p>"
    # The dataframe itself will be displayed outside the card for better rendering.
    styled_card(
        title="Investor Search Results",
        content=results_content,
        icon="🔍"
    )
    
    if results_df_isa is not None and not results_df_isa.empty:
        st.dataframe(results_df_isa)
        csv_export_isa = results_df_isa.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Strategy Results as CSV",
            data=csv_export_isa,
            file_name="investor_strategy_results.csv",
            mime="text/csv",
            key="isa_download_strategy_results_csv"
        )
    elif st.session_state.isa_execution_results is not None: 
        st.info("The investor strategy execution did not yield any specific investor matches based on the current criteria.")

    if st.session_state.isa_execution_results is not None: 
        st.session_state.investor_strategy_status = "Completed"
        st.success("Investor Strategy process complete!")
        if st.button("🎉 Mark Project as Complete & Review Dashboard", type="primary", key="isa_mark_project_complete"):
            st.info("All steps completed! Review your project status on the main Dashboard.")

st.sidebar.markdown("---")
st.sidebar.markdown("Developed by AInvestor Team")

# Placeholder for actual logic imports and calls
# Ensure llm_interface.py is updated and core/investor_strategy_logic.py is created.
