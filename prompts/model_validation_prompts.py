# prompts/model_validation_prompts.py

# flake8: noqa E501

MODEL_REASONABLENESS_REVIEW_PROMPT = """
You are an expert financial analyst AI. Your task is to review a generated financial model for overall reasonableness, logical consistency, and potential red flags.

Business Context:
---
{business_assumptions_json}
---

Selected Model Structure:
---
{model_structure_json}
---

User's Key Financial Assumptions:
---
{financial_assumptions_json} 
---

Generated Financial Statements Summary (Key Metrics over 3 Years - Y1, Y2, Y3):
---
Income Statement Highlights:
  Revenue: {pnl_revenue_y1}, {pnl_revenue_y2}, {pnl_revenue_y3}
  COGS: {pnl_cogs_y1}, {pnl_cogs_y2}, {pnl_cogs_y3}
  Gross Profit: {pnl_gp_y1}, {pnl_gp_y2}, {pnl_gp_y3}
  Operating Expenses: {pnl_opex_y1}, {pnl_opex_y2}, {pnl_opex_y3}
  EBITDA: {pnl_ebitda_y1}, {pnl_ebitda_y2}, {pnl_ebitda_y3}
  Net Income: {pnl_net_income_y1}, {pnl_net_income_y2}, {pnl_net_income_y3}

Cash Flow Statement Highlights:
  Cash Flow from Operations (CFO): {cf_cfo_y1}, {cf_cfo_y2}, {cf_cfo_y3}
  Cash Flow from Investing (CFI): {cf_cfi_y1}, {cf_cfi_y2}, {cf_cfi_y3}
  Cash Flow from Financing (CFF): {cf_cff_y1}, {cf_cff_y2}, {cf_cff_y3}
  Ending Cash Balance: {cf_end_cash_y1}, {cf_end_cash_y2}, {cf_end_cash_y3}

Balance Sheet Highlights (End of Year):
  Total Assets (Y1, Y2, Y3): {bs_assets_y1}, {bs_assets_y2}, {bs_assets_y3}
  Total Liabilities (Y1, Y2, Y3): {bs_liabilities_y1}, {bs_liabilities_y2}, {bs_liabilities_y3}
  Total Equity (Y1, Y2, Y3): {bs_equity_y1}, {bs_equity_y2}, {bs_equity_y3}
  Balance Check (Assets - L&E) (Y1, Y2, Y3): {bs_check_y1}, {bs_check_y2}, {bs_check_y3} 
---

Review Checklist & Considerations:
1.  **Growth Trajectory:** Is revenue growth consistent with OpEx growth? Rapid revenue growth usually requires increased OpEx (marketing, sales, R&D). Are there any years where OpEx grows significantly faster than revenue without clear justification (e.g., major product launch planned)?
2.  **Profitability Margins:** Are Gross Profit Margin and Net Profit Margin trends plausible? Do they improve, decline, or stay stable? Are these margins typical for the industry/business model described in the business context? (e.g., SaaS often has high gross margins).
3.  **Cash Flow Health:** Is the business generating positive Cash Flow from Operations? If not, is there a clear path to it? Is the Ending Cash Balance dangerously low or negative at any point? Does the cash balance trend make sense given investments (CFI) and financing (CFF)?
4.  **Capital Structure:** How is the Debt-to-Equity ratio evolving (if applicable)? Does the model rely heavily on debt or equity financing?
5.  **Specific Assumptions vs. Outcomes:** Do any of the user's key financial assumptions (e.g., high growth rate, low COGS %) lead to outcomes that seem overly optimistic or unrealistic without strong backing from the business context?
6.  **Balance Sheet Sanity:** (The Balance Check is provided). Are there any other glaring issues like negative equity (unless it's a very early-stage startup with accumulated losses)?

Provide a concise (3-5 bullet points) review focusing on:
-   Positive aspects or areas that look reasonable.
-   Potential areas of concern or assumptions that might need re-evaluation by the user.
-   Any apparent inconsistencies between assumptions and outcomes.

Be constructive and aim to help the user build a more robust model.

AI Model Reasonableness Review:
"""
