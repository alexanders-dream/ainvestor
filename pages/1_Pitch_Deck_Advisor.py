import streamlit as st
# from core import pitch_deck_logic
from core import pitch_deck_logic, utils # Import utils
from core.utils import styled_card # Specifically import styled_card
# SUPPORTED_PROVIDERS and get_available_models are now handled globally in app.py

st.set_page_config(page_title="Pitch Deck Advisor", layout="wide")

def initialize_page_session_state():
    """Initializes session state keys specific to the Pitch Deck Advisor page."""
    if 'pda_uploaded_file' not in st.session_state:
        st.session_state.pda_uploaded_file = None
    if 'pda_analysis_results' not in st.session_state:
        st.session_state.pda_analysis_results = None
    if 'pda_refined_section_text' not in st.session_state:
        st.session_state.pda_refined_section_text = None
    # Add a global session state key for extracted info from pitch deck
    if 'global_pitch_deck_extracted_info' not in st.session_state:
        st.session_state.global_pitch_deck_extracted_info = None


initialize_page_session_state()

st.title("Pitch Deck Advisor 💡")
st.markdown("""
This page displays the AI-powered feedback for your pitch deck. 
Upload and analyze your pitch deck on the main **Dashboard** first.
Once analyzed, you can review the full feedback here and optionally refine specific sections.
""")

# --- DISPLAY RESULTS ---
if st.session_state.get('pda_analysis_results'):
    # Ensure pda_analysis_results is a string for markdown display
    analysis_content = st.session_state.pda_analysis_results
    if not isinstance(analysis_content, str):
        analysis_content = str(analysis_content) # Convert if it's not a string

    styled_card(
        title="Analysis Feedback",
        content=st.session_state.pda_analysis_results, # Assuming this is markdown/HTML compatible
        icon="📊"
    )

    with st.expander("Refine a Section (Optional)", expanded=False):
        # Use a form for multiple inputs before action
        with st.form(key="refine_section_form"):
            section_to_refine = st.text_input(
                "Enter section name (e.g., 'Problem Statement')", 
                key="pda_section_name",
                help="Specify the name of the pitch deck section you want to refine (e.g., Market Size, Team)."
            )
            current_text = st.text_area(
                "Paste the current text of this section here", 
                height=150, 
                key="pda_section_text",
                help="Provide the existing text from the section you wish to improve."
            )
            usp_input = st.text_input(
                "What is your startup's Unique Selling Proposition (USP)? (Optional)", 
                key="pda_usp",
                help="If relevant for this section, provide your USP to help the AI tailor the refinement."
            )
            submit_refinement = st.form_submit_button(
                "Refine Section Text",
                help="Click to get AI suggestions for improving the selected section's text."
            )

        if submit_refinement:
            if not section_to_refine or not current_text:
                st.warning("Please provide the section name and its current text to refine.")
            elif not st.session_state.get("global_ai_provider") or not st.session_state.get("global_ai_model"):
                st.error("Please configure the AI Provider and Model in the sidebar under 'AI Configuration'.")
            else:
                with st.spinner("Refining section text..."):
                    try:
                        refined_text_response = pitch_deck_logic.get_section_refinement_from_llm(
                            section_name=section_to_refine,
                            section_text=current_text,
                            startup_usp=usp_input,
                            provider=st.session_state.global_ai_provider,
                            model=st.session_state.global_ai_model,
                            temperature=st.session_state.get("global_temperature", 0.3),
                            max_tokens=st.session_state.get("global_max_tokens", 4096),
                            api_key=st.session_state.get("global_api_key") or None,
                            base_url=st.session_state.get("global_api_endpoint") or None
                        )
                        st.session_state.pda_refined_section_text = refined_text_response
                    except Exception as e:
                        st.error(f"An error occurred during refinement: {e}")
                        st.session_state.pda_refined_section_text = None
        
        if st.session_state.get('pda_refined_section_text'):
            styled_card(
                title="Refined Text Suggestion",
                content=st.session_state.pda_refined_section_text, # Assuming markdown/HTML
                icon="✍️"
            )

    # --- Update Status and Continue Button ---
    # The status is now set to "Analysis Ready" in app.py. 
    # This page can set it to "Completed" if further interaction is deemed necessary,
    # or "Analysis Ready" can be the final status for this tool's main output.
    # For simplicity, we'll assume "Analysis Ready" is sufficient for now.
    # The pre-fill logic for startup profile is now in app.py.
    
    if st.session_state.get('pitch_deck_status') == "Analysis Ready":
        # Optionally, if user interacts with refinement, we could change status.
        # For now, just provide the continue button if analysis is ready.
        st.markdown("---")
        if st.button("➡️ Continue to Financial Modeling", key="pda_continue_to_fm_page"):
            st.info("Navigate to 'Financial Modeling' from the sidebar or top navigation to continue.")
            st.session_state.fm_needs_pitch_deck_data = True 
    
else:
    st.info("No pitch deck analysis found. Please upload and analyze your pitch deck on the main Dashboard.")


st.divider()

# --- TEMPLATE DOWNLOAD ---
st.subheader("Pitch Deck Templates 📝")
st.markdown("Download our recommended pitch deck template to get started.")

try:
    with open("assets/pitch_deck_template_v1.pptx", "rb") as fp:
        btn = st.download_button(
            label="Download Template V1 (PPTX)",
            data=fp,
            file_name="pitch_deck_template_v1.pptx",
            mime="application/vnd.openxmlformats-officedocument.presentationml.presentation"
        )
except FileNotFoundError:
    st.error("Template file 'assets/pitch_deck_template_v1.pptx' not found. Please ensure it exists.")
except Exception as e:
    st.error(f"An error occurred while trying to load the template: {e}")


# To run this page: Ensure Streamlit is run from `app.py`
# The page will be accessible via the Streamlit multipage navigation.
