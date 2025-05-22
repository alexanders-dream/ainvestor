# core/interpretation_engine.py

import json
from typing import Dict, Any, Optional, List
import pandas as pd

from core.llm_interface import LLMInterface
from prompts.interpretation_presentation_prompts import (
    KPI_EXPLANATION_PROMPT,
    FINANCIAL_SUMMARY_NARRATIVE_PROMPT,
)
from core.assumption_engine import ASSUMPTION_FIELD_DETAILS # For labeling financial_assumptions

class InterpretationEngine:
    """
    Provides AI-driven interpretation of financial models, including KPI explanations
    and summary narratives.
    """

    def __init__(self, llm_interface: LLMInterface):
        self.llm = llm_interface

    def explain_kpi(
        self,
        kpi_name: str,
        business_assumptions: Dict[str, Any],
        model_structure: Dict[str, Any], # Contains list of selected KPIs
        kpi_value: Optional[str] = "N/A", # e.g., "15%" or "12000"
    ) -> Optional[str]:
        """
        Provides an LLM-generated explanation for a given KPI.

        Args:
            kpi_name: The name of the KPI to explain.
            business_assumptions: General business context.
            model_structure: Selected model structure, including the list of relevant KPIs.
            kpi_value: (Optional) The calculated value of the KPI for context.

        Returns:
            A string containing the AI-generated explanation, or None.
        """
        if not all([kpi_name, business_assumptions, model_structure]):
            return "Missing context for KPI explanation."

        # Extract business type for better contextualization if possible
        business_type = business_assumptions.get("business_model", "general business")


        prompt = KPI_EXPLANATION_PROMPT.format(
            business_assumptions_json=json.dumps(business_assumptions, indent=2),
            model_structure_json=json.dumps(model_structure, indent=2),
            kpi_name=kpi_name,
            kpi_value=str(kpi_value),
            business_type_from_context=business_type
        )
        explanation_text = self.llm.generate_text(prompt, max_tokens=500)
        return explanation_text.strip() if explanation_text else None

    def _prepare_narrative_prompt_metrics(
        self,
        statements: Dict[str, pd.DataFrame],
        kpis_from_model_structure: List[str] # List of KPI names from final_model_structure
        ) -> Dict[str, Any]:
        """Helper to extract and calculate key metrics for the narrative prompt."""
        metrics = {}
        years = ["Year 1", "Year 2", "Year 3"]
        pnl = statements.get("p_and_l", pd.DataFrame())

        # P&L Metrics
        for i, year in enumerate(years):
            rev = pnl.loc["Revenue", year] if "Revenue" in pnl.index and year in pnl.columns else 0
            gp = pnl.loc["Gross Profit", year] if "Gross Profit" in pnl.index and year in pnl.columns else 0
            ni = pnl.loc["Net Income", year] if "Net Income" in pnl.index and year in pnl.columns else 0
            
            metrics[f"pnl_revenue_y{i+1}"] = f"{rev:,.0f}"
            metrics[f"pnl_net_income_y{i+1}"] = f"{ni:,.0f}"
            if i == 0 or i == 2: # Y1 and Y3 for margins
                metrics[f"pnl_gp_margin_y{i+1}"] = f"{(gp / rev * 100) if rev else 0:.1f}"
                metrics[f"pnl_npm_margin_y{i+1}"] = f"{(ni / rev * 100) if rev else 0:.1f}"
        
        # Cash Flow Metrics
        cf = statements.get("cash_flow", pd.DataFrame())
        cfo_sum = 0
        for i, year in enumerate(years):
            cfo = cf.loc["Cash Flow from Operations (CFO)", year] if "Cash Flow from Operations (CFO)" in cf.index and year in cf.columns else 0
            end_cash = cf.loc["Ending Cash Balance", year] if "Ending Cash Balance" in cf.index and year in cf.columns else 0
            metrics[f"cf_cfo_y{i+1}"] = f"{cfo:,.0f}"
            metrics[f"cf_end_cash_y{i+1}"] = f"{end_cash:,.0f}"
            cfo_sum += cfo
        metrics["cf_cumulative_cfo_y1_y3"] = f"{cfo_sum:,.0f}"

        # KPI Summary (simplified - assumes KPIs are directly calculable or already in a summary)
        # This part would need more robust KPI calculation logic in a full system
        kpi_summary = {}
        # For now, we'll just list the KPIs from model_structure.
        # A real implementation would calculate/fetch their Y3 values.
        for kpi_name in kpis_from_model_structure:
            kpi_summary[f"{kpi_name} Y3"] = "Value N/A" # Placeholder
        metrics["kpi_summary_json"] = json.dumps(kpi_summary)
        
        return metrics

    def generate_financial_summary_narrative(
        self,
        business_assumptions: Dict[str, Any],
        model_structure: Dict[str, Any], # Includes selected KPIs
        financial_assumptions: Dict[str, Any], # User's fm_inputs
        generated_statements: Dict[str, pd.DataFrame]
    ) -> Optional[str]:
        """
        Generates an AI-powered narrative summarizing the financial model.
        """
        if not all([business_assumptions, model_structure, financial_assumptions, generated_statements]):
            return "Missing context for summary narrative."

        labeled_financial_assumptions = {
            ASSUMPTION_FIELD_DETAILS.get(k, {"label": k})["label"]: v
            for k, v in financial_assumptions.items()
        }
        
        narrative_metrics = self._prepare_narrative_prompt_metrics(
            generated_statements,
            model_structure.get("kpis", [])
        )

        prompt_format_args = {
            "business_assumptions_json": json.dumps(business_assumptions, indent=2),
            "financial_assumptions_json": json.dumps(labeled_financial_assumptions, indent=2),
            **narrative_metrics
        }
        
        prompt = FINANCIAL_SUMMARY_NARRATIVE_PROMPT.format(**prompt_format_args)
        narrative_text = self.llm.generate_text(prompt, max_tokens=400) # Increased for 2-3 paras
        return narrative_text.strip() if narrative_text else None


if __name__ == "__main__":
    try:
        llm_api = LLMInterface()
    except Exception as e:
        print(f"Failed to initialize LLMInterface: {e}. Ensure API key is set.")
        llm_api = None

    if llm_api:
        ie = InterpretationEngine(llm_interface=llm_api)

        sample_biz_assumptions = {
            "business_model": "Direct-to-Consumer (DTC) E-commerce selling sustainable home goods.",
            "revenue_streams": ["Online product sales"],
            "target_market": "Eco-conscious millennials and Gen Z."
        }
        sample_model_structure = {
            "template_name": "E-commerce 3-Statement Model",
            "components": ["Assumptions", "Sales Forecast", "COGS", "Income Statement", "Balance Sheet", "Cash Flow"],
            "kpis": ["Average Order Value (AOV)", "Conversion Rate", "Customer Acquisition Cost (CAC)", "Gross Profit Margin"]
        }
        sample_fm_inputs = { # User's key inputs
            "revenue_y1": 150000, "revenue_growth_y2": 0.6, "revenue_growth_y3": 0.4,
            "cogs_percent": 0.50, "opex_y1": 60000
        }
        
        # Dummy generated statements
        years = ["Year 1", "Year 2", "Year 3"]
        pnl_data = {"Revenue": [150000, 240000, 336000], "COGS": [75000, 120000, 168000],
                    "Gross Profit": [75000, 120000, 168000], "Total Operating Expenses": [60000, 72000, 82800],
                    "Net Income": [10000, 35000, 60000]}
        cf_data = {"Cash Flow from Operations (CFO)": [12000, 40000, 65000], "Ending Cash Balance": [50000, 80000, 130000]}
        
        idx_pnl = ["Revenue", "COGS", "Gross Profit", "Total Operating Expenses", "Net Income"]
        idx_cf = ["Cash Flow from Operations (CFO)", "Ending Cash Balance"]
        sample_statements = {
            "p_and_l": pd.DataFrame(list(zip(*[pnl_data[key] for key in idx_pnl])), index=years, columns=idx_pnl).T,
            "cash_flow": pd.DataFrame(list(zip(*[cf_data[key] for key in idx_cf])), index=years, columns=idx_cf).T
        }


        print("--- KPI Explanation for 'Average Order Value (AOV)' ---")
        kpi_expl = ie.explain_kpi("Average Order Value (AOV)", sample_biz_assumptions, sample_model_structure, kpi_value="120 USD")
        print(kpi_expl or "No KPI explanation generated.")

        print("\n--- KPI Explanation for 'Customer Acquisition Cost (CAC)' ---")
        kpi_expl_cac = ie.explain_kpi("Customer Acquisition Cost (CAC)", sample_biz_assumptions, sample_model_structure)
        print(kpi_expl_cac or "No KPI explanation generated.")

        print("\n--- Financial Summary Narrative ---")
        narrative = ie.generate_financial_summary_narrative(
            sample_biz_assumptions, sample_model_structure, sample_fm_inputs, sample_statements
        )
        print(narrative or "No narrative generated.")
    else:
        print("Skipping InterpretationEngine example usage.")
