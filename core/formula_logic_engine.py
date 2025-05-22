# core/formula_logic_engine.py

import json
from typing import Dict, Any, Optional

from core.llm_interface import LLMInterface
from prompts.formula_logic_prompts import (
    FORMULA_EXPLANATION_PROMPT,
    FINANCIAL_STATEMENT_INTERDEPENDENCY_PROMPT,
)

class FormulaLogicEngine:
    """
    Provides AI-driven explanations for financial formulas, concepts,
    and statement interdependencies.
    """

    def __init__(self, llm_interface: LLMInterface):
        self.llm = llm_interface

    def explain_formula_or_concept(
        self,
        formula_or_concept: str,
        business_assumptions: Dict[str, Any],
        model_structure: Dict[str, Any],
        financial_assumptions: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Provides an LLM-generated explanation for a given financial formula or concept.

        Args:
            formula_or_concept: The specific term the user wants explained (e.g., "NPV", "Depreciation", "EBITDA").
            business_assumptions: General business context.
            model_structure: Selected model structure details.
            financial_assumptions: (Optional) User's current financial inputs for more context.

        Returns:
            A string containing the AI-generated explanation, or None.
        """
        if not all([formula_or_concept, business_assumptions, model_structure]):
            return "Missing context for explanation (formula, business info, or model structure)."

        prompt = FORMULA_EXPLANATION_PROMPT.format(
            business_assumptions_json=json.dumps(business_assumptions, indent=2),
            model_structure_json=json.dumps(model_structure, indent=2),
            financial_assumptions_json=json.dumps(financial_assumptions, indent=2) if financial_assumptions else "N/A",
            formula_or_concept=formula_or_concept
        )
        explanation_text = self.llm.generate_text(prompt, max_tokens=600)
        return explanation_text.strip() if explanation_text else None

    def explain_statement_interdependencies(
        self,
        business_assumptions: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Provides an LLM-generated explanation of how the financial statements link together.

        Args:
            business_assumptions: (Optional) General business context to tailor the example.

        Returns:
            A string containing the AI-generated explanation, or None.
        """
        prompt = FINANCIAL_STATEMENT_INTERDEPENDENCY_PROMPT.format(
            business_assumptions_json=json.dumps(business_assumptions, indent=2) if business_assumptions else "N/A"
        )
        explanation_text = self.llm.generate_text(prompt, max_tokens=800)
        return explanation_text.strip() if explanation_text else None


if __name__ == "__main__":
    try:
        llm_api = LLMInterface()
    except Exception as e:
        print(f"Failed to initialize LLMInterface: {e}. Ensure API key is set.")
        llm_api = None

    if llm_api:
        fle = FormulaLogicEngine(llm_interface=llm_api)

        sample_biz_assumptions = {
            "business_model": "SaaS for small businesses",
            "revenue_streams": ["Monthly subscriptions"],
        }
        sample_model_structure = {
            "template_name": "SaaS Basic 3-Statement Model",
            "components": ["Assumptions", "Revenue Forecast", "Income Statement", "Balance Sheet", "Cash Flow Statement", "SaaS KPIs"],
            "kpis": ["MRR", "CAC", "LTV"]
        }
        sample_fm_inputs = {"revenue_y1": 120000, "opex_y1": 50000}

        print("--- Explanation for 'EBITDA' ---")
        explanation1 = fle.explain_formula_or_concept(
            "EBITDA", sample_biz_assumptions, sample_model_structure, sample_fm_inputs
        )
        print(explanation1 or "No explanation generated.")

        print("\n--- Explanation for 'Working Capital' ---")
        explanation2 = fle.explain_formula_or_concept(
            "Working Capital", sample_biz_assumptions, sample_model_structure
        )
        print(explanation2 or "No explanation generated.")
        
        print("\n--- Explanation for 'Customer Acquisition Cost (CAC)' ---")
        explanation3 = fle.explain_formula_or_concept(
            "Customer Acquisition Cost (CAC)", sample_biz_assumptions, sample_model_structure, sample_fm_inputs
        )
        print(explanation3 or "No explanation generated.")

        print("\n--- Explanation of Financial Statement Interdependencies (SaaS context) ---")
        interdependency_explanation = fle.explain_statement_interdependencies(sample_biz_assumptions)
        print(interdependency_explanation or "No explanation generated.")
        
        print("\n--- Explanation of Financial Statement Interdependencies (General context) ---")
        interdependency_explanation_general = fle.explain_statement_interdependencies()
        print(interdependency_explanation_general or "No explanation generated.")

    else:
        print("Skipping FormulaLogicEngine example usage as LLMInterface failed to initialize.")
