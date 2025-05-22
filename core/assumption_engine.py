# core/assumption_engine.py

import json
from typing import Dict, Any, Optional

from core.llm_interface import LLMInterface
from prompts.assumption_guidance_prompts import (
    ASSUMPTION_INPUT_GUIDANCE_PROMPT,
    ASSUMPTION_REVIEW_PROMPT,
)

# This mapping helps connect form input keys to more descriptive labels for the LLM.
# It should align with st.session_state.fm_inputs keys in the Streamlit page.
ASSUMPTION_FIELD_DETAILS = {
    "revenue_y1": {"label": "Year 1 Revenue", "type": "currency"},
    "revenue_growth_y2": {"label": "Year 2 Revenue Growth Rate", "type": "percentage"},
    "revenue_growth_y3": {"label": "Year 3 Revenue Growth Rate", "type": "percentage"},
    "cogs_percent": {"label": "Cost of Goods Sold (COGS) as % of Revenue", "type": "percentage"},
    "opex_y1": {"label": "Year 1 Operating Expenses (OpEx)", "type": "currency"},
    "opex_growth_y2": {"label": "Year 2 OpEx Growth Rate", "type": "percentage"},
    "opex_growth_y3": {"label": "Year 3 OpEx Growth Rate", "type": "percentage"},
    "tax_rate": {"label": "Effective Tax Rate", "type": "percentage"},
    "interest_expense": {"label": "Annual Interest Expense", "type": "currency"},
    "depreciation_amortization": {"label": "Annual Depreciation & Amortization", "type": "currency"},
    "change_in_working_capital": {"label": "Change in Net Working Capital", "type": "currency"},
    "capital_expenditures": {"label": "Capital Expenditures (CapEx)", "type": "currency"},
    # Add more mappings as new input fields are introduced
}


class AssumptionEngine:
    """
    Provides AI-driven guidance and review for financial assumptions.
    """

    def __init__(self, llm_interface: LLMInterface):
        self.llm = llm_interface

    def get_guidance_for_assumption_field(
        self,
        assumption_field_key: str,
        current_value: Any,
        business_assumptions: Dict[str, Any],
        model_structure: Dict[str, Any],
    ) -> Optional[str]:
        """
        Provides LLM-generated guidance for a specific assumption input field.

        Args:
            assumption_field_key: The key of the assumption field (e.g., "revenue_y1").
            current_value: The current value entered by the user for this field.
            business_assumptions: General business context.
            model_structure: Selected model structure details.

        Returns:
            A string containing AI-generated guidance, or None.
        """
        if not all([assumption_field_key, business_assumptions, model_structure]):
            return "Missing context for guidance (business, model structure, or field key)."

        field_details = ASSUMPTION_FIELD_DETAILS.get(assumption_field_key)
        if not field_details:
            return f"No details found for assumption field: {assumption_field_key}."

        prompt = ASSUMPTION_INPUT_GUIDANCE_PROMPT.format(
            business_assumptions_json=json.dumps(business_assumptions, indent=2),
            model_structure_json=json.dumps(model_structure, indent=2),
            assumption_field_key=assumption_field_key,
            assumption_field_label=field_details["label"],
            current_value=str(current_value) # Ensure it's a string for the prompt
        )
        guidance_text = self.llm.generate_text(prompt, max_tokens=300)
        return guidance_text.strip() if guidance_text else None

    def review_all_assumptions(
        self,
        financial_assumptions: Dict[str, Any], # The st.session_state.fm_inputs
        business_assumptions: Dict[str, Any],
        model_structure: Dict[str, Any],
    ) -> Optional[str]:
        """
        Provides an LLM-based review of the complete set of financial assumptions.

        Args:
            financial_assumptions: The user's entered financial assumptions.
            business_assumptions: General business context.
            model_structure: Selected model structure details.

        Returns:
            A string containing AI-generated review feedback, or None.
        """
        if not all([financial_assumptions, business_assumptions, model_structure]):
            return "Missing context for review (financial inputs, business info, or model structure)."

        # Prepare financial_assumptions with labels for better LLM understanding
        labeled_financial_assumptions = {
            ASSUMPTION_FIELD_DETAILS.get(k, {"label": k})["label"]: v
            for k, v in financial_assumptions.items()
        }

        prompt = ASSUMPTION_REVIEW_PROMPT.format(
            business_assumptions_json=json.dumps(business_assumptions, indent=2),
            model_structure_json=json.dumps(model_structure, indent=2),
            financial_assumptions_json=json.dumps(labeled_financial_assumptions, indent=2)
        )
        review_text = self.llm.generate_text(prompt, max_tokens=500)
        return review_text.strip() if review_text else None


if __name__ == "__main__":
    try:
        llm_api = LLMInterface()
    except Exception as e:
        print(f"Failed to initialize LLMInterface: {e}. Ensure API key is set.")
        llm_api = None

    if llm_api:
        ae = AssumptionEngine(llm_interface=llm_api)

        # Sample data (mimicking session state content)
        sample_biz_assumptions = {
            "business_model": "B2C E-commerce selling custom T-shirts.",
            "revenue_streams": ["Online sales via Shopify"],
            "target_market": "Millennials interested in unique apparel."
        }
        sample_model_structure = {
            "template_id": "ecommerce_3_statement",
            "template_name": "E-commerce 3-Statement Model",
            "components": ["Assumptions", "Sales Forecast", "COGS", "Income Statement", "Balance Sheet", "Cash Flow"],
            "kpis": ["AOV", "Conversion Rate", "CAC"]
        }
        sample_fm_inputs = { # User's current financial inputs
            "revenue_y1": 50000,
            "revenue_growth_y2": 1.50, # 150%
            "cogs_percent": 0.60 # 60%
        }

        print("--- Guidance for 'Year 1 Revenue' ---")
        guidance1 = ae.get_guidance_for_assumption_field(
            "revenue_y1", 50000, sample_biz_assumptions, sample_model_structure
        )
        print(guidance1 or "No guidance generated.")

        print("\n--- Guidance for 'COGS %' (with high value) ---")
        guidance2 = ae.get_guidance_for_assumption_field(
            "cogs_percent", 0.95, sample_biz_assumptions, sample_model_structure # 95% COGS
        )
        print(guidance2 or "No guidance generated.")
        
        print("\n--- Guidance for 'Year 2 Revenue Growth Rate' ---")
        guidance3 = ae.get_guidance_for_assumption_field(
            "revenue_growth_y2", "150%", sample_biz_assumptions, sample_model_structure
        )
        print(guidance3 or "No guidance generated.")

        print("\n--- Review of All Assumptions ---")
        review = ae.review_all_assumptions(
            sample_fm_inputs, sample_biz_assumptions, sample_model_structure
        )
        print(review or "No review generated.")
        
        # Test with a more aggressive assumption
        sample_fm_inputs_aggressive = {
             "revenue_y1": 10000,
             "revenue_growth_y2": 5.00, # 500% growth
             "revenue_growth_y3": 3.00, # 300% growth
             "cogs_percent": 0.20, # Very low COGS
             "opex_y1": 5000,
        }
        print("\n--- Review of Aggressive Assumptions ---")
        review_aggressive = ae.review_all_assumptions(
            sample_fm_inputs_aggressive, sample_biz_assumptions, sample_model_structure
        )
        print(review_aggressive or "No review generated.")

    else:
        print("Skipping AssumptionEngine example usage as LLMInterface failed to initialize.")
