import streamlit as st
import pandas as pd
from io import BytesIO # For excel export
from core import financial_model_logic
from core.utils import styled_card # Import styled_card
# LLM interface for guidance/tips would use global config from app.py's sidebar

st.set_page_config(page_title="Financial Modeling", layout="wide")

def initialize_page_session_state():
    """Initializes session state keys specific to the Financial Modeling page."""
    if 'fm_inputs' not in st.session_state:
        # Initialize with default values or ensure they are set before use
        st.session_state.fm_inputs = {
            "revenue_y1": 100000, "revenue_growth_y2": 0.20, "revenue_growth_y3": 0.15,
            "cogs_percent": 0.40,
            "opex_y1": 30000, "opex_growth_y2": 0.10, "opex_growth_y3": 0.05,
            "tax_rate": 0.21,
            "interest_expense": 1000,
            "depreciation_amortization": 5000,
            "change_in_working_capital": 2000,
            "capital_expenditures": 10000,
            "debt_raised_repaid": 0,
            "equity_issued_repurchased": 0,
            "initial_cash_balance": 50000,
            "initial_accounts_receivable": 15000,
            "initial_inventory": 10000,
            "initial_accounts_payable": 8000,
            "initial_ppe": 75000,
            "initial_accumulated_depreciation": 10000,
            "initial_long_term_debt": 20000,
            # Corrected initial equity calculation for BS to balance
            # Assets(50+15+10+(75-10)=140) - Liab(8+20=28) = 112
            "initial_equity": 112000
        }
    if 'fm_financial_statements' not in st.session_state:
        st.session_state.fm_financial_statements = None
    if 'fm_scenario_revenue_sensitivity' not in st.session_state:
        st.session_state.fm_scenario_revenue_sensitivity = 0.0


initialize_page_session_state()

st.title("Financial Modeling Agent 💰")
st.markdown("Input your key assumptions to generate basic 3-year financial projections. Configure AI provider in the sidebar if LLM guidance features are used.")

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
            if st.session_state.fm_inputs.get("revenue_y1") == 100000: # Default value check
                 st.session_state.fm_inputs["revenue_y1"] = int(parsed_funding * 0.5) # Example: Y1 revenue is 50% of funding needed
                 st.info(f"Pre-filled Year 1 Revenue based on funding needed ({profile['funding_needed']}). Please review and adjust.")
        except ValueError:
            pass # Could not parse funding_needed, skip pre-fill for revenue

# Use a form for inputs to prevent reruns on each widget change until submission
with st.form(key="financial_assumptions_form"):

    # Group inputs for better layout
    input_cols = st.columns(3)
    with input_cols[0]:
        st.subheader("Revenue")
        st.session_state.fm_inputs["revenue_y1"] = st.number_input("Year 1 Revenue ($)", min_value=0, value=st.session_state.fm_inputs.get("revenue_y1", 100000), step=1000, key="fm_rev_y1", help="Projected total revenue for the first full year of operation.")
        st.session_state.fm_inputs["revenue_growth_y2"] = st.slider("Year 2 Revenue Growth", min_value=-1.0, max_value=2.0, value=st.session_state.fm_inputs.get("revenue_growth_y2", 0.20), step=0.01, format="%.0f%%", key="fm_rev_g2", help="Expected year-over-year revenue growth rate for Year 2.")
        st.session_state.fm_inputs["revenue_growth_y3"] = st.slider("Year 3 Revenue Growth", min_value=-1.0, max_value=2.0, value=st.session_state.fm_inputs.get("revenue_growth_y3", 0.15), step=0.01, format="%.0f%%", key="fm_rev_g3", help="Expected year-over-year revenue growth rate for Year 3.")

    with input_cols[1]:
        st.subheader("Costs & Expenses")
        st.session_state.fm_inputs["cogs_percent"] = st.slider("COGS (% of Revenue)", min_value=0.0, max_value=1.0, value=st.session_state.fm_inputs.get("cogs_percent", 0.40), step=0.01, format="%.0f%%", key="fm_cogs", help="Cost of Goods Sold as a percentage of total revenue.")
        st.session_state.fm_inputs["opex_y1"] = st.number_input("Year 1 Operating Expenses ($)", min_value=0, value=st.session_state.fm_inputs.get("opex_y1", 30000), step=1000, key="fm_opex_y1", help="Total operating expenses (e.g., salaries, rent, marketing) for Year 1, excluding COGS.")
        st.session_state.fm_inputs["opex_growth_y2"] = st.slider("Year 2 OpEx Growth", min_value=-1.0, max_value=1.0, value=st.session_state.fm_inputs.get("opex_growth_y2", 0.10), step=0.01, format="%.0f%%", key="fm_opex_g2", help="Expected growth rate for operating expenses in Year 2.")
        st.session_state.fm_inputs["opex_growth_y3"] = st.slider("Year 3 OpEx Growth", min_value=-1.0, max_value=1.0, value=st.session_state.fm_inputs.get("opex_growth_y3", 0.05), step=0.01, format="%.0f%%", key="fm_opex_g3", help="Expected growth rate for operating expenses in Year 3.")

    with input_cols[2]:
        st.subheader("Other Financial Inputs")
        st.session_state.fm_inputs["tax_rate"] = st.slider("Tax Rate", min_value=0.0, max_value=0.5, value=st.session_state.fm_inputs.get("tax_rate", 0.21), step=0.01, format="%.0f%%", key="fm_tax", help="Effective corporate tax rate on profits.")
        st.session_state.fm_inputs["interest_expense"] = st.number_input("Annual Interest Expense ($)", min_value=0, value=st.session_state.fm_inputs.get("interest_expense", 1000), step=100, key="fm_interest", help="Projected annual interest paid on debt.")
        st.session_state.fm_inputs["depreciation_amortization"] = st.number_input("Annual Depreciation & Amortization ($)", min_value=0, value=st.session_state.fm_inputs.get("depreciation_amortization", 5000), step=500, key="fm_da", help="Annual non-cash expense for depreciation of assets and amortization of intangibles.")

    st.divider()
    st.subheader("Cash Flow & Balance Sheet Assumptions (Annual)")
    cf_bs_cols = st.columns(3)
    with cf_bs_cols[0]:
        st.session_state.fm_inputs["change_in_working_capital"] = st.number_input("Change in Net Working Capital ($)", value=st.session_state.fm_inputs.get("change_in_working_capital", 2000), step=500, help="Annual change in (Current Assets - Current Liabilities). Positive for increase (cash outflow).", key="fm_nwc")
        st.session_state.fm_inputs["capital_expenditures"] = st.number_input("Capital Expenditures (CapEx) ($)", min_value=0, value=st.session_state.fm_inputs.get("capital_expenditures", 10000), step=1000, help="Annual investment in long-term assets (e.g., property, plant, equipment). Enter as positive for cash outflow.", key="fm_capex")
    with cf_bs_cols[1]:
        st.session_state.fm_inputs["debt_raised_repaid"] = st.number_input("Net Debt Raised/(Repaid) ($)", value=st.session_state.fm_inputs.get("debt_raised_repaid", 0), step=1000, help="Net cash from new debt minus debt repayments. Positive for inflow, negative for outflow.", key="fm_debt")
        st.session_state.fm_inputs["equity_issued_repurchased"] = st.number_input("Net Equity Issued/(Repurchased) ($)", value=st.session_state.fm_inputs.get("equity_issued_repurchased", 0), step=1000, help="Net cash from new equity issued minus equity repurchased. Positive for inflow, negative for outflow.", key="fm_equity_fin")
    with cf_bs_cols[2]:
        st.subheader("Initial Balance Sheet Values (Year 0)")
        st.session_state.fm_inputs["initial_cash_balance"] = st.number_input("Cash ($)", min_value=0, value=st.session_state.fm_inputs.get("initial_cash_balance", 50000), key="fm_init_cash", help="Cash balance at the beginning of Year 1 (end of Year 0).")
        # Add more initial BS items as needed by financial_model_logic.py
        # For now, the logic file has defaults for AR, Inv, AP, PPE, AccDep, LTD, Equity.
        # These could be exposed here if more granular control is desired.

    submitted_assumptions = st.form_submit_button("Generate Financial Statements", help="Click to generate P&L, Cash Flow, and Balance Sheet based on your inputs.")


if submitted_assumptions:
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
    # Moved to sidebar in rec.md, but it's already in sidebar.
    # If it were in main page, it could be an expander too.
    st.sidebar.subheader("Scenario Analysis")
    st.session_state.fm_scenario_revenue_sensitivity = st.sidebar.slider(
        "Revenue Sensitivity (+/- %)", 
        min_value=-0.5, max_value=0.5, 
        value=st.session_state.fm_scenario_revenue_sensitivity, 
        step=0.05, format="%.0f%%",
        key="fm_rev_sensitivity_slider"
        )

    if st.session_state.fm_scenario_revenue_sensitivity != 0.0:
        original_revenue_y1 = st.session_state.fm_inputs["revenue_y1"]
        modified_inputs = st.session_state.fm_inputs.copy()
        modified_inputs["revenue_y1"] = original_revenue_y1 * (1 + st.session_state.fm_scenario_revenue_sensitivity)
        
        try:
            with st.spinner("Recalculating for scenario..."):
                scenario_statements = financial_model_logic.generate_financial_statements(modified_inputs)
            st.subheader(f"Scenario: Revenue {st.session_state.fm_scenario_revenue_sensitivity*100:+.0f}%")
            
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
