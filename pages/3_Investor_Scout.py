import streamlit as st
import pandas as pd
from core import investor_scout_logic
from core.utils import styled_card # Import styled_card
# LLM interface for guidance/matching would use global config from app.py's sidebar

st.set_page_config(page_title="Investor Scout", layout="wide")

def initialize_page_session_state():
    """Initializes session state keys specific to the Investor Scout page."""
    if 'is_search_criteria' not in st.session_state:
        st.session_state.is_search_criteria = {} # Initialize empty

    # Pre-fill from global pitch deck info if available
    # This should run once when the page loads or when global_pitch_deck_extracted_info changes and is relevant
    # For simplicity, we'll check here. A more robust solution might use a callback on global_pitch_deck_extracted_info.
    
    default_industry = "Technology"
    default_stage = "Seed"
    default_min_inv = 50000
    default_max_inv = 500000
    default_keywords = ""

    if 'global_pitch_deck_extracted_info' in st.session_state and st.session_state.global_pitch_deck_extracted_info:
        extracted = st.session_state.global_pitch_deck_extracted_info
        default_industry = extracted.get("industry_sector", default_industry)
        default_stage = extracted.get("current_stage", default_stage)
        # funding_ask_amount needs parsing, for now, we'll use keywords
        # For keywords, we can join the list if it exists
        extracted_keywords = extracted.get("keywords_for_investor_search")
        if isinstance(extracted_keywords, list):
            default_keywords = ", ".join(extracted_keywords)
        elif isinstance(extracted_keywords, str):
            default_keywords = extracted_keywords
        
        # Simple parsing for funding_ask_amount (very basic)
        funding_ask_str = extracted.get("funding_ask_amount", "")
        if funding_ask_str:
            try:
                # Remove common currency symbols and suffixes like K, M
                cleaned_ask = funding_ask_str.replace("$", "").replace("€", "").replace("£", "").strip()
                multiplier = 1
                if cleaned_ask.upper().endswith("K"):
                    multiplier = 1000
                    cleaned_ask = cleaned_ask[:-1].strip()
                elif cleaned_ask.upper().endswith("M"):
                    multiplier = 1000000
                    cleaned_ask = cleaned_ask[:-1].strip()
                
                ask_value = int(float(cleaned_ask.replace(",", ""))) * multiplier
                default_min_inv = max(0, ask_value - int(ask_value * 0.5)) # e.g., ask - 50%
                default_max_inv = ask_value + int(ask_value * 0.5)       # e.g., ask + 50%
            except ValueError:
                print(f"Could not parse funding_ask_amount: {funding_ask_str}")


    # Initialize with defaults or pre-filled values
    st.session_state.is_search_criteria.setdefault("industry", default_industry)
    st.session_state.is_search_criteria.setdefault("stage", default_stage)
    st.session_state.is_search_criteria.setdefault("investment_range_min", default_min_inv)
    st.session_state.is_search_criteria.setdefault("investment_range_max", default_max_inv)
    st.session_state.is_search_criteria.setdefault("keywords", default_keywords)

    if 'is_search_results' not in st.session_state:
        st.session_state.is_search_results = None
    if 'is_firecrawl_search_results' not in st.session_state:
        st.session_state.is_firecrawl_search_results = None
    if 'is_combined_search_results' not in st.session_state:
        st.session_state.is_combined_search_results = None


initialize_page_session_state()

st.title("Investor Scout 🔎")
st.markdown("Define your startup's profile to find potential investors. Configure AI provider in the sidebar if LLM features are used.")

# --- SEARCH CRITERIA INPUT ---
with st.expander("Define Your Search Criteria", expanded=True):
    st.subheader("Investor Search Filters") # Reverted to simple subheader for debugging

    # Button to autofill from pitch deck analysis
    if 'global_pitch_deck_extracted_info' in st.session_state and st.session_state.global_pitch_deck_extracted_info:
        if st.button("Autofill Filters from Pitch Deck Analysis", key="is_autofill_from_deck"):
            extracted = st.session_state.global_pitch_deck_extracted_info
            st.session_state.is_search_criteria["industry"] = extracted.get("industry_sector", st.session_state.is_search_criteria.get("industry"))
            st.session_state.is_search_criteria["stage"] = extracted.get("current_stage", st.session_state.is_search_criteria.get("stage"))
            
            keywords_list = extracted.get("keywords_for_investor_search", [])
            if isinstance(keywords_list, list):
                st.session_state.is_search_criteria["keywords"] = ", ".join(keywords_list)
            elif isinstance(keywords_list, str): # Should be a list based on prompt, but handle if string
                st.session_state.is_search_criteria["keywords"] = keywords_list
            else:
                st.session_state.is_search_criteria["keywords"] = st.session_state.is_search_criteria.get("keywords","")


            funding_ask_str = extracted.get("funding_ask_amount", "")
            if funding_ask_str:
                try:
                    cleaned_ask = funding_ask_str.replace("$", "").replace("€", "").replace("£", "").strip()
                    multiplier = 1
                    if cleaned_ask.upper().endswith("K"):
                        multiplier = 1000
                        cleaned_ask = cleaned_ask[:-1].strip()
                    elif cleaned_ask.upper().endswith("M"):
                        multiplier = 1000000
                        cleaned_ask = cleaned_ask[:-1].strip()
                    ask_value = int(float(cleaned_ask.replace(",", ""))) * multiplier
                    st.session_state.is_search_criteria["investment_range_min"] = max(0, ask_value - int(ask_value * 0.5))
                    st.session_state.is_search_criteria["investment_range_max"] = ask_value + int(ask_value * 0.5)
                except ValueError:
                    # Keep existing values if parsing fails
                    st.session_state.is_search_criteria["investment_range_min"] = st.session_state.is_search_criteria.get("investment_range_min", 50000)
                    st.session_state.is_search_criteria["investment_range_max"] = st.session_state.is_search_criteria.get("investment_range_max", 500000)
            
            st.success("Search filters autofilled from pitch deck analysis. Please review.")
            st.rerun() # Rerun to update widget values from changed session_state.is_search_criteria

    # Use a form for inputs
    with st.form(key="investor_search_form"):
        # Mock data for dropdowns
        INDUSTRIES = ["Technology", "Healthcare", "Fintech", "Consumer Goods", "Energy", "Real Estate", "Education", "Other"]
        STAGES = ["Pre-Seed", "Seed", "Series A", "Series B", "Series C+", "Angel", "Other"]

        # Inputs (no columns for debugging)
        current_industry = st.session_state.is_search_criteria.get("industry", "Technology")
        if current_industry not in INDUSTRIES: current_industry = "Other"
        industry_index = INDUSTRIES.index(current_industry)
        # search_industry variable is not used later, value is read from st.session_state.is_industry_sb
        st.selectbox(
            "Industry Focus", 
            INDUSTRIES, 
            index=industry_index, 
            key="is_industry_sb",
            help="Select the primary industry focus for your investor search."
        )
        
        current_stage = st.session_state.is_search_criteria.get("stage", "Seed")
        if current_stage not in STAGES: current_stage = "Other"
        stage_index = STAGES.index(current_stage)
        # search_stage variable is not used later
        st.selectbox(
            "Investment Stage", 
            STAGES, 
            index=stage_index, 
            key="is_stage_sb",
            help="Select the investment stage you are targeting (e.g., Seed, Series A)."
        )

        # search_min_investment variable is not used later for its value, only for max_investment's min_value
        # We will read from session_state for max_investment's min_value
        st.number_input(
            "Minimum Desired Investment ($)",
            min_value=0,
            value=st.session_state.is_search_criteria.get("investment_range_min", 50000),
            step=10000, 
            key="is_min_inv_ni",
            help="Enter the minimum investment amount you are looking for from an investor."
        )
        
        # Ensure is_min_inv_ni is in session_state before accessing for max_investment's min_value
        min_investment_for_max = st.session_state.get("is_min_inv_ni", 0)

        st.number_input(
            "Maximum Desired Investment ($)",
            min_value=min_investment_for_max, 
            value=max(min_investment_for_max, st.session_state.is_search_criteria.get("investment_range_max", 500000)),
            step=50000, 
            key="is_max_inv_ni",
            help="Enter the maximum investment amount you are looking for from an investor."
        )

        # search_keywords variable is not used later
        st.text_input(
            "Keywords (e.g., SaaS, AI, B2B, specific market)",
            value=st.session_state.is_search_criteria.get("keywords", ""),
            key="is_keywords_ti",
            help="Enter relevant keywords to refine your search (comma-separated, e.g., impact investing, edtech, Africa focus)."
        )
        
        # search_online_platforms variable is not used later
        st.checkbox(
            "Search Online Investor Platforms (e.g., African Angel Network, VC4A - requires Firecrawl & LLM)", 
            value=False, 
            key="is_search_online_cb",
            help="Enable to search online investor databases and websites. This uses Firecrawl and an LLM, and may take longer."
        )
        
        # custom_urls_to_scrape variable is not used later
        st.text_area(
            "Additional URLs to scrape (one per line, optional):", 
            height=75, 
            key="is_custom_urls_ta", 
            help="If searching online, you can add specific websites (one URL per line) to scrape for investor information."
        )

        submitted_search = st.form_submit_button("Find Investors", help="Click to search for investors based on the criteria you've defined.")

if submitted_search:
    # Update session state.is_search_criteria with the submitted form values from their respective widget keys
    st.session_state.is_search_criteria["industry"] = st.session_state.is_industry_sb
    st.session_state.is_search_criteria["stage"] = st.session_state.is_stage_sb
    st.session_state.is_search_criteria["investment_range_min"] = st.session_state.is_min_inv_ni
    st.session_state.is_search_criteria["investment_range_max"] = st.session_state.is_max_inv_ni
    st.session_state.is_search_criteria["keywords"] = st.session_state.is_keywords_ti
    # search_online_platforms and custom_urls_to_scrape are also in session_state via their keys
    # 'is_search_online_cb' and 'is_custom_urls_ta'

    # Reset previous results
    st.session_state.is_search_results = pd.DataFrame()
    st.session_state.is_firecrawl_search_results = pd.DataFrame()
    st.session_state.is_combined_search_results = pd.DataFrame()

    with st.spinner("Searching for investors (Local DB)..."):
        try:
            db_results_df = investor_scout_logic.find_investors(
                industry=st.session_state.is_search_criteria["industry"],
                stage=st.session_state.is_search_criteria["stage"],
                min_investment=st.session_state.is_search_criteria["investment_range_min"],
                max_investment=st.session_state.is_search_criteria["investment_range_max"],
                keywords=st.session_state.is_search_criteria["keywords"]
            )
            st.session_state.is_search_results = db_results_df
            if not db_results_df.empty:
                st.success(f"Found {len(db_results_df)} potential investors from local database!")
            else:
                st.info("No investors found matching your criteria in the local database.")
        except FileNotFoundError:
            st.error(f"Local investor database not found. Please ensure '{investor_scout_logic.INVESTOR_DB_PATH}' exists.")
        except Exception as e:
            st.error(f"An error occurred during local DB search: {e}")

    # Use the value from session state for search_online_platforms
    if st.session_state.is_search_online_cb:
        if not st.session_state.get("global_ai_provider") or not st.session_state.get("global_ai_model"):
            st.error("AI Provider and Model must be configured in the sidebar to search online platforms.")
        else:
            with st.spinner("Searching online platforms with Firecrawl & LLM... This may take some time."):
                try:
                    target_urls_input = []
                    # Use the value from session state for custom_urls_to_scrape
                    if st.session_state.is_custom_urls_ta:
                        target_urls_input.extend([url.strip() for url in st.session_state.is_custom_urls_ta.splitlines() if url.strip()])
                    
                    # If no custom URLs, it will use the default AFRICAN_INVESTOR_PLATFORMS from the logic file
                    # Or, you could explicitly pass AFRICAN_INVESTOR_PLATFORMS if target_urls_input is empty.
                    # For now, find_investors_firecrawl defaults to AFRICAN_INVESTOR_PLATFORMS if target_urls is None or empty.

                    firecrawl_results_df = investor_scout_logic.find_investors_firecrawl(
                        target_urls=target_urls_input if target_urls_input else None, # Pass None to use default list in logic
                        provider=st.session_state.global_ai_provider,
                        model=st.session_state.global_ai_model,
                        temperature=st.session_state.get("global_temperature", 0.1),
                        max_tokens=st.session_state.get("global_max_tokens", 3000)
                    )
                    st.session_state.is_firecrawl_search_results = firecrawl_results_df
                    if not firecrawl_results_df.empty:
                        st.success(f"Found {len(firecrawl_results_df)} potential investors/mentions from online platforms!")
                    else:
                        st.info("No additional investors found from online platforms based on scraping.")
                except Exception as e:
                    st.error(f"An error occurred during online platform search: {e}")
    
    # Combine results
    final_results_list = []
    if not st.session_state.is_search_results.empty:
        # Add a source column to DB results if it doesn't exist
        if 'source_platform' not in st.session_state.is_search_results.columns:
            st.session_state.is_search_results['source_platform'] = 'Local Database'
        final_results_list.append(st.session_state.is_search_results)
        
    if not st.session_state.is_firecrawl_search_results.empty:
        final_results_list.append(st.session_state.is_firecrawl_search_results)
    
    if final_results_list:
        st.session_state.is_combined_search_results = pd.concat(final_results_list, ignore_index=True)
        # Optional: Deduplicate based on name and website_url if available
        if 'name' in st.session_state.is_combined_search_results.columns and 'website_url' in st.session_state.is_combined_search_results.columns:
            st.session_state.is_combined_search_results = st.session_state.is_combined_search_results.drop_duplicates(subset=['name', 'website_url'], keep='first')
        elif 'name' in st.session_state.is_combined_search_results.columns:
            st.session_state.is_combined_search_results = st.session_state.is_combined_search_results.drop_duplicates(subset=['name'], keep='first')

# --- DISPLAY RESULTS ---
combined_results_df = st.session_state.get('is_combined_search_results')
if combined_results_df is not None and not combined_results_df.empty:
    styled_card(
        title="Potential Investor Matches",
        content="", # DataFrame will be displayed below
        icon="🎯"
    )
    st.dataframe(combined_results_df)
    
    try:
        csv = combined_results_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Combined Results as CSV",
            data=csv,
            file_name='combined_investor_matches.csv',
            mime='text/csv',
            key='is_download_combined_csv'
        )
    except Exception as e:
        st.error(f"Could not prepare CSV for download: {e}")
elif submitted_search: # Only show if a search was attempted
    st.info("No investors found matching your criteria from any source.")

# --- Update Status and Continue Button ---
if combined_results_df is not None and not combined_results_df.empty:
    st.session_state.investor_scout_status = "Completed" # Update status
    st.success("Investor Scouting complete!")
    
    if st.button("➡️ Continue to Investor Strategy", key="is_continue_to_strategy"):
        st.info("Navigate to 'Investor Strategy Agent' from the sidebar or top navigation to continue.")
        st.session_state.strategy_needs_investor_data = True 
        if 'selected_investors_df' not in st.session_state or st.session_state.selected_investors_df is None:
            st.session_state.selected_investors_df = combined_results_df 
        elif st.session_state.selected_investors_df is not None: # if it exists, append new results if they are different
            # This simple concat might lead to duplicates if search is run multiple times with overlaps
            # A more robust approach would be to merge and deduplicate based on a unique investor ID or name/website
            st.session_state.selected_investors_df = pd.concat([st.session_state.selected_investors_df, combined_results_df]).drop_duplicates(subset=['name', 'website_url'] if 'name' in combined_results_df.columns and 'website_url' in combined_results_df.columns else ['name'] if 'name' in combined_results_df.columns else None, keep='last').reset_index(drop=True)


elif submitted_search and (combined_results_df is None or combined_results_df.empty):
    st.session_state.investor_scout_status = "Completed (No Results)"
    if st.button("➡️ Continue to Investor Strategy (with no matches)", key="is_continue_to_strategy_no_match"):
        st.info("Navigate to 'Investor Strategy Agent' from the sidebar or top navigation to continue. You can manually input investor details there.")
        st.session_state.strategy_needs_investor_data = False
        if 'selected_investors_df' in st.session_state:
            del st.session_state.selected_investors_df
