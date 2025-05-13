import pandas as pd
from io import BytesIO

def generate_financial_statements(inputs: dict):
    """
    Generates 3-year financial statements (P&L, Cash Flow, Balance Sheet)
    based on user inputs.

    Args:
        inputs (dict): A dictionary containing all necessary financial assumptions.
                       Keys should match those defined in the Streamlit page (e.g.,
                       "revenue_y1", "cogs_percent", "initial_cash_balance", etc.).

    Returns:
        dict: A dictionary containing three pandas DataFrames:
              "p_and_l", "cash_flow", "balance_sheet".
    """
    years = ["Year 1", "Year 2", "Year 3"]
    p_and_l = pd.DataFrame(index=[
        "Revenue", "COGS", "Gross Profit", "Operating Expenses (OpEx)",
        "EBITDA", "Depreciation & Amortization (D&A)", "EBIT (Operating Income)",
        "Interest Expense", "Earnings Before Tax (EBT)", "Taxes", "Net Income"
    ], columns=years, dtype=float)

    cash_flow = pd.DataFrame(index=[
        "Net Income", "Depreciation & Amortization", "Change in Net Working Capital",
        "Cash Flow from Operations (CFO)",
        "Capital Expenditures (CapEx)", "Cash Flow from Investing (CFI)",
        "Net Debt Raised/(Repaid)", "Net Equity Issued/(Repurchased)",
        "Cash Flow from Financing (CFF)",
        "Net Change in Cash", "Beginning Cash Balance", "Ending Cash Balance"
    ], columns=years, dtype=float)

    balance_sheet = pd.DataFrame(index=[
        "Cash & Cash Equivalents", "Accounts Receivable (A/R)", "Inventory",
        "Total Current Assets",
        "Property, Plant & Equipment (PPE), Gross", "Accumulated Depreciation",
        "PPE, Net", "Total Assets",
        "Accounts Payable (A/P)", "Short-Term Debt (Placeholder)", "Total Current Liabilities",
        "Long-Term Debt", "Total Liabilities",
        "Common Stock & APIC (Placeholder)", "Retained Earnings", "Total Equity",
        "Total Liabilities & Equity", "Balance Check (Assets - L&E)"
    ], columns=["Year 0"] + years, dtype=float)

    # --- Profit & Loss Calculations ---
    rev_y1 = inputs.get("revenue_y1", 0)
    p_and_l.loc["Revenue", "Year 1"] = rev_y1
    p_and_l.loc["Revenue", "Year 2"] = p_and_l.loc["Revenue", "Year 1"] * (1 + inputs.get("revenue_growth_y2", 0))
    p_and_l.loc["Revenue", "Year 3"] = p_and_l.loc["Revenue", "Year 2"] * (1 + inputs.get("revenue_growth_y3", 0))

    p_and_l.loc["COGS"] = p_and_l.loc["Revenue"] * inputs.get("cogs_percent", 0)
    p_and_l.loc["Gross Profit"] = p_and_l.loc["Revenue"] - p_and_l.loc["COGS"]

    opex_y1 = inputs.get("opex_y1", 0)
    p_and_l.loc["Operating Expenses (OpEx)", "Year 1"] = opex_y1
    p_and_l.loc["Operating Expenses (OpEx)", "Year 2"] = p_and_l.loc["Operating Expenses (OpEx)", "Year 1"] * (1 + inputs.get("opex_growth_y2", 0))
    p_and_l.loc["Operating Expenses (OpEx)", "Year 3"] = p_and_l.loc["Operating Expenses (OpEx)", "Year 2"] * (1 + inputs.get("opex_growth_y3", 0))

    p_and_l.loc["EBITDA"] = p_and_l.loc["Gross Profit"] - p_and_l.loc["Operating Expenses (OpEx)"]
    p_and_l.loc["Depreciation & Amortization (D&A)"] = inputs.get("depreciation_amortization", 0)
    p_and_l.loc["EBIT (Operating Income)"] = p_and_l.loc["EBITDA"] - p_and_l.loc["Depreciation & Amortization (D&A)"]
    p_and_l.loc["Interest Expense"] = inputs.get("interest_expense", 0)
    p_and_l.loc["Earnings Before Tax (EBT)"] = p_and_l.loc["EBIT (Operating Income)"] - p_and_l.loc["Interest Expense"]
    p_and_l.loc["Taxes"] = p_and_l.loc["Earnings Before Tax (EBT)"] * inputs.get("tax_rate", 0)
    p_and_l.loc["Taxes"] = p_and_l.loc["Taxes"].apply(lambda x: max(0, x)) # Ensure taxes are not negative
    p_and_l.loc["Net Income"] = p_and_l.loc["Earnings Before Tax (EBT)"] - p_and_l.loc["Taxes"]

    # --- Cash Flow Calculations ---
    cash_flow.loc["Net Income"] = p_and_l.loc["Net Income"]
    cash_flow.loc["Depreciation & Amortization"] = p_and_l.loc["Depreciation & Amortization (D&A)"]
    # Change in NWC: positive value means NWC increased, so cash decreased (outflow)
    cash_flow.loc["Change in Net Working Capital"] = -inputs.get("change_in_working_capital", 0) 
    cash_flow.loc["Cash Flow from Operations (CFO)"] = cash_flow.loc[["Net Income", "Depreciation & Amortization", "Change in Net Working Capital"]].sum()

    cash_flow.loc["Capital Expenditures (CapEx)"] = -inputs.get("capital_expenditures", 0) # CapEx is an outflow
    cash_flow.loc["Cash Flow from Investing (CFI)"] = cash_flow.loc["Capital Expenditures (CapEx)"]

    cash_flow.loc["Net Debt Raised/(Repaid)"] = inputs.get("debt_raised_repaid", 0)
    cash_flow.loc["Net Equity Issued/(Repurchased)"] = inputs.get("equity_issued_repurchased", 0)
    cash_flow.loc["Cash Flow from Financing (CFF)"] = cash_flow.loc[["Net Debt Raised/(Repaid)", "Net Equity Issued/(Repurchased)"]].sum()

    cash_flow.loc["Net Change in Cash"] = cash_flow.loc[["Cash Flow from Operations (CFO)", "Cash Flow from Investing (CFI)", "Cash Flow from Financing (CFF)"]].sum()

    cash_flow.loc["Beginning Cash Balance", "Year 1"] = inputs.get("initial_cash_balance", 0)
    cash_flow.loc["Ending Cash Balance", "Year 1"] = cash_flow.loc["Beginning Cash Balance", "Year 1"] + cash_flow.loc["Net Change in Cash", "Year 1"]
    cash_flow.loc["Beginning Cash Balance", "Year 2"] = cash_flow.loc["Ending Cash Balance", "Year 1"]
    cash_flow.loc["Ending Cash Balance", "Year 2"] = cash_flow.loc["Beginning Cash Balance", "Year 2"] + cash_flow.loc["Net Change in Cash", "Year 2"]
    cash_flow.loc["Beginning Cash Balance", "Year 3"] = cash_flow.loc["Ending Cash Balance", "Year 2"]
    cash_flow.loc["Ending Cash Balance", "Year 3"] = cash_flow.loc["Beginning Cash Balance", "Year 3"] + cash_flow.loc["Net Change in Cash", "Year 3"]

    # --- Balance Sheet Calculations (Simplified) ---
    # Year 0 (Initial Balances)
    balance_sheet.loc["Cash & Cash Equivalents", "Year 0"] = inputs.get("initial_cash_balance", 0)
    balance_sheet.loc["Accounts Receivable (A/R)", "Year 0"] = inputs.get("initial_accounts_receivable", 0)
    balance_sheet.loc["Inventory", "Year 0"] = inputs.get("initial_inventory", 0)
    balance_sheet.loc["Total Current Assets", "Year 0"] = balance_sheet.loc[["Cash & Cash Equivalents", "Accounts Receivable (A/R)", "Inventory"], "Year 0"].sum()
    
    balance_sheet.loc["PPE, Gross", "Year 0"] = inputs.get("initial_ppe", 0) # Assuming this is gross
    balance_sheet.loc["Accumulated Depreciation", "Year 0"] = -inputs.get("initial_accumulated_depreciation", 0) # Conventionally negative
    balance_sheet.loc["PPE, Net", "Year 0"] = balance_sheet.loc[["PPE, Gross", "Accumulated Depreciation"], "Year 0"].sum()
    balance_sheet.loc["Total Assets", "Year 0"] = balance_sheet.loc[["Total Current Assets", "PPE, Net"], "Year 0"].sum()

    balance_sheet.loc["Accounts Payable (A/P)", "Year 0"] = inputs.get("initial_accounts_payable", 0)
    balance_sheet.loc["Short-Term Debt (Placeholder)", "Year 0"] = 0 # Placeholder
    balance_sheet.loc["Total Current Liabilities", "Year 0"] = balance_sheet.loc[["Accounts Payable (A/P)", "Short-Term Debt (Placeholder)"], "Year 0"].sum()
    balance_sheet.loc["Long-Term Debt", "Year 0"] = inputs.get("initial_long_term_debt", 0)
    balance_sheet.loc["Total Liabilities", "Year 0"] = balance_sheet.loc[["Total Current Liabilities", "Long-Term Debt"], "Year 0"].sum()

    balance_sheet.loc["Common Stock & APIC (Placeholder)", "Year 0"] = inputs.get("initial_equity", 0) # Simplified: initial equity
    balance_sheet.loc["Retained Earnings", "Year 0"] = 0 # Or could be part of initial_equity if specified
    balance_sheet.loc["Total Equity", "Year 0"] = balance_sheet.loc["Common Stock & APIC (Placeholder)", "Year 0"] + balance_sheet.loc["Retained Earnings", "Year 0"]
    
    # If initial_equity is total equity, and we want to derive Common Stock from BS equation:
    # balance_sheet.loc["Total Equity", "Year 0"] = inputs.get("initial_equity", 0)
    # balance_sheet.loc["Common Stock & APIC (Placeholder)", "Year 0"] = balance_sheet.loc["Total Equity", "Year 0"] - balance_sheet.loc["Retained Earnings", "Year 0"]


    balance_sheet.loc["Total Liabilities & Equity", "Year 0"] = balance_sheet.loc["Total Liabilities", "Year 0"] + balance_sheet.loc["Total Equity", "Year 0"]
    balance_sheet.loc["Balance Check (Assets - L&E)", "Year 0"] = balance_sheet.loc["Total Assets", "Year 0"] - balance_sheet.loc["Total Liabilities & Equity", "Year 0"]


    # Projecting BS for Year 1, 2, 3 (Simplified - many items would be driven by assumptions not yet included)
    # For a simple model, NWC changes are given, not derived from AR/Inv/AP changes.
    # This means AR, Inv, AP need simple growth assumptions or are held constant for this MVP.
    ar_growth = inputs.get("revenue_growth_y2",0) # Tie AR growth to revenue growth for simplicity
    inv_growth = inputs.get("revenue_growth_y2",0) # Tie Inv growth to revenue growth / COGS
    ap_growth = inputs.get("revenue_growth_y2",0) # Tie AP growth to COGS / OpEx

    for i, year in enumerate(years):
        prev_year = "Year 0" if i == 0 else years[i-1]

        balance_sheet.loc["Cash & Cash Equivalents", year] = cash_flow.loc["Ending Cash Balance", year]
        
        # Simplified NWC component projections (could be more complex)
        # If change_in_working_capital is an input, these are illustrative.
        # A full model would derive change_in_working_capital from these.
        balance_sheet.loc["Accounts Receivable (A/R)", year] = balance_sheet.loc["Accounts Receivable (A/R)", prev_year] * (1 + ar_growth if i > 0 else 1 + inputs.get("revenue_growth_y2",0)/2) # Simplified growth
        balance_sheet.loc["Inventory", year] = balance_sheet.loc["Inventory", prev_year] * (1 + inv_growth if i > 0 else 1 + inputs.get("revenue_growth_y2",0)/2)
        balance_sheet.loc["Total Current Assets", year] = balance_sheet.loc[["Cash & Cash Equivalents", "Accounts Receivable (A/R)", "Inventory"], year].sum()

        # CapEx input is positive (outflow), representing additions to PPE
        balance_sheet.loc["PPE, Gross", year] = balance_sheet.loc["PPE, Gross", prev_year] + inputs.get("capital_expenditures", 0)
        balance_sheet.loc["Accumulated Depreciation", year] = balance_sheet.loc["Accumulated Depreciation", prev_year] - p_and_l.loc["Depreciation & Amortization (D&A)", year] # D&A is expense, Acc Dep is negative
        balance_sheet.loc["PPE, Net", year] = balance_sheet.loc["PPE, Gross", year] + balance_sheet.loc["Accumulated Depreciation", year]
        balance_sheet.loc["Total Assets", year] = balance_sheet.loc["Total Current Assets", year] + balance_sheet.loc["PPE, Net", year]

        balance_sheet.loc["Accounts Payable (A/P)", year] = balance_sheet.loc["Accounts Payable (A/P)", prev_year] * (1 + ap_growth if i > 0 else 1 + inputs.get("revenue_growth_y2",0)/2)
        balance_sheet.loc["Short-Term Debt (Placeholder)", year] = balance_sheet.loc["Short-Term Debt (Placeholder)", prev_year] # No change assumed
        balance_sheet.loc["Total Current Liabilities", year] = balance_sheet.loc[["Accounts Payable (A/P)", "Short-Term Debt (Placeholder)"], year].sum()
        
        balance_sheet.loc["Long-Term Debt", year] = balance_sheet.loc["Long-Term Debt", prev_year] + cash_flow.loc["Net Debt Raised/(Repaid)", year]
        balance_sheet.loc["Total Liabilities", year] = balance_sheet.loc["Total Current Liabilities", year] + balance_sheet.loc["Long-Term Debt", year]

        balance_sheet.loc["Common Stock & APIC (Placeholder)", year] = balance_sheet.loc["Common Stock & APIC (Placeholder)", prev_year] + cash_flow.loc["Net Equity Issued/(Repurchased)", year]
        balance_sheet.loc["Retained Earnings", year] = balance_sheet.loc["Retained Earnings", prev_year] + p_and_l.loc["Net Income", year]
        balance_sheet.loc["Total Equity", year] = balance_sheet.loc["Common Stock & APIC (Placeholder)", year] + balance_sheet.loc["Retained Earnings", year]
        
        balance_sheet.loc["Total Liabilities & Equity", year] = balance_sheet.loc["Total Liabilities", year] + balance_sheet.loc["Total Equity", year]
        balance_sheet.loc["Balance Check (Assets - L&E)", year] = balance_sheet.loc["Total Assets", year] - balance_sheet.loc["Total Liabilities & Equity", year]

    return {
        "p_and_l": p_and_l.fillna(0),
        "cash_flow": cash_flow.fillna(0),
        "balance_sheet": balance_sheet.fillna(0)
    }


def export_to_excel(financial_statements: dict):
    """
    Exports financial statements to an Excel file in memory.

    Args:
        financial_statements (dict): A dictionary containing P&L, Cash Flow,
                                     and Balance Sheet DataFrames.

    Returns:
        BytesIO: A BytesIO object containing the Excel file data.
    """
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        financial_statements["p_and_l"].to_excel(writer, sheet_name="Profit & Loss")
        financial_statements["cash_flow"].to_excel(writer, sheet_name="Cash Flow Statement")
        financial_statements["balance_sheet"].to_excel(writer, sheet_name="Balance Sheet")
    
    # writer.save() # Not needed with context manager for xlsxwriter >= 0.7.3
    output.seek(0) # Reset pointer to the beginning of the stream
    return output

# Example Usage (for testing this module directly):
if __name__ == '__main__':
    mock_inputs = {
        "revenue_y1": 1000000, "revenue_growth_y2": 0.25, "revenue_growth_y3": 0.20,
        "cogs_percent": 0.45,
        "opex_y1": 250000, "opex_growth_y2": 0.10, "opex_growth_y3": 0.08,
        "tax_rate": 0.21,
        "interest_expense": 20000,
        "depreciation_amortization": 50000,
        "change_in_working_capital": 30000, # Increase in NWC (cash outflow)
        "capital_expenditures": 150000, # Cash outflow
        "debt_raised_repaid": 10000, # Net debt raised (cash inflow)
        "equity_issued_repurchased": 5000, # Net equity issued (cash inflow)
        "initial_cash_balance": 200000,
        "initial_accounts_receivable": 150000,
        "initial_inventory": 100000,
        "initial_accounts_payable": 80000,
        "initial_ppe": 500000, # Gross PPE
        "initial_accumulated_depreciation": 100000, # Positive value, will be made negative
        "initial_long_term_debt": 300000,
        "initial_equity": 470000 # Initial Total Equity (Cash+AR+Inv-AP + NetPPE - LTD)
                                 # 200+150+100-80 + (500-100) - 300 = 170 + 400 - 300 = 270. This is wrong.
                                 # Assets: Cash(200) + AR(150) + Inv(100) + NetPPE(400) = 850
                                 # Liab: AP(80) + LTD(300) = 380
                                 # Equity = Assets - Liab = 850 - 380 = 470. Correct.
    }
    statements = generate_financial_statements(mock_inputs)
    print("--- Profit & Loss ---")
    print(statements["p_and_l"].to_string())
    print("\n--- Cash Flow Statement ---")
    print(statements["cash_flow"].to_string())
    print("\n--- Balance Sheet ---")
    print(statements["balance_sheet"].to_string())

    # Test Excel export
    # excel_bytes = export_to_excel(statements)
    # with open("test_financials.xlsx", "wb") as f:
    #     f.write(excel_bytes.getvalue())
    # print("\nExported to test_financials.xlsx")
