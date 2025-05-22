import streamlit as st
import pandas as pd
import json # Added for JSON display
from io import BytesIO # For excel export

from core import financial_model_logic # Existing
from core.llm_interface import LLMInterface
from core.business_understanding_logic import BusinessUnderstandingLogic
from core.model_structuring_logic import ModelStructuringLogic
from core.assumption_engine import AssumptionEngine # Added
from core.formula_logic_engine import FormulaLogicEngine # Added
from core.scenario_analysis_engine import ScenarioAnalysisEngine # Added
from core.model_validation_engine import ModelValidationEngine # Added
from core.interpretation_engine import InterpretationEngine
from core.utils import styled_card
from core.yaml_utils import dump_yaml as dump_yaml_util, load_yaml as load_yaml_util # For saving/loading assumptions
# LLM interface for guidance/tips would use global config from app.py's sidebar

# --- Initialize LLM and Business Logic ---
# This should ideally be done once, perhaps cached or in a central app setup.
# For simplicity in this page, we initialize here.
# Ensure API keys are set in environment variables if using cloud LLMs.
try:
    if 'llm_interface' not in st.session_state:
        st.session_state.llm_interface = LLMInterface()
    llm = st.session_state.llm_interface
except Exception as e:
    st.error(f"Critical Error: Failed to initialize LLM Interface: {e}. Ensure API key is configured. The page cannot proceed.")
    st.stop() # Stop execution if LLM can't load

try:
    if 'bu_logic' not in st.session_state:
        st.session_state.bu_logic = BusinessUnderstandingLogic(llm_interface=llm)
    bu_logic = st.session_state.bu_logic # Business Understanding Logic
except Exception as e:
    st.error(f"Critical Error: Failed to initialize Business Understanding Logic: {e}. The page cannot proceed.")
    st.stop()

try:
    if 'ms_logic' not in st.session_state:
        st.session_state.ms_logic = ModelStructuringLogic(llm_interface=llm) # Model Structuring Logic
    ms_logic = st.session_state.ms_logic # Model Structuring Logic
except Exception as e:
    st.error(f"Critical Error: Failed to initialize Model Structuring Logic: {e}. The page cannot proceed.")
    st.stop()

try:
    if 'ae_logic' not in st.session_state:
        st.session_state.ae_logic = AssumptionEngine(llm_interface=llm) # Assumption Engine Logic
    ae = st.session_state.ae_logic # Assumption Engine Logic
except Exception as e:
    st.error(f"Critical Error: Failed to initialize Assumption Engine: {e}. The page cannot proceed.")
    st.stop()

try:
    if 'fle_logic' not in st.session_state:
        st.session_state.fle_logic = FormulaLogicEngine(llm_interface=llm) # Formula Logic Engine
    fle = st.session_state.fle_logic # Formula Logic Engine
except Exception as e:
    st.error(f"Critical Error: Failed to initialize Formula Logic Engine: {e}. The page cannot proceed.")
    st.stop()

try:
    if 'sae_logic' not in st.session_state:
        st.session_state.sae_logic = ScenarioAnalysisEngine(llm_interface=llm) # Scenario Analysis Engine
    sae = st.session_state.sae_logic # Scenario Analysis Engine
except Exception as e:
    st.error(f"Critical Error: Failed to initialize Scenario Analysis Engine: {e}. The page cannot proceed.")
    st.stop()

try:
    if 'mve_logic' not in st.session_state:
        st.session_state.mve_logic = ModelValidationEngine(llm_interface=llm) # Model Validation Engine
    mve = st.session_state.mve_logic # Model Validation Engine
except Exception as e:
    st.error(f"Critical Error: Failed to initialize Model Validation Engine: {e}. The page cannot proceed.")
    st.stop()

try:
    if 'ie_logic' not in st.session_state:
        st.session_state.ie_logic = InterpretationEngine(llm_interface=llm) # Interpretation Engine
    ie = st.session_state.ie_logic
except Exception as e:
    st.error(f"Critical Error: Failed to initialize Interpretation Engine: {e}. The page cannot proceed.")
    st.stop()


st.set_page_config(page_title="Financial Modeling", layout="wide")

# --- Default Values Constants ---
DEFAULT_REVENUE_Y1 = 100000
DEFAULT_REVENUE_GROWTH_Y2 = 0.20
DEFAULT_REVENUE_GROWTH_Y3 = 0.15
DEFAULT_COGS_PERCENT = 0.40
DEFAULT_OPEX_Y1 = 30000
DEFAULT_OPEX_GROWTH_Y2 = 0.10
DEFAULT_OPEX_GROWTH_Y3 = 0.05
DEFAULT_TAX_RATE = 0.21
DEFAULT_INTEREST_EXPENSE = 1000
DEFAULT_DEPRECIATION_AMORTIZATION = 5000
DEFAULT_CHANGE_IN_WORKING_CAPITAL = 2000
DEFAULT_CAPITAL_EXPENDITURES = 10000
DEFAULT_DEBT_RAISED_REPAID = 0
DEFAULT_EQUITY_ISSUED_REPURCHASED = 0
DEFAULT_INITIAL_CASH_BALANCE = 50000
DEFAULT_INITIAL_ACCOUNTS_RECEIVABLE = 15000
DEFAULT_INITIAL_INVENTORY = 10000
DEFAULT_INITIAL_ACCOUNTS_PAYABLE = 8000
DEFAULT_INITIAL_PPE = 75000
DEFAULT_INITIAL_ACCUMULATED_DEPRECIATION = 10000
DEFAULT_INITIAL_LONG_TERM_DEBT = 20000
DEFAULT_INITIAL_EQUITY = 112000 # Derived: Assets(50+15+10+(75-10)=140) - Liab(8+20=28) = 112

# Map for percentage inputs: main fm_inputs key to widget key prefix
PERCENTAGE_KEYS_INFO = {
    "revenue_growth_y2": "fm_revenue_growth_y2",
    "revenue_growth_y3": "fm_revenue_growth_y3",
    "cogs_percent": "fm_cogs_percent",
    "opex_growth_y2": "fm_opex_growth_y2",
    "opex_growth_y3": "fm_opex_growth_y3",
    "tax_rate": "fm_tax_rate"
}

# --- Callback functions for synchronized percentage inputs (will be used outside the form) ---
def create_sync_callbacks(main_input_key_in_fm_inputs, widget_key_prefix):
    """Helper to create a pair of sync callback functions."""
    slider_display_key = f"{widget_key_prefix}_slider_display"
    text_display_key = f"{widget_key_prefix}_text_display"

    def _sync_from_slider():
        # Update main fm_inputs key (0.0-1.0)
        st.session_state.fm_inputs[main_input_key_in_fm_inputs] = st.session_state[slider_display_key] / 100.0
        # Update the text display key to match slider
        st.session_state[text_display_key] = st.session_state[slider_display_key]

    def _sync_from_text():
        # Update main fm_inputs key (0.0-1.0)
        st.session_state.fm_inputs[main_input_key_in_fm_inputs] = st.session_state[text_display_key] / 100.0
        # Update the slider display key to match text
        st.session_state[slider_display_key] = st.session_state[text_display_key]
    
    return _sync_from_slider, _sync_from_text

# Create callbacks for each percentage input
# These will be assigned to widgets outside the form
sync_rev_g2_slider, sync_rev_g2_text = create_sync_callbacks("revenue_growth_y2", PERCENTAGE_KEYS_INFO["revenue_growth_y2"])
sync_rev_g3_slider, sync_rev_g3_text = create_sync_callbacks("revenue_growth_y3", PERCENTAGE_KEYS_INFO["revenue_growth_y3"])
sync_cogs_slider, sync_cogs_text = create_sync_callbacks("cogs_percent", PERCENTAGE_KEYS_INFO["cogs_percent"])
sync_opex_g2_slider, sync_opex_g2_text = create_sync_callbacks("opex_growth_y2", PERCENTAGE_KEYS_INFO["opex_growth_y2"])
sync_opex_g3_slider, sync_opex_g3_text = create_sync_callbacks("opex_growth_y3", PERCENTAGE_KEYS_INFO["opex_growth_y3"])
sync_tax_slider, sync_tax_text = create_sync_callbacks("tax_rate", PERCENTAGE_KEYS_INFO["tax_rate"])


def initialize_page_session_state():
    """Initializes session state keys specific to the Financial Modeling page."""
    if 'fm_inputs' not in st.session_state:
        # Initialize with default values or ensure they are set before use
        st.session_state.fm_inputs = {
            "revenue_y1": DEFAULT_REVENUE_Y1, "revenue_growth_y2": DEFAULT_REVENUE_GROWTH_Y2, "revenue_growth_y3": DEFAULT_REVENUE_GROWTH_Y3,
            "cogs_percent": DEFAULT_COGS_PERCENT,
            "opex_y1": DEFAULT_OPEX_Y1, "opex_growth_y2": DEFAULT_OPEX_GROWTH_Y2, "opex_growth_y3": DEFAULT_OPEX_GROWTH_Y3,
            "tax_rate": DEFAULT_TAX_RATE,
            "interest_expense": DEFAULT_INTEREST_EXPENSE,
            "depreciation_amortization": DEFAULT_DEPRECIATION_AMORTIZATION,
            "change_in_working_capital": DEFAULT_CHANGE_IN_WORKING_CAPITAL,
            "capital_expenditures": DEFAULT_CAPITAL_EXPENDITURES,
            "debt_raised_repaid": DEFAULT_DEBT_RAISED_REPAID,
            "equity_issued_repurchased": DEFAULT_EQUITY_ISSUED_REPURCHASED,
            "initial_cash_balance": DEFAULT_INITIAL_CASH_BALANCE,
            "initial_accounts_receivable": DEFAULT_INITIAL_ACCOUNTS_RECEIVABLE,
            "initial_inventory": DEFAULT_INITIAL_INVENTORY,
            "initial_accounts_payable": DEFAULT_INITIAL_ACCOUNTS_PAYABLE,
            "initial_ppe": DEFAULT_INITIAL_PPE,
            "initial_accumulated_depreciation": DEFAULT_INITIAL_ACCUMULATED_DEPRECIATION,
            "initial_long_term_debt": DEFAULT_INITIAL_LONG_TERM_DEBT,
            "initial_equity": DEFAULT_INITIAL_EQUITY
        }
    # Initialize display-specific keys for percentage inputs (0-100 range)
    for main_key, widget_key_prefix in PERCENTAGE_KEYS_INFO.items():
        slider_display_key = f"{widget_key_prefix}_slider_display"
        text_display_key = f"{widget_key_prefix}_text_display"
        if slider_display_key not in st.session_state:
            st.session_state[slider_display_key] = st.session_state.fm_inputs[main_key] * 100
        if text_display_key not in st.session_state:
            st.session_state[text_display_key] = st.session_state.fm_inputs[main_key] * 100
            
    if 'fm_financial_statements' not in st.session_state:
        st.session_state.fm_financial_statements = None
    if 'fm_scenario_revenue_sensitivity' not in st.session_state:
        st.session_state.fm_scenario_revenue_sensitivity = 0 # Changed to integer 0

    # --- Session State for Business Understanding ---
    if 'business_assumptions' not in st.session_state:
        st.session_state.business_assumptions = None # Will store dict from BU logic
    if 'bu_conversation_history' not in st.session_state: # For chat display
        st.session_state.bu_conversation_history = []
    if 'current_bu_question' not in st.session_state:
        st.session_state.current_bu_question = None
    if 'pitch_deck_text_input' not in st.session_state:
        st.session_state.pitch_deck_text_input = ""

    # --- Session State for Model Structuring ---
    if 'model_structure_suggestion' not in st.session_state:
        st.session_state.model_structure_suggestion = None # Stores AI's full suggestion
    if 'selected_template_id' not in st.session_state:
        st.session_state.selected_template_id = None # User's final choice
    if 'final_model_structure' not in st.session_state: # Will hold components & KPIs for the chosen model
        st.session_state.final_model_structure = None

    # --- Session State for Assumption Guidance ---
    if 'assumption_guidance_texts' not in st.session_state: # Dict to store guidance for multiple fields
        st.session_state.assumption_guidance_texts = {}
    if 'assumption_review_feedback' not in st.session_state:
        st.session_state.assumption_review_feedback = None
    if 'proceed_after_review' not in st.session_state: # Flag to control generation after review
        st.session_state.proceed_after_review = False

    # --- Session State for Formula/Logic Explanations ---
    if 'formula_explanation_topic' not in st.session_state:
        st.session_state.formula_explanation_topic = "" # User input for topic
    if 'formula_explanation_output' not in st.session_state: # Stores the AI's explanation
        st.session_state.formula_explanation_output = None
    if 'interdependency_explanation_output' not in st.session_state:
        st.session_state.interdependency_explanation_output = None

    # --- Session State for Scenario Analysis Suggestions ---
    if 'scenario_variable_suggestions' not in st.session_state:
        st.session_state.scenario_variable_suggestions = None

    # --- Session State for Model Validation ---
    if 'model_reasonableness_feedback' not in st.session_state:
        st.session_state.model_reasonableness_feedback = None

    # --- Session State for Interpretation & Presentation ---
    if 'kpi_to_explain' not in st.session_state:
        st.session_state.kpi_to_explain = None
    if 'kpi_explanation_output' not in st.session_state:
        st.session_state.kpi_explanation_output = None
    if 'financial_summary_narrative' not in st.session_state:
        st.session_state.financial_summary_narrative = None


initialize_page_session_state()

st.title("AI-Guided Financial Modeling 💰") # Title updated
st.markdown("Input your key assumptions to generate basic 3-year financial projections. Configure AI provider in the sidebar if LLM guidance features are used.")

# --- 1. Business Understanding & Contextualization ---
with st.expander("Step 1: Understand Your Business 📝", expanded=True):
    st.subheader("A. Load Business Context from Dashboard")
    st.markdown("""
    If you have analyzed your pitch deck on the main dashboard, the extracted structured information 
    can be loaded here to kickstart the business understanding process for financial modeling.
    """)

    if st.button("Load Business Info from Dashboard Analysis", key="load_bu_from_dashboard_btn"):
        structured_info = st.session_state.get("global_pitch_deck_extracted_info")
        if structured_info and isinstance(structured_info, dict):
            with st.spinner("Loading and processing structured business info..."):
                try:
                    # Reset previous BU state before new loading
                    st.session_state.business_assumptions = None
                    st.session_state.current_bu_question = None
                    st.session_state.bu_logic.reset_conversation() # Reset history in logic

                    # Use the new method in BusinessUnderstandingLogic
                    initialized_assumptions = bu_logic.initialize_assumptions_from_structured_data(structured_info)
                    
                    if initialized_assumptions:
                        st.session_state.business_assumptions = initialized_assumptions
                        st.success("Business information loaded and initialized successfully from dashboard analysis!")
                        
                        # Immediately try to get a clarification question based on the loaded assumptions
                        question = bu_logic.get_clarification_question(st.session_state.business_assumptions)
                        st.session_state.current_bu_question = question
                        st.session_state.bu_conversation_history = bu_logic.get_full_conversation_history()
                    else:
                        st.error("Failed to initialize business assumptions from the structured data.")
                except Exception as e:
                    st.error(f"An error occurred during loading/processing: {e}")
        else:
            st.warning("No structured business information found from dashboard analysis. Please analyze your pitch deck on the main dashboard first.")

    # The rest of the logic for displaying assumptions and handling clarifications remains largely the same,
    # but it now operates on st.session_state.business_assumptions which can be populated by the new button.
    if st.session_state.business_assumptions:
        st.subheader("B. Review Loaded/Updated Assumptions & Clarify")
        st.json(st.session_state.business_assumptions)

        # Display conversation history (simplified)
        # for msg in st.session_state.get("bu_conversation_history", []):
        #     if msg["role"] == "assistant" and "Extracted data:" not in msg["content"] and "Updated assumptions:" not in msg["content"]:
        #         st.info(f"AI: {msg['content']}") # AI questions
        #     elif msg["role"] == "user":
        #         st.text_input("Your previous answer:", value=msg['content'], disabled=True, key=f"hist_user_{len(st.session_state.bu_conversation_history)}_{msg['content'][:10]}")


        if st.session_state.current_bu_question:
            st.info(f"AI Clarification: {st.session_state.current_bu_question}")
            user_clarification_response = st.text_input(
                "Your answer:",
                key="user_bu_clarification_response_area"
            )
            if st.button("Submit Clarification", key="submit_bu_clarification_btn"):
                if user_clarification_response and st.session_state.business_assumptions:
                    with st.spinner("AI is processing your answer..."):
                        try:
                            updated_assumptions = bu_logic.update_assumptions_with_user_response(
                                st.session_state.business_assumptions,
                                user_clarification_response
                            )
                            if updated_assumptions:
                                st.session_state.business_assumptions = updated_assumptions
                                st.success("Business assumptions updated!")
                                # Ask another question or conclude
                                new_question = bu_logic.get_clarification_question(updated_assumptions)
                                st.session_state.current_bu_question = new_question
                                st.session_state.bu_conversation_history = bu_logic.get_full_conversation_history()

                                # Clear the input box by rerunning
                                st.rerun()
                            else:
                                st.error("Could not update assumptions based on your response.")
                        except Exception as e:
                            st.error(f"An error occurred during update: {e}")
                else:
                    st.warning("Please provide an answer to the clarification question.")
        elif st.session_state.business_assumptions and not st.session_state.current_bu_question:
             st.success("Step 1: Business Understanding seems complete based on the current AI assessment!")
             st.markdown("---") # Visual separator

# --- 2. Model Structuring & Template Suggestion ---
# This section activates after business assumptions are stable (no pending BU questions)
if st.session_state.get("business_assumptions") and not st.session_state.get("current_bu_question"):
    with st.expander("Step 2: Define Model Structure 🏗️", expanded=True):
        st.write("Based on your business information, the AI can suggest a suitable financial model template.")

        if st.button("Suggest Model Structure", key="suggest_model_structure_btn"):
            with st.spinner("AI is thinking about the best model structure..."):
                try:
                    suggestion = ms_logic.suggest_model_template(st.session_state.business_assumptions)
                    if suggestion:
                        st.session_state.model_structure_suggestion = suggestion
                        # Pre-select the AI's recommendation if valid
                        if suggestion.get("recommended_template_id") in ms_logic.get_available_templates_summary():
                            st.session_state.selected_template_id = suggestion.get("recommended_template_id")
                        elif ms_logic.get_available_templates_summary(): # if recommendation is bad, pick first available
                            st.session_state.selected_template_id = list(ms_logic.get_available_templates_summary().keys())[0]
                        st.success("AI has suggested a model structure.")
                    else:
                        st.error("AI could not generate a model structure suggestion at this time.")
                except Exception as e:
                    st.error(f"Error suggesting model structure: {e}")

        if st.session_state.model_structure_suggestion:
            suggestion = st.session_state.model_structure_suggestion
            st.subheader("AI Suggestion:")
            st.markdown(f"**Recommended Template:** `{suggestion.get('recommended_template_id', 'N/A')}`")
            st.info(f"**Reasoning:** {suggestion.get('reasoning', 'No reasoning provided.')}")
            
            if suggestion.get("alternative_template_ids"):
                st.markdown(f"**Alternative Templates:** `{(', '.join(suggestion.get('alternative_template_ids')))}`")
            
            st.markdown("**Essential Model Components Suggested:**")
            if suggestion.get("essential_components"):
                for comp in suggestion.get("essential_components"):
                    st.markdown(f"- {comp}")
            
            st.markdown("**Suggested Key Performance Indicators (KPIs):**")
            if suggestion.get("suggested_kpis"):
                for kpi in suggestion.get("suggested_kpis"):
                    st.markdown(f"- {kpi}")
            else:
                st.markdown("_No specific KPIs suggested by AI, consider standard ones for the chosen template._")
            st.markdown("---")

        # Allow user to select or override
        available_templates_summary = ms_logic.get_available_templates_summary()
        template_options = {id: f"{name} ({id})" for id, name in available_templates_summary.items()}
        
        # Ensure selected_template_id is valid, default if not
        if not st.session_state.get("selected_template_id") and available_templates_summary:
             st.session_state.selected_template_id = list(available_templates_summary.keys())[0]


        selected_id = st.selectbox(
            "Choose your financial model template:",
            options=list(template_options.keys()),
            format_func=lambda id: template_options[id],
            index=list(template_options.keys()).index(st.session_state.selected_template_id) if st.session_state.selected_template_id in template_options else 0,
            key="template_select_dropdown"
        )
        st.session_state.selected_template_id = selected_id


        if st.session_state.selected_template_id:
            template_details = ms_logic.get_template_details(st.session_state.selected_template_id)
            if template_details:
                st.subheader(f"Details for: {template_details['name']}")
                st.markdown(f"**Description:** {template_details['description']}")
                st.markdown("**Standard Components:**")
                for comp in template_details.get("components", []):
                    st.markdown(f"- {comp}")
                st.markdown("**Default KPIs:**")
                for kpi in template_details.get("default_kpis", []):
                    st.markdown(f"- {kpi}")

                if st.button("Confirm Model Structure", key="confirm_model_structure_btn"):
                    # Store the final structure based on the selected template's details
                    # And potentially merge with AI's suggested KPIs if they are more specific
                    final_struct = {
                        "template_id": st.session_state.selected_template_id,
                        "template_name": template_details["name"],
                        "components": template_details.get("components", []),
                        "kpis": template_details.get("default_kpis", [])
                    }
                    # If AI suggested KPIs and they are different, consider adding them or letting user choose
                    ai_suggested_kpis = st.session_state.model_structure_suggestion.get("suggested_kpis", [])
                    if ai_suggested_kpis and set(ai_suggested_kpis) != set(final_struct["kpis"]):
                        # Simple merge: add AI KPIs if not already present
                        for kpi in ai_suggested_kpis:
                            if kpi not in final_struct["kpis"]:
                                final_struct["kpis"].append(kpi)
                        # Could add a note here that KPIs were merged/updated from AI suggestion
                    
                    st.session_state.final_model_structure = final_struct
                    st.success(f"Model structure confirmed using '{template_details['name']}' template.")
                    st.json(st.session_state.final_model_structure) # Display the final structure
                    st.markdown("---")


# --- Sidebar Elements ---
st.sidebar.subheader("Model Actions")

# Save Assumptions
if 'fm_inputs' in st.session_state:
    try:
        assumptions_yaml_str = dump_yaml_util(st.session_state.fm_inputs)
        st.sidebar.download_button(
            label="Save Assumptions (YAML)",
            data=assumptions_yaml_str,
            file_name="financial_model_assumptions.yaml",
            mime="application/x-yaml",
            key="fm_download_assumptions_yaml"
        )
    except Exception as e:
        st.sidebar.error(f"Error preparing assumptions for download: {e}")

# Load Assumptions
uploaded_assumptions_file = st.sidebar.file_uploader(
    "Load Assumptions (YAML)", 
    type=["yaml", "yml"],
    key="fm_upload_assumptions_yaml"
)

if uploaded_assumptions_file is not None:
    try:
        bytes_data = uploaded_assumptions_file.getvalue()
        yaml_str_content = bytes_data.decode('utf-8')
        loaded_assumptions = load_yaml_util(yaml_str_content)

        if loaded_assumptions and isinstance(loaded_assumptions, dict):
            # Validate loaded assumptions against expected keys (optional but good practice)
            # For now, directly update fm_inputs
            st.session_state.fm_inputs = loaded_assumptions
            
            # IMPORTANT: Update individual display keys for percentages and form inputs
            # This ensures the UI reflects the loaded data correctly.
            for main_key, widget_key_prefix in PERCENTAGE_KEYS_INFO.items():
                slider_display_key = f"{widget_key_prefix}_slider_display"
                text_display_key = f"{widget_key_prefix}_text_display"
                if main_key in loaded_assumptions:
                    st.session_state[slider_display_key] = loaded_assumptions[main_key] * 100
                    st.session_state[text_display_key] = loaded_assumptions[main_key] * 100
            
            # For non-percentage inputs that are part of the form, fm_inputs is the source of truth.
            # We might need to trigger a rerun or ensure form defaults pick up new fm_inputs values.
            # For inputs outside the form but directly using fm_inputs (like the guidance display), they should update.
            
            st.sidebar.success("Assumptions loaded successfully!")
            st.rerun() # Rerun to reflect loaded values in all widgets
        elif loaded_assumptions is None and yaml_str_content.strip() == "":
            st.sidebar.warning("Uploaded assumptions file is empty.")
        else:
            st.sidebar.error("Failed to parse YAML or invalid assumptions structure.")
            if loaded_assumptions is not None: # It parsed but wasn't a dict
                 st.sidebar.info(f"Loaded data type: {type(loaded_assumptions)}")


    except Exception as e:
        st.sidebar.error(f"Error loading assumptions: {e}")
    finally:
        # Reset the uploader to allow re-uploading the same file if needed after an error
        # This can be tricky with Streamlit's default file_uploader behavior.
        # A common workaround is to change its key, but that's complex here.
        # For now, user might need to upload a different file or refresh if error.
        pass


st.sidebar.divider()
st.sidebar.subheader("Scenario Analysis")
# Existing Revenue Sensitivity Slider
st.session_state.fm_scenario_revenue_sensitivity = st.sidebar.slider(
    "Revenue Sensitivity (+/- %)",
    min_value=-50, max_value=50,
    value=st.session_state.fm_scenario_revenue_sensitivity,
    step=1, format="%d%%",
    key="fm_rev_sensitivity_slider",
    help="Adjust overall Year 1 Revenue to see its impact on projections. This is a simple sensitivity test."
)

# AI Suggestions for Scenario Variables
st.sidebar.markdown("---")
st.sidebar.markdown("**AI Guidance for Scenarios:**")
if st.sidebar.button("Suggest Key Variables for Scenarios", key="suggest_scenario_vars_btn"):
    if st.session_state.get("business_assumptions") and \
       st.session_state.get("final_model_structure") and \
       st.session_state.get("fm_inputs"):
        with st.spinner("AI is thinking of impactful variables..."):
            try:
                suggestions = sae.suggest_scenario_variables(
                    business_assumptions=st.session_state.business_assumptions,
                    model_structure=st.session_state.final_model_structure,
                    financial_assumptions=st.session_state.fm_inputs
                )
                st.session_state.scenario_variable_suggestions = suggestions
            except Exception as e:
                st.sidebar.error(f"Error getting suggestions: {e}")
                st.session_state.scenario_variable_suggestions = ["Failed to get suggestions."]
    else:
        st.sidebar.warning("Please complete Steps 1, 2, and input initial assumptions in Step 3 first.")

if st.session_state.get("scenario_variable_suggestions"):
    st.sidebar.markdown("**Consider testing scenarios with:**")
    for suggestion in st.session_state.scenario_variable_suggestions:
        st.sidebar.caption(f"- {suggestion}")
st.sidebar.markdown("_(Note: The slider above only tests Year 1 Revenue. For other variables, you'd currently need to adjust them in Step 3 and regenerate.)_")


# --- INPUTS WIZARD (Now part of Step 3) ---
# This section will be wrapped by "Step 3" expander logic further down.

# The actual input fields will be defined within the "Step 3" expander,
# which only appears if st.session_state.final_model_structure is set.

# Placeholder for where the main financial inputs form will be defined.
# The existing st.subheader("Key Assumptions (3-Year Projection)") and subsequent form
# will be moved/nested under the Step 3 expander.


# --- Step 3: Input Financial Assumptions with AI Guidance ---
if st.session_state.get("final_model_structure"):
    with st.expander("Step 3: Input Financial Assumptions 📊", expanded=True):
        st.markdown("Now, let's input the core financial numbers for your model. AI can provide guidance and benchmarks for key assumptions.")
        st.markdown(f"You've selected the **'{st.session_state.final_model_structure['template_name']}'** model structure.")
        st.markdown(f"Key components to consider: {', '.join(st.session_state.final_model_structure['components'])}")
        st.markdown(f"Key KPIs to track: {', '.join(st.session_state.final_model_structure['kpis'])}")
        st.markdown("---")

        # The existing input form and logic will be placed here.
        # For now, let's ensure the structure is correct.
        # The original "Key Assumptions (3-Year Projection)" subheader and form will go here.

        # --- Original Input Form Starts Here (Moved into Step 3) ---
        st.subheader("Key Assumptions (3-Year Projection)")

        # Attempt to pre-fill from global_startup_profile if available and if inputs haven't been set by user yet
# This is a simple pre-fill, more sophisticated logic might be needed for specific fields
if 'global_startup_profile' in st.session_state and st.session_state.global_startup_profile:
    profile = st.session_state.global_startup_profile
    # Example: Pre-fill revenue_y1 if funding_needed is available and looks like a number
    if profile.get("funding_needed") and isinstance(profile["funding_needed"], (str, int, float)):
        try:
            # Attempt to parse funding_needed (e.g., "$500k", "1M")
            # This is a very basic parser, a more robust one would be needed for production
            funding_str = str(profile["funding_needed"]).lower().replace('$', '').replace(',', '')
            multiplier = 1
            if 'k' in funding_str:
                multiplier = 1000
                funding_str = funding_str.replace('k', '')
            elif 'm' in funding_str:
                multiplier = 1000000
                funding_str = funding_str.replace('m', '')
            
            parsed_funding = float(funding_str) * multiplier
            
            # Heuristic: If revenue_y1 is still at its default and funding is available,
            # set revenue_y1 to a multiple of funding (e.g., 2x funding as a starting point)
            # This is a placeholder heuristic and should be refined based on typical startup scenarios.
            if st.session_state.fm_inputs.get("revenue_y1") == DEFAULT_REVENUE_Y1: # Check against constant
                 st.session_state.fm_inputs["revenue_y1"] = int(parsed_funding * 0.5) # Example: Y1 revenue is 50% of funding needed
                 st.info(f"Pre-filled Year 1 Revenue based on funding needed ({profile['funding_needed']}). Please review and adjust.")
        except ValueError:
            pass # Could not parse funding_needed, skip pre-fill for revenue

# --- Interactive Percentage Inputs (Outside Form) ---
st.subheader("Growth Rates & Percentages")
interactive_cols = st.columns(3)

with interactive_cols[0]: # Revenue Growth Rates
    st.write("Year 2 Revenue Growth")
    rev_g2_cols = st.columns([3, 1])
    with rev_g2_cols[0]:
        st.slider("Year 2 Revenue Growth Slider", min_value=0.0, max_value=100.0, step=1.0, format="%.0f%%", 
                  key=f"{PERCENTAGE_KEYS_INFO['revenue_growth_y2']}_slider_display", 
                  on_change=sync_rev_g2_slider,
                  help="Expected year-over-year revenue growth rate for Year 2 (0-100%).", label_visibility="collapsed")
    with rev_g2_cols[1]:
        st.number_input("Y2 Rev Growth Text", min_value=0.0, max_value=100.0, step=0.1, format="%.1f",
                        key=f"{PERCENTAGE_KEYS_INFO['revenue_growth_y2']}_text_display", 
                        on_change=sync_rev_g2_text,
                        label_visibility="collapsed")

    st.write("Year 3 Revenue Growth")
    rev_g3_cols = st.columns([3, 1])
    with rev_g3_cols[0]:
        st.slider("Year 3 Revenue Growth Slider", min_value=0.0, max_value=100.0, step=1.0, format="%.0f%%",
                  key=f"{PERCENTAGE_KEYS_INFO['revenue_growth_y3']}_slider_display", 
                  on_change=sync_rev_g3_slider,
                  help="Expected year-over-year revenue growth rate for Year 3 (0-100%).", label_visibility="collapsed")
    with rev_g3_cols[1]:
        st.number_input("Y3 Rev Growth Text", min_value=0.0, max_value=100.0, step=0.1, format="%.1f",
                        key=f"{PERCENTAGE_KEYS_INFO['revenue_growth_y3']}_text_display", 
                        on_change=sync_rev_g3_text,
                        label_visibility="collapsed")

with interactive_cols[1]: # Costs & Expenses Percentages
    st.write("COGS (% of Revenue)")
    field_key_cogs = "cogs_percent"
    # Layout: Slider and Text Input in one row, AI tip button and guidance in the next.
    cogs_input_cols = st.columns([3, 1]) # For slider and text input
    with cogs_input_cols[0]:
        st.slider(
            "COGS Slider", min_value=0.0, max_value=100.0, step=1.0, format="%.0f%%",
            key=f"{PERCENTAGE_KEYS_INFO[field_key_cogs]}_slider_display",
            on_change=sync_cogs_slider,
            help="Cost of Goods Sold as a percentage of total revenue.", label_visibility="collapsed"
        )
    with cogs_input_cols[1]:
        st.number_input(
            "COGS Text", min_value=0.0, max_value=100.0, step=0.1, format="%.1f",
            key=f"{PERCENTAGE_KEYS_INFO[field_key_cogs]}_text_display",
            on_change=sync_cogs_text,
            label_visibility="collapsed"
        )
    
    # AI Tip button and guidance display for COGS
    if st.button("💡 AI Tip", key=f"guidance_btn_{field_key_cogs}", help="Get AI guidance for COGS %."):
        if st.session_state.business_assumptions and st.session_state.final_model_structure:
            with st.spinner("Fetching AI guidance..."):
                # For percentage inputs, the value in fm_inputs is 0.0-1.0, but display is 0-100.
                # The LLM prompt expects the value as the user sees it (0-100).
                current_cogs_display_val = st.session_state.get(f"{PERCENTAGE_KEYS_INFO[field_key_cogs]}_text_display", DEFAULT_COGS_PERCENT * 100)
                guidance = ae.get_guidance_for_assumption_field(
                    assumption_field_key=field_key_cogs,
                    current_value=f"{current_cogs_display_val}%", # Pass as percentage string
                    business_assumptions=st.session_state.business_assumptions,
                    model_structure=st.session_state.final_model_structure
                )
                st.session_state.assumption_guidance_texts[field_key_cogs] = guidance
        else:
            st.session_state.assumption_guidance_texts[field_key_cogs] = "Please complete Step 1 & 2 for contextual guidance."
    
    if st.session_state.assumption_guidance_texts.get(field_key_cogs):
        st.caption(f"💡 {st.session_state.assumption_guidance_texts[field_key_cogs]}")


    st.write("Year 2 OpEx Growth")
    opex_g2_cols = st.columns([3,1])
    with opex_g2_cols[0]:
        st.slider("Year 2 OpEx Growth Slider", min_value=0.0, max_value=100.0, step=1.0, format="%.0f%%",
                  key=f"{PERCENTAGE_KEYS_INFO['opex_growth_y2']}_slider_display", 
                  on_change=sync_opex_g2_slider,
                  help="Expected growth rate for operating expenses in Year 2 (0-100%).", label_visibility="collapsed")
    with opex_g2_cols[1]:
        st.number_input("Y2 OpEx Growth Text", min_value=0.0, max_value=100.0, step=0.1, format="%.1f",
                        key=f"{PERCENTAGE_KEYS_INFO['opex_growth_y2']}_text_display", 
                        on_change=sync_opex_g2_text,
                        label_visibility="collapsed")

    st.write("Year 3 OpEx Growth")
    opex_g3_cols = st.columns([3,1])
    with opex_g3_cols[0]:
        st.slider("Year 3 OpEx Growth Slider", min_value=0.0, max_value=100.0, step=1.0, format="%.0f%%",
                  key=f"{PERCENTAGE_KEYS_INFO['opex_growth_y3']}_slider_display", 
                  on_change=sync_opex_g3_slider,
                  help="Expected growth rate for operating expenses in Year 3 (0-100%).", label_visibility="collapsed")
    with opex_g3_cols[1]:
        st.number_input("Y3 OpEx Growth Text", min_value=0.0, max_value=100.0, step=0.1, format="%.1f",
                        key=f"{PERCENTAGE_KEYS_INFO['opex_growth_y3']}_text_display", 
                        on_change=sync_opex_g3_text,
                        label_visibility="collapsed")

with interactive_cols[2]: # Other Percentages
    st.write("Tax Rate")
    tax_cols = st.columns([3,1])
    with tax_cols[0]:
        st.slider("Tax Rate Slider", min_value=0.0, max_value=100.0, step=1.0, format="%.0f%%",
                  key=f"{PERCENTAGE_KEYS_INFO['tax_rate']}_slider_display", 
                  on_change=sync_tax_slider,
                  help="Effective corporate tax rate on profits (0-100%).", label_visibility="collapsed")
    with tax_cols[1]:
        st.number_input("Tax Rate Text", min_value=0.0, max_value=100.0, step=0.1, format="%.1f",
                        key=f"{PERCENTAGE_KEYS_INFO['tax_rate']}_text_display", 
                        on_change=sync_tax_text,
                        label_visibility="collapsed")

st.divider() # Separator before the form

# --- AI Guidance for Form Inputs (Displayed outside form) ---
st.markdown("#### AI Guidance for Key Values")

# Guidance for Year 1 Revenue
field_key_rev_y1 = "revenue_y1"
current_rev_y1_val_for_tip = st.session_state.fm_inputs.get(field_key_rev_y1, DEFAULT_REVENUE_Y1)
# Display label for context, as the input itself is inside the form
st.markdown(f"**Year 1 Revenue ($)**: Guidance for the value currently set at `${current_rev_y1_val_for_tip:,.0f}`")
if st.button("💡 AI Tip", key=f"guidance_btn_{field_key_rev_y1}_outside_form", help="Get AI guidance for Year 1 Revenue."):
    if st.session_state.business_assumptions and st.session_state.final_model_structure:
        with st.spinner("Fetching AI guidance..."):
            guidance = ae.get_guidance_for_assumption_field(
                assumption_field_key=field_key_rev_y1,
                current_value=current_rev_y1_val_for_tip, 
                business_assumptions=st.session_state.business_assumptions,
                model_structure=st.session_state.final_model_structure
            )
            st.session_state.assumption_guidance_texts[field_key_rev_y1] = guidance
    else:
        st.session_state.assumption_guidance_texts[field_key_rev_y1] = "Please complete Step 1 & 2 for contextual guidance."

if st.session_state.assumption_guidance_texts.get(field_key_rev_y1):
    st.caption(f"💡 {st.session_state.assumption_guidance_texts[field_key_rev_y1]}")

# Guidance for Year 1 Operating Expenses
field_key_opex_y1 = "opex_y1"
current_opex_y1_val_for_tip = st.session_state.fm_inputs.get(field_key_opex_y1, DEFAULT_OPEX_Y1)
st.markdown(f"**Year 1 Operating Expenses ($)**: Guidance for the value currently set at `${current_opex_y1_val_for_tip:,.0f}`")
if st.button("💡 AI Tip", key=f"guidance_btn_{field_key_opex_y1}_outside_form", help="Get AI guidance for Year 1 OpEx."):
    if st.session_state.business_assumptions and st.session_state.final_model_structure:
        with st.spinner("Fetching AI guidance..."):
            guidance = ae.get_guidance_for_assumption_field(
                assumption_field_key=field_key_opex_y1,
                current_value=current_opex_y1_val_for_tip,
                business_assumptions=st.session_state.business_assumptions,
                model_structure=st.session_state.final_model_structure
            )
            st.session_state.assumption_guidance_texts[field_key_opex_y1] = guidance
    else:
        st.session_state.assumption_guidance_texts[field_key_opex_y1] = "Please complete Step 1 & 2 for contextual guidance."

if st.session_state.assumption_guidance_texts.get(field_key_opex_y1):
    st.caption(f"💡 {st.session_state.assumption_guidance_texts[field_key_opex_y1]}")

st.divider() # Visually separate this guidance section from the form below

# Use a form for remaining inputs to prevent reruns on each widget change until submission
with st.form(key="financial_assumptions_form"):
    st.subheader("Core Financial Values & Other Assumptions") # Changed subheader
    # Group inputs for better layout
    form_input_cols = st.columns(3) # Renamed to avoid conflict
    with form_input_cols[0]: # Was input_cols[0]
        st.subheader("Revenue")
        field_key_rev_y1 = "revenue_y1"
        current_rev_y1_val = st.session_state.fm_inputs.get(field_key_rev_y1, DEFAULT_REVENUE_Y1)
        st.session_state.fm_inputs[field_key_rev_y1] = st.number_input(
            "Year 1 Revenue ($)", 
            min_value=0, 
            value=current_rev_y1_val, 
            step=1000, 
            key="fm_rev_y1_form", 
            help="Projected total revenue for the first full year of operation."
        )
        # AI Tip button and caption for revenue_y1 are now outside the form
        # Percentage inputs for revenue growth are now outside the form

    with form_input_cols[1]: # Was input_cols[1]
        st.subheader("Costs & Expenses")
        # COGS % is now outside the form
        field_key_opex_y1 = "opex_y1"
        current_opex_y1_val = st.session_state.fm_inputs.get(field_key_opex_y1, DEFAULT_OPEX_Y1)
        st.session_state.fm_inputs[field_key_opex_y1] = st.number_input(
            "Year 1 Operating Expenses ($)", 
            min_value=0, 
            value=current_opex_y1_val, 
            step=1000, 
            key="fm_opex_y1_form", 
            help="Total operating expenses (e.g., salaries, rent, marketing) for Year 1, excluding COGS."
        )
        # AI Tip button and caption for opex_y1 are now outside the form
        # OpEx growth percentages are now outside the form

    with form_input_cols[2]: # Was input_cols[2]
        st.subheader("Other Financial Inputs") # Redundant?
        # Tax Rate is now outside the form
        st.session_state.fm_inputs["interest_expense"] = st.number_input("Annual Interest Expense ($)", min_value=0, value=st.session_state.fm_inputs.get("interest_expense", DEFAULT_INTEREST_EXPENSE), step=100, key="fm_interest_form", help="Projected annual interest paid on debt.")
        st.session_state.fm_inputs["depreciation_amortization"] = st.number_input("Annual Depreciation & Amortization ($)", min_value=0, value=st.session_state.fm_inputs.get("depreciation_amortization", DEFAULT_DEPRECIATION_AMORTIZATION), step=500, key="fm_da_form", help="Annual non-cash expense for depreciation of assets and amortization of intangibles.")

    st.divider()
    st.subheader("Cash Flow & Balance Sheet Assumptions (Annual)") # This subheader is fine
    cf_bs_cols = st.columns(3)
    with cf_bs_cols[0]:
        st.session_state.fm_inputs["change_in_working_capital"] = st.number_input("Change in Net Working Capital ($)", value=st.session_state.fm_inputs.get("change_in_working_capital", DEFAULT_CHANGE_IN_WORKING_CAPITAL), step=500, help="Annual change in (Current Assets - Current Liabilities). Positive for increase (cash outflow).", key="fm_nwc_form")
        st.session_state.fm_inputs["capital_expenditures"] = st.number_input("Capital Expenditures (CapEx) ($)", min_value=0, value=st.session_state.fm_inputs.get("capital_expenditures", DEFAULT_CAPITAL_EXPENDITURES), step=1000, help="Annual investment in long-term assets (e.g., property, plant, equipment). Enter as positive for cash outflow.", key="fm_capex_form")
    with cf_bs_cols[1]:
        st.session_state.fm_inputs["debt_raised_repaid"] = st.number_input("Net Debt Raised/(Repaid) ($)", value=st.session_state.fm_inputs.get("debt_raised_repaid", DEFAULT_DEBT_RAISED_REPAID), step=1000, help="Net cash from new debt minus debt repayments. Positive for inflow, negative for outflow.", key="fm_debt_form")
        st.session_state.fm_inputs["equity_issued_repurchased"] = st.number_input("Net Equity Issued/(Repurchased) ($)", value=st.session_state.fm_inputs.get("equity_issued_repurchased", DEFAULT_EQUITY_ISSUED_REPURCHASED), step=1000, help="Net cash from new equity issued minus equity repurchased. Positive for inflow, negative for outflow.", key="fm_equity_fin_form")
    with cf_bs_cols[2]:
        st.subheader("Initial Balance Sheet Values (Year 0)")
        st.session_state.fm_inputs["initial_cash_balance"] = st.number_input("Cash ($)", min_value=0, value=st.session_state.fm_inputs.get("initial_cash_balance", DEFAULT_INITIAL_CASH_BALANCE), key="fm_init_cash_form", help="Cash balance at the beginning of Year 1 (end of Year 0).")
        st.session_state.fm_inputs["initial_accounts_receivable"] = st.number_input("Accounts Receivable ($)", min_value=0, value=st.session_state.fm_inputs.get("initial_accounts_receivable", DEFAULT_INITIAL_ACCOUNTS_RECEIVABLE), key="fm_init_ar_form", help="Initial accounts receivable.")
        st.session_state.fm_inputs["initial_inventory"] = st.number_input("Inventory ($)", min_value=0, value=st.session_state.fm_inputs.get("initial_inventory", DEFAULT_INITIAL_INVENTORY), key="fm_init_inv_form", help="Initial inventory value.")
        st.session_state.fm_inputs["initial_accounts_payable"] = st.number_input("Accounts Payable ($)", min_value=0, value=st.session_state.fm_inputs.get("initial_accounts_payable", DEFAULT_INITIAL_ACCOUNTS_PAYABLE), key="fm_init_ap_form", help="Initial accounts payable.")
        st.session_state.fm_inputs["initial_ppe"] = st.number_input("Property, Plant & Equipment (Net PPE) ($)", min_value=0, value=st.session_state.fm_inputs.get("initial_ppe", DEFAULT_INITIAL_PPE), key="fm_init_ppe_form", help="Initial net Property, Plant, and Equipment value.")
        st.session_state.fm_inputs["initial_accumulated_depreciation"] = st.number_input("Accumulated Depreciation ($)", min_value=0, value=st.session_state.fm_inputs.get("initial_accumulated_depreciation", DEFAULT_INITIAL_ACCUMULATED_DEPRECIATION), key="fm_init_ad_form", help="Initial accumulated depreciation. Note: Net PPE should be Gross PPE - Accumulated Depreciation. This input is for tracking, ensure consistency if Gross PPE is considered elsewhere.")
        st.session_state.fm_inputs["initial_long_term_debt"] = st.number_input("Long-Term Debt ($)", min_value=0, value=st.session_state.fm_inputs.get("initial_long_term_debt", DEFAULT_INITIAL_LONG_TERM_DEBT), key="fm_init_ltd_form", help="Initial long-term debt.")
        st.session_state.fm_inputs["initial_equity"] = st.number_input("Total Equity ($)", min_value=0, value=st.session_state.fm_inputs.get("initial_equity", DEFAULT_INITIAL_EQUITY), key="fm_init_equity_form", help="Initial total equity. Ensure A = L + E for Year 0.")

    submitted_assumptions = st.form_submit_button("Generate Financial Statements", help="Click to generate P&L, Cash Flow, and Balance Sheet based on your inputs.")

# Initialize should_generate to False before the main conditional block
should_generate = False

if submitted_assumptions:
    # Update fm_inputs from the text_display fields before calculation
    # This makes the number input (text_display key) the source of truth for percentages
    # THIS BLOCK IS NO LONGER NEEDED as callbacks handle fm_inputs updates for percentages.
    # for main_input_key, widget_key_prefix in PERCENTAGE_KEYS_INFO.items():
    #     text_display_key = f"{widget_key_prefix}_text_display"
    #     if text_display_key in st.session_state:
    #         st.session_state.fm_inputs[main_input_key] = st.session_state[text_display_key] / 100.0
    #     # Also, ensure the slider display value is consistent with the text input after submission for next render
    #     slider_display_key = f"{widget_key_prefix}_slider_display"
    #     if text_display_key in st.session_state and slider_display_key in st.session_state:
    #          st.session_state[slider_display_key] = st.session_state[text_display_key]

    # --- AI Review of Assumptions (before generation) ---
    if st.session_state.get("business_assumptions") and \
       st.session_state.get("final_model_structure") and \
       st.session_state.fm_inputs: # fm_inputs should be populated by the form submission

        with st.spinner("AI is reviewing your assumptions..."):
            try:
                review_feedback = ae.review_all_assumptions(
                    financial_assumptions=st.session_state.fm_inputs,
                    business_assumptions=st.session_state.business_assumptions,
                    model_structure=st.session_state.final_model_structure
                )
                st.session_state.assumption_review_feedback = review_feedback
            except Exception as e:
                st.error(f"Error during AI assumption review: {e}")
                st.session_state.assumption_review_feedback = "Review failed."

    if st.session_state.assumption_review_feedback:
        st.info("AI Review of Your Assumptions:")
        st.markdown(st.session_state.assumption_review_feedback)
        
        review_cols = st.columns(2)
        with review_cols[0]:
            if st.button("Proceed to Generate Statements Anyway", key="proceed_generation_btn"):
                st.session_state.proceed_after_review = True
                st.session_state.assumption_review_feedback = None # Clear feedback to avoid re-showing
                st.rerun() # Rerun to trigger generation
        with review_cols[1]:
            st.write("Or, revise your inputs above and click 'Generate Financial Statements' again.")
            
    # --- Actual Financial Statement Generation ---
    # Only generate if submitted, and ( (no review was done/needed) OR (user chose to proceed after review) )
    should_generate = submitted_assumptions and \
                      (not st.session_state.assumption_review_feedback or st.session_state.proceed_after_review)

    if should_generate:
        with st.spinner("Generating financial statements..."):
            try:
                statements = financial_model_logic.generate_financial_statements(st.session_state.fm_inputs)
                st.session_state.fm_financial_statements = statements
                st.success("Financial statements generated!")
                st.session_state.proceed_after_review = False # Reset flag
                st.session_state.assumption_review_feedback = None # Clear feedback
            except Exception as e:
                st.error(f"An error occurred during financial statement generation: {e}")
                st.session_state.fm_financial_statements = None
                st.session_state.proceed_after_review = False # Reset flag


# --- DISPLAY RESULTS ---
# Now 'should_generate' is defined regardless of whether 'submitted_assumptions' was true,
# but its value correctly reflects if generation should have occurred.
if st.session_state.get('fm_financial_statements') and should_generate:
    # --- Step 4: Understand Formulas & Model Logic (Contextual to generated statements) ---
    # This section appears after statements are generated, allowing users to explore concepts.
    with st.expander("Step 4: Understand Formulas & Model Logic 🧠", expanded=True): # Expanded True for visibility
        st.markdown("Explore common financial concepts or how statements connect.")

        # Explanation for Financial Statement Interdependencies
        if st.button("Explain Financial Statement Connections", key="explain_interdependencies_btn"):
            with st.spinner("AI is preparing an explanation..."):
                explanation = fle.explain_statement_interdependencies(
                    business_assumptions=st.session_state.get("business_assumptions")
                )
                st.session_state.interdependency_explanation_output = explanation
        
        if st.session_state.interdependency_explanation_output:
            st.subheader("How Financial Statements Connect:")
            st.markdown(st.session_state.interdependency_explanation_output)
            st.markdown("---")

        # Explanation for a specific formula/concept
        st.session_state.formula_explanation_topic = st.text_input(
            "Enter a financial formula or concept to explain (e.g., EBITDA, NPV, Working Capital):",
            value=st.session_state.formula_explanation_topic,
            key="formula_topic_input"
        )
        if st.button("Explain Concept", key="explain_concept_btn"):
            if st.session_state.formula_explanation_topic:
                if st.session_state.business_assumptions and st.session_state.final_model_structure:
                    with st.spinner(f"AI is explaining '{st.session_state.formula_explanation_topic}'..."):
                        explanation = fle.explain_formula_or_concept(
                            formula_or_concept=st.session_state.formula_explanation_topic,
                            business_assumptions=st.session_state.business_assumptions,
                            model_structure=st.session_state.final_model_structure,
                            financial_assumptions=st.session_state.fm_inputs # Provide current inputs for context
                        )
                        st.session_state.formula_explanation_output = explanation
                else:
                    st.warning("Business context (Step 1) and Model Structure (Step 2) are needed for tailored explanations.")
            else:
                st.warning("Please enter a formula or concept to explain.")

        if st.session_state.formula_explanation_output:
            st.subheader(f"Explanation for: {st.session_state.formula_explanation_topic}")
            st.markdown(st.session_state.formula_explanation_output)
            # Clear after showing or keep until new topic? For now, keep.
            # To clear: st.session_state.formula_explanation_output = None 
            # st.session_state.formula_explanation_topic = ""
        st.markdown("---")


    # --- Step 5: AI Model Validation (Contextual to generated statements) ---
    with st.expander("Step 5: AI Model Validation & Review ✅", expanded=True):
        st.markdown("Get an AI-powered review of your generated model for overall reasonableness and potential insights.")
        if st.button("Get AI Reasonableness Review", key="ai_reasonableness_review_btn"):
            if st.session_state.get("business_assumptions") and \
               st.session_state.get("final_model_structure") and \
               st.session_state.get("fm_inputs") and \
               st.session_state.get("fm_financial_statements"):
                with st.spinner("AI is reviewing your financial model..."):
                    try:
                        feedback = mve.review_model_reasonableness(
                            business_assumptions=st.session_state.business_assumptions,
                            model_structure=st.session_state.final_model_structure,
                            financial_assumptions=st.session_state.fm_inputs,
                            generated_statements=st.session_state.fm_financial_statements
                        )
                        st.session_state.model_reasonableness_feedback = feedback
                    except Exception as e:
                        st.error(f"Error during AI model review: {e}")
                        st.session_state.model_reasonableness_feedback = "Failed to get review."
            else:
                st.warning("Ensure business context, model structure, financial inputs, and generated statements are available for a comprehensive review.")

        if st.session_state.model_reasonableness_feedback:
            st.subheader("AI Model Reasonableness Review:")
            st.markdown(st.session_state.model_reasonableness_feedback)
            st.markdown("---")
    
    # --- Step 6: Interpretation & Presentation Aids ---
    with st.expander("Step 6: Interpret Your Model with AI 🔍", expanded=True):
        st.markdown("Understand your Key Performance Indicators (KPIs) and get an AI-generated summary of your model.")

        # KPI Explanation
        if st.session_state.final_model_structure and st.session_state.final_model_structure.get("kpis"):
            kpi_options = st.session_state.final_model_structure["kpis"]
            st.session_state.kpi_to_explain = st.selectbox(
                "Select a KPI to understand:",
                options=kpi_options,
                index=kpi_options.index(st.session_state.kpi_to_explain) if st.session_state.kpi_to_explain in kpi_options else 0,
                key="kpi_select_for_explanation"
            )
            if st.button("Explain KPI", key="explain_kpi_btn"):
                if st.session_state.kpi_to_explain and \
                   st.session_state.business_assumptions and \
                   st.session_state.final_model_structure:
                    with st.spinner(f"AI is explaining '{st.session_state.kpi_to_explain}'..."):
                        # KPI value could be fetched from statements if calculated, for now passing N/A
                        explanation = ie.explain_kpi(
                            kpi_name=st.session_state.kpi_to_explain,
                            business_assumptions=st.session_state.business_assumptions,
                            model_structure=st.session_state.final_model_structure,
                            kpi_value="N/A" # Placeholder - enhance later to pass actual value
                        )
                        st.session_state.kpi_explanation_output = explanation
                else:
                    st.warning("Ensure business context and model structure are defined for KPI explanation.")
            
            if st.session_state.kpi_explanation_output and st.session_state.kpi_to_explain:
                st.subheader(f"AI Explanation for: {st.session_state.kpi_to_explain}")
                st.markdown(st.session_state.kpi_explanation_output)
                st.markdown("---")
        else:
            st.caption("KPIs will be available for explanation once the model structure is confirmed (Step 2).")

        # Financial Summary Narrative
        if st.button("Generate Financial Summary Narrative", key="generate_narrative_btn"):
            if st.session_state.business_assumptions and \
               st.session_state.final_model_structure and \
               st.session_state.fm_inputs and \
               st.session_state.fm_financial_statements:
                with st.spinner("AI is crafting your financial summary..."):
                    narrative = ie.generate_financial_summary_narrative(
                        business_assumptions=st.session_state.business_assumptions,
                        model_structure=st.session_state.final_model_structure,
                        financial_assumptions=st.session_state.fm_inputs,
                        generated_statements=st.session_state.fm_financial_statements
                    )
                    st.session_state.financial_summary_narrative = narrative
            else:
                st.warning("Full context (Steps 1-3 & generated statements) needed for summary narrative.")

        if st.session_state.financial_summary_narrative:
            st.subheader("AI-Generated Financial Summary Narrative:")
            st.markdown(st.session_state.financial_summary_narrative)
            st.markdown("---")


    statements = st.session_state.fm_financial_statements
    
    # Card for P&L
    with st.expander("Profit & Loss (P&L) Statement", expanded=True):
        styled_card(
            title="Profit & Loss (P&L)",
            content="", # Content will be added by st elements below
            icon="📈"
        )
        st.dataframe(statements["p_and_l"].style.format("{:,.0f}"))
        st.line_chart(statements["p_and_l"].T[['Revenue', 'Net Income', 'EBITDA']])

    # Card for Cash Flow
    with st.expander("Cash Flow Statement", expanded=True):
        styled_card(
            title="Cash Flow Statement",
            content="", # Content will be added by st elements below
            icon="🌊"
        )
        st.dataframe(statements["cash_flow"].style.format("{:,.0f}"))
        st.line_chart(statements["cash_flow"].T[['Cash Flow from Operations (CFO)', 'Ending Cash Balance']])

    # Card for Balance Sheet
    with st.expander("Balance Sheet", expanded=True):
        styled_card(
            title="Balance Sheet",
            content="", # Content will be added by st elements below
            icon="⚖️"
        )
        st.dataframe(statements["balance_sheet"].style.format("{:,.0f}"))
        # Check if BS balances, display warning if not
        for year_col in ["Year 0", "Year 1", "Year 2", "Year 3"]:
            balance_check_value = statements["balance_sheet"].loc["Balance Check (Assets - L&E)", year_col]
            if abs(balance_check_value) > 0.01: # Using a small tolerance
                st.warning(f"Balance Sheet for {year_col} does not balance. Difference: {balance_check_value:.2f}")
        st.line_chart(statements["balance_sheet"].T[['Total Assets', 'Total Liabilities', 'Total Equity']])
    
    # --- SCENARIO ANALYSIS (Simple) ---
    # The slider is now defined unconditionally in the sidebar.
    # This section now only handles calculation and display if sensitivity is set and statements exist.
    if st.session_state.fm_scenario_revenue_sensitivity != 0: # Check against integer 0
        original_revenue_y1 = st.session_state.fm_inputs["revenue_y1"]
        modified_inputs = st.session_state.fm_inputs.copy()
        # Adjust calculation to divide sensitivity by 100.0
        modified_inputs["revenue_y1"] = original_revenue_y1 * (1 + st.session_state.fm_scenario_revenue_sensitivity / 100.0)
        
        try:
            with st.spinner("Recalculating for scenario..."):
                scenario_statements = financial_model_logic.generate_financial_statements(modified_inputs)
            # Display sensitivity directly as it's already a whole percentage number
            st.subheader(f"Scenario: Revenue {st.session_state.fm_scenario_revenue_sensitivity:+.0f}%")
            
            scenario_display_cols = st.columns(2)
            with scenario_display_cols[0]:
                st.write("P&L (Scenario):")
                st.dataframe(scenario_statements["p_and_l"].style.format("{:,.0f}"))
            with scenario_display_cols[1]:
                st.write("Cash Flow (Scenario):")
                st.dataframe(scenario_statements["cash_flow"].style.format("{:,.0f}"))
            st.write("Balance Sheet (Scenario):")
            st.dataframe(scenario_statements["balance_sheet"].style.format("{:,.0f}"))

        except Exception as e:
            st.error(f"Error in scenario analysis: {e}")

    st.divider()
    # --- Update Status and Continue Button ---
    if st.session_state.get('fm_financial_statements'): # Only show if statements have been generated
        st.session_state.financial_model_status = "Completed" # Update status
        st.success("Financial Modeling complete!")
        
        if st.button("➡️ Continue to Investor Scout", key="fm_continue_to_is"):
            st.info("Navigate to 'Investor Scout' from the sidebar or top navigation to continue.")
            # Potentially set a session state flag to guide the user or pre-fill something on the next page.
            st.session_state.is_needs_financial_data = True # Example flag
    
    st.divider()
    # --- EXPORT ---
    st.subheader("Export Financials") # Added a subheader for clarity
    try:
        excel_data = financial_model_logic.export_to_excel(st.session_state.fm_financial_statements)
        st.download_button(
            label="Download Financials as Excel",
            data=excel_data,
            file_name="financial_projections.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="fm_download_excel"
        )
    except Exception as e:
        st.error(f"Could not prepare Excel for download: {e}")
        st.info("Excel export functionality encountered an issue.")
