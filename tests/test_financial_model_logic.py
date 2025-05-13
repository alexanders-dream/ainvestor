import pytest
import pandas as pd
from pandas.testing import assert_frame_equal
from io import BytesIO

from core import financial_model_logic

# Sample inputs for testing, similar to the __main__ block in the logic file
sample_inputs_valid = {
    "revenue_y1": 100000, "revenue_growth_y2": 0.20, "revenue_growth_y3": 0.15,
    "cogs_percent": 0.40,
    "opex_y1": 30000, "opex_growth_y2": 0.10, "opex_growth_y3": 0.05,
    "tax_rate": 0.21,
    "interest_expense": 1000,
    "depreciation_amortization": 5000,
    "change_in_working_capital": 2000, # Positive value means NWC increased, cash decreased
    "capital_expenditures": 10000,
    "debt_raised_repaid": 0,
    "equity_issued_repurchased": 0,
    "initial_cash_balance": 50000,
    "initial_accounts_receivable": 15000,
    "initial_inventory": 10000,
    "initial_accounts_payable": 8000,
    "initial_ppe": 75000, # Gross
    "initial_accumulated_depreciation": 10000, # Positive value, logic makes it negative
    "initial_long_term_debt": 20000,
    "initial_equity": 102000 # Assets(50+15+10+(75-10)=140) - Liab(8+20=28) = 112. Vision.md example was 102000. Let's use a calculated one.
                           # Cash(50) + AR(15) + Inv(10) + NetPPE(75-10=65) = 140 (Assets)
                           # AP(8) + LTD(20) = 28 (Liabilities)
                           # Equity = 140 - 28 = 112. So initial_equity should be 112000 for BS to balance.
                           # The example in vision.md page for FinModel had 102000.
                           # The example in financial_model_logic.py __main__ had 470000.
                           # For consistency with the logic's own test, let's use a value that makes Year 0 BS balance.
                           # Initial Equity = Initial Assets - Initial Liabilities
                           # Initial Assets = 50000 (Cash) + 15000 (AR) + 10000 (Inv) + (75000 (PPE) - 10000 (AccDep)) = 140000
                           # Initial Liabilities = 8000 (AP) + 20000 (LTD) = 28000
                           # Initial Equity = 140000 - 28000 = 112000
}
sample_inputs_valid["initial_equity"] = 112000


def test_generate_financial_statements_structure():
    """Test if the function returns the correct structure (dict of DataFrames)."""
    statements = financial_model_logic.generate_financial_statements(sample_inputs_valid)
    assert isinstance(statements, dict)
    assert "p_and_l" in statements
    assert "cash_flow" in statements
    assert "balance_sheet" in statements
    assert isinstance(statements["p_and_l"], pd.DataFrame)
    assert isinstance(statements["cash_flow"], pd.DataFrame)
    assert isinstance(statements["balance_sheet"], pd.DataFrame)

def test_p_and_l_calculations():
    """Test some key P&L calculations."""
    statements = financial_model_logic.generate_financial_statements(sample_inputs_valid)
    p_and_l = statements["p_and_l"]

    # Revenue Year 1
    assert p_and_l.loc["Revenue", "Year 1"] == sample_inputs_valid["revenue_y1"]
    # Revenue Year 2
    expected_rev_y2 = sample_inputs_valid["revenue_y1"] * (1 + sample_inputs_valid["revenue_growth_y2"])
    assert p_and_l.loc["Revenue", "Year 2"] == expected_rev_y2
    # Gross Profit Year 1
    expected_gp_y1 = sample_inputs_valid["revenue_y1"] * (1 - sample_inputs_valid["cogs_percent"])
    assert p_and_l.loc["Gross Profit", "Year 1"] == expected_gp_y1
    # Net Income Year 1 (example, more detailed checks could be added)
    # This requires calculating all intermediate P&L steps.
    # For brevity, we'll trust the logic for now or add more specific checks if bugs are found.
    # Example: EBIT = EBITDA - D&A
    ebitda_y1 = expected_gp_y1 - sample_inputs_valid["opex_y1"]
    ebit_y1 = ebitda_y1 - sample_inputs_valid["depreciation_amortization"]
    assert p_and_l.loc["EBIT (Operating Income)", "Year 1"] == ebit_y1
    ebt_y1 = ebit_y1 - sample_inputs_valid["interest_expense"]
    taxes_y1 = max(0, ebt_y1 * sample_inputs_valid["tax_rate"])
    net_income_y1 = ebt_y1 - taxes_y1
    assert abs(p_and_l.loc["Net Income", "Year 1"] - net_income_y1) < 0.01 # Using tolerance for float


def test_cash_flow_calculations():
    """Test some key Cash Flow calculations."""
    statements = financial_model_logic.generate_financial_statements(sample_inputs_valid)
    cash_flow = statements["cash_flow"]
    p_and_l = statements["p_and_l"] # Needed for Net Income

    # CFO Year 1
    # Net Income from P&L, D&A from inputs, Change in NWC from inputs (negative for CF)
    cfo_y1 = (p_and_l.loc["Net Income", "Year 1"] +
                sample_inputs_valid["depreciation_amortization"] -
                sample_inputs_valid["change_in_working_capital"])
    assert abs(cash_flow.loc["Cash Flow from Operations (CFO)", "Year 1"] - cfo_y1) < 0.01

    # Ending Cash Balance Year 1
    net_change_cash_y1 = (cfo_y1 - 
                          sample_inputs_valid["capital_expenditures"] + 
                          sample_inputs_valid["debt_raised_repaid"] + 
                          sample_inputs_valid["equity_issued_repurchased"])
    ending_cash_y1 = sample_inputs_valid["initial_cash_balance"] + net_change_cash_y1
    assert abs(cash_flow.loc["Ending Cash Balance", "Year 1"] - ending_cash_y1) < 0.01


def test_balance_sheet_balancing():
    """Test if the balance sheet balances for all years."""
    statements = financial_model_logic.generate_financial_statements(sample_inputs_valid)
    balance_sheet = statements["balance_sheet"]
    for year_col in ["Year 0", "Year 1", "Year 2", "Year 3"]:
        # Using a small tolerance for floating point comparisons
        assert abs(balance_sheet.loc["Balance Check (Assets - L&E)", year_col]) < 0.01, f"BS does not balance in {year_col}"

def test_export_to_excel():
    """Test Excel export functionality."""
    statements = financial_model_logic.generate_financial_statements(sample_inputs_valid)
    excel_bytes_io = financial_model_logic.export_to_excel(statements)
    
    assert isinstance(excel_bytes_io, BytesIO)
    excel_bytes_io.seek(0) # Go to the start of the stream
    
    # Try to read it back with pandas to verify it's a valid Excel file
    # This also implicitly checks if all sheets are there if pd.read_excel is used correctly
    try:
        xls = pd.ExcelFile(excel_bytes_io)
        assert "Profit & Loss" in xls.sheet_names
        assert "Cash Flow Statement" in xls.sheet_names
        assert "Balance Sheet" in xls.sheet_names
        
        # Optionally, read a sheet and check some values
        pnl_df_from_excel = pd.read_excel(xls, sheet_name="Profit & Loss", index_col=0)
        assert_frame_equal(statements["p_and_l"].fillna(0), pnl_df_from_excel.fillna(0), check_dtype=False, atol=0.01)

    except Exception as e:
        pytest.fail(f"Failed to read exported Excel file: {e}")


# Test with zero inputs (should not crash, produce all zeros)
zero_inputs = {key: 0 for key in sample_inputs_valid.keys()}
# some percentages should be handled, e.g. tax_rate
zero_inputs["tax_rate"] = 0.0 
zero_inputs["cogs_percent"] = 0.0
zero_inputs["revenue_growth_y2"] = 0.0
zero_inputs["revenue_growth_y3"] = 0.0
zero_inputs["opex_growth_y2"] = 0.0
zero_inputs["opex_growth_y3"] = 0.0


def test_generate_financial_statements_zero_inputs():
    statements = financial_model_logic.generate_financial_statements(zero_inputs)
    assert statements["p_and_l"].sum().sum() == 0  # All P&L values should be zero
    # Cash flow might have beginning balance if it was part of zero_inputs, but changes should be zero
    assert statements["cash_flow"].loc["Net Change in Cash"].sum() == 0
    # Balance sheet should balance even with zeros
    for year_col in ["Year 0", "Year 1", "Year 2", "Year 3"]:
        assert abs(statements["balance_sheet"].loc["Balance Check (Assets - L&E)", year_col]) < 0.01
