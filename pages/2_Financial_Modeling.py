import streamlit as st
import pandas as pd
from io import BytesIO # For excel export
from core import financial_model_logic
from core.utils import styled_card # Import styled_card
# LLM interface for guidance/tips would use global config from app.py's sidebar

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


initialize_page_session_state()

st.title("Financial Modeling Agent 💰")
st.markdown("Input your key assumptions to generate basic 3-year financial projections. Configure AI provider in the sidebar if LLM guidance features are used.")

# --- Sidebar Elements ---
# Scenario Analysis Slider (always visible)
st.sidebar.subheader("Scenario Analysis")
st.session_state.fm_scenario_revenue_sensitivity = st.sidebar.slider(
    "Revenue Sensitivity (+/- %)", 
    min_value=-50, max_value=50,
    value=st.session_state.fm_scenario_revenue_sensitivity, 
    step=1, format="%d%%",
    key="fm_rev_sensitivity_slider"
)

# --- INPUTS WIZARD ---
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
    cogs_cols = st.columns([3,1])
    with cogs_cols[0]:
        st.slider("COGS Slider", min_value=0.0, max_value=100.0, step=1.0, format="%.0f%%",
                  key=f"{PERCENTAGE_KEYS_INFO['cogs_percent']}_slider_display", 
                  on_change=sync_cogs_slider,
                  help="Cost of Goods Sold as a percentage of total revenue.", label_visibility="collapsed")
    with cogs_cols[1]:
        st.number_input("COGS Text", min_value=0.0, max_value=100.0, step=0.1, format="%.1f",
                        key=f"{PERCENTAGE_KEYS_INFO['cogs_percent']}_text_display", 
                        on_change=sync_cogs_text,
                        label_visibility="collapsed")

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

# Use a form for remaining inputs to prevent reruns on each widget change until submission
with st.form(key="financial_assumptions_form"):
    st.subheader("Core Financial Values & Other Assumptions") # Changed subheader
    # Group inputs for better layout
    form_input_cols = st.columns(3) # Renamed to avoid conflict
    with form_input_cols[0]: # Was input_cols[0]
        st.subheader("Revenue") # This subheader might be redundant if one is above for the whole section
        st.session_state.fm_inputs["revenue_y1"] = st.number_input("Year 1 Revenue ($)", min_value=0, value=st.session_state.fm_inputs.get("revenue_y1", DEFAULT_REVENUE_Y1), step=1000, key="fm_rev_y1_form", help="Projected total revenue for the first full year of operation.")
        # Percentage inputs for revenue growth are now outside the form

    with form_input_cols[1]: # Was input_cols[1]
        st.subheader("Costs & Expenses") # Redundant?
        # COGS % is now outside the form
        st.session_state.fm_inputs["opex_y1"] = st.number_input("Year 1 Operating Expenses ($)", min_value=0, value=st.session_state.fm_inputs.get("opex_y1", DEFAULT_OPEX_Y1), step=1000, key="fm_opex_y1_form", help="Total operating expenses (e.g., salaries, rent, marketing) for Year 1, excluding COGS.")
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


    with st.spinner("Generating financial statements..."):
        try:
            # Use the actual logic now
            statements = financial_model_logic.generate_financial_statements(st.session_state.fm_inputs)
            st.session_state.fm_financial_statements = statements
            st.success("Financial statements generated!")
        except Exception as e:
            st.error(f"An error occurred during financial statement generation: {e}")
            st.session_state.fm_financial_statements = None

# --- DISPLAY RESULTS ---
if st.session_state.get('fm_financial_statements'):
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
