# core/model_validation_engine.py

import json
from typing import Dict, Any, Optional
import pandas as pd

from core.llm_interface import LLMInterface
from prompts.model_validation_prompts import MODEL_REASONABLENESS_REVIEW_PROMPT
from core.assumption_engine import ASSUMPTION_FIELD_DETAILS # For labeling financial_assumptions

class ModelValidationEngine:
    """
    Provides AI-driven review of generated financial models for reasonableness.
    """

    def __init__(self, llm_interface: LLMInterface):
        self.llm = llm_interface

    def _extract_metrics_for_prompt(self, statements: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
        """Helper to extract key metrics from statement DataFrames for the LLM prompt."""
        metrics = {}
        years = ["Year 1", "Year 2", "Year 3"] # Assuming these columns exist

        # P&L
        pnl = statements.get("p_and_l", pd.DataFrame())
        for y_idx, year_col in enumerate(years):
            metrics[f"pnl_revenue_y{y_idx+1}"] = pnl.loc["Revenue", year_col] if "Revenue" in pnl.index and year_col in pnl.columns else "N/A"
            metrics[f"pnl_cogs_y{y_idx+1}"] = pnl.loc["COGS", year_col] if "COGS" in pnl.index and year_col in pnl.columns else "N/A"
            metrics[f"pnl_gp_y{y_idx+1}"] = pnl.loc["Gross Profit", year_col] if "Gross Profit" in pnl.index and year_col in pnl.columns else "N/A"
            metrics[f"pnl_opex_y{y_idx+1}"] = pnl.loc["Total Operating Expenses", year_col] if "Total Operating Expenses" in pnl.index and year_col in pnl.columns else "N/A"
            metrics[f"pnl_ebitda_y{y_idx+1}"] = pnl.loc["EBITDA", year_col] if "EBITDA" in pnl.index and year_col in pnl.columns else "N/A"
            metrics[f"pnl_net_income_y{y_idx+1}"] = pnl.loc["Net Income", year_col] if "Net Income" in pnl.index and year_col in pnl.columns else "N/A"

        # Cash Flow
        cf = statements.get("cash_flow", pd.DataFrame())
        for y_idx, year_col in enumerate(years):
            metrics[f"cf_cfo_y{y_idx+1}"] = cf.loc["Cash Flow from Operations (CFO)", year_col] if "Cash Flow from Operations (CFO)" in cf.index and year_col in cf.columns else "N/A"
            metrics[f"cf_cfi_y{y_idx+1}"] = cf.loc["Cash Flow from Investing (CFI)", year_col] if "Cash Flow from Investing (CFI)" in cf.index and year_col in cf.columns else "N/A"
            metrics[f"cf_cff_y{y_idx+1}"] = cf.loc["Cash Flow from Financing (CFF)", year_col] if "Cash Flow from Financing (CFF)" in cf.index and year_col in cf.columns else "N/A"
            metrics[f"cf_end_cash_y{y_idx+1}"] = cf.loc["Ending Cash Balance", year_col] if "Ending Cash Balance" in cf.index and year_col in cf.columns else "N/A"

        # Balance Sheet
        bs = statements.get("balance_sheet", pd.DataFrame())
        for y_idx, year_col in enumerate(years):
            metrics[f"bs_assets_y{y_idx+1}"] = bs.loc["Total Assets", year_col] if "Total Assets" in bs.index and year_col in bs.columns else "N/A"
            metrics[f"bs_liabilities_y{y_idx+1}"] = bs.loc["Total Liabilities", year_col] if "Total Liabilities" in bs.index and year_col in bs.columns else "N/A"
            metrics[f"bs_equity_y{y_idx+1}"] = bs.loc["Total Equity", year_col] if "Total Equity" in bs.index and year_col in bs.columns else "N/A"
            metrics[f"bs_check_y{y_idx+1}"] = bs.loc["Balance Check (Assets - L&E)", year_col] if "Balance Check (Assets - L&E)" in bs.index and year_col in bs.columns else "N/A"
        
        return metrics


    def review_model_reasonableness(
        self,
        business_assumptions: Dict[str, Any],
        model_structure: Dict[str, Any],
        financial_assumptions: Dict[str, Any], # User's fm_inputs
        generated_statements: Dict[str, pd.DataFrame] # The actual P&L, BS, CF DataFrames
    ) -> Optional[str]:
        """
        Provides an LLM-based review of the generated financial model for reasonableness.

        Args:
            business_assumptions: General business context.
            model_structure: Selected model structure details.
            financial_assumptions: User's key input assumptions.
            generated_statements: Dictionary of Pandas DataFrames for P&L, BS, CF.

        Returns:
            A string containing AI-generated review feedback, or None.
        """
        if not all([business_assumptions, model_structure, financial_assumptions, generated_statements]):
            return "Missing context for model review."

        labeled_financial_assumptions = {
            ASSUMPTION_FIELD_DETAILS.get(k, {"label": k})["label"]: v
            for k, v in financial_assumptions.items()
        }
        
        statement_summary_metrics = self._extract_metrics_for_prompt(generated_statements)

        prompt_format_args = {
            "business_assumptions_json": json.dumps(business_assumptions, indent=2),
            "model_structure_json": json.dumps(model_structure, indent=2),
            "financial_assumptions_json": json.dumps(labeled_financial_assumptions, indent=2),
            **statement_summary_metrics # Unpack all metric placeholders
        }
        
        prompt = MODEL_REASONABLENESS_REVIEW_PROMPT.format(**prompt_format_args)
        
        review_text = self.llm.generate_text(prompt, max_tokens=700)
        return review_text.strip() if review_text else None


if __name__ == "__main__":
    try:
        llm_api = LLMInterface()
    except Exception as e:
        print(f"Failed to initialize LLMInterface: {e}. Ensure API key is set.")
        llm_api = None

    if llm_api:
        mve = ModelValidationEngine(llm_interface=llm_api)

        # Sample data (mimicking session state content and generated statements)
        sample_biz_assumptions = {
            "business_model": "Subscription box for eco-friendly products.",
            "revenue_streams": ["Monthly subscription fees"],
            "target_market": "Environmentally conscious consumers."
        }
        sample_model_structure = {
            "template_name": "SaaS Basic 3-Statement Model", # Using SaaS as an example structure
            "components": ["Assumptions", "Revenue", "COGS", "OpEx", "P&L", "BS", "CF"],
            "kpis": ["MRR", "Churn", "CAC"]
        }
        sample_fm_inputs = {
            "revenue_y1": 60000, "revenue_growth_y2": 0.7, "revenue_growth_y3": 0.5,
            "cogs_percent": 0.45,
            "opex_y1": 25000, "opex_growth_y2": 0.2, "opex_growth_y3": 0.15,
            "tax_rate": 0.0, # Early stage, no profit tax
        }

        # Create dummy DataFrames for generated_statements
        # In a real scenario, these would come from financial_model_logic.py
        years = ["Year 1", "Year 2", "Year 3"]
        pnl_data = {
            "Revenue": [60000, 102000, 153000], "COGS": [27000, 45900, 68850],
            "Gross Profit": [33000, 56100, 84150], "Total Operating Expenses": [25000, 28750, 33063],
            "EBITDA": [8000, 27350, 51088], "Net Income": [5000, 15000, 30000] # Simplified
        }
        cf_data = {
            "Cash Flow from Operations (CFO)": [7000, 18000, 35000],
            "Cash Flow from Investing (CFI)": [-5000, -5000, -5000],
            "Cash Flow from Financing (CFF)": [10000, 0, -2000],
            "Ending Cash Balance": [50000, 63000, 91000]
        }
        bs_data = {
            "Total Assets": [70000, 85000, 115000],
            "Total Liabilities": [15000, 12000, 10000],
            "Total Equity": [55000, 73000, 105000],
            "Balance Check (Assets - L&E)": [0,0,0]
        }
        sample_statements = {
            "p_and_l": pd.DataFrame(pnl_data, index=pd.Index(pnl_data.keys()).str.replace("_", " ").str.title(), columns=years).T.reindex(pnl_data.keys()).T, # More robust creation
            "cash_flow": pd.DataFrame(cf_data, index=pd.Index(cf_data.keys()), columns=years).T.reindex(cf_data.keys()).T,
            "balance_sheet": pd.DataFrame(bs_data, index=pd.Index(bs_data.keys()), columns=years).T.reindex(bs_data.keys()).T
        }
        # Correcting DataFrame creation to match expected structure (index as items, columns as Years)
        idx_pnl = ["Revenue", "COGS", "Gross Profit", "Total Operating Expenses", "EBITDA", "Net Income"]
        idx_cf = ["Cash Flow from Operations (CFO)", "Cash Flow from Investing (CFI)", "Cash Flow from Financing (CFF)", "Ending Cash Balance"]
        idx_bs = ["Total Assets", "Total Liabilities", "Total Equity", "Balance Check (Assets - L&E)"]

        sample_statements["p_and_l"] = pd.DataFrame(list(zip(*[pnl_data[key] for key in idx_pnl])), index=years, columns=idx_pnl).T
        sample_statements["cash_flow"] = pd.DataFrame(list(zip(*[cf_data[key] for key in idx_cf])), index=years, columns=idx_cf).T
        sample_statements["balance_sheet"] = pd.DataFrame(list(zip(*[bs_data[key] for key in idx_bs])), index=years, columns=idx_bs).T


        print("--- Model Reasonableness Review ---")
        review = mve.review_model_reasonableness(
            sample_biz_assumptions, sample_model_structure, sample_fm_inputs, sample_statements
        )
        print(review or "No review generated.")
        
        # Example with potentially problematic assumption (e.g., OpEx shrinking while revenue grows)
        sample_fm_inputs_issue = sample_fm_inputs.copy()
        sample_fm_inputs_issue["opex_growth_y2"] = -0.1 # OpEx shrinks
        pnl_data_issue = pnl_data.copy()
        pnl_data_issue["Total Operating Expenses"] = [25000, 22500, 20250] # OpEx decreasing
        pnl_data_issue["Net Income"] = [6000, 20000, 40000] # Net income higher due to lower OpEx
        
        sample_statements_issue = sample_statements.copy()
        sample_statements_issue["p_and_l"] = pd.DataFrame(list(zip(*[pnl_data_issue[key] for key in idx_pnl])), index=years, columns=idx_pnl).T


        print("\n--- Model Reasonableness Review (with OpEx issue) ---")
        review_issue = mve.review_model_reasonableness(
            sample_biz_assumptions, sample_model_structure, sample_fm_inputs_issue, sample_statements_issue
        )
        print(review_issue or "No review generated.")

    else:
        print("Skipping ModelValidationEngine example usage as LLMInterface failed to initialize.")
