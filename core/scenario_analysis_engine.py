# core/scenario_analysis_engine.py

import json # Still used for formatting parts of prompts
# import yaml # For potential use, though yaml_utils is preferred for parsing
from typing import Dict, Any, Optional, List

from core.llm_interface import LLMInterface
from prompts.scenario_analysis_prompts import (
    SCENARIO_VARIABLE_SUGGESTION_PROMPT,
    # SCENARIO_NARRATIVE_PROMPT, # For future use
)
# from core.utils import extract_json_from_response # No longer needed
from core.yaml_utils import extract_yaml_from_text, load_yaml # Import YAML utilities
from core.assumption_engine import ASSUMPTION_FIELD_DETAILS # For labeling

class ScenarioAnalysisEngine:
    """
    Provides AI-driven suggestions for scenario analysis.
    """

    def __init__(self, llm_interface: LLMInterface):
        self.llm = llm_interface

    def suggest_scenario_variables(
        self,
        business_assumptions: Dict[str, Any],
        model_structure: Dict[str, Any],
        financial_assumptions: Dict[str, Any], # Current fm_inputs
    ) -> Optional[List[str]]:
        """
        Suggests key variables that would be impactful for scenario analysis.

        Args:
            business_assumptions: General business context.
            model_structure: Selected model structure details.
            financial_assumptions: Current financial input values.

        Returns:
            A list of strings, where each string describes a suggested variable and why it's impactful.
            Returns None if suggestion fails.
        """
        if not all([business_assumptions, model_structure, financial_assumptions]):
            return None

        # Use labels for financial assumptions for better LLM understanding
        labeled_financial_assumptions = {
            ASSUMPTION_FIELD_DETAILS.get(k, {"label": k})["label"]: v
            for k, v in financial_assumptions.items()
        }

        prompt = SCENARIO_VARIABLE_SUGGESTION_PROMPT.format(
            business_assumptions_json=json.dumps(business_assumptions, indent=2),
            model_structure_json=json.dumps(model_structure, indent=2),
            financial_assumptions_json=json.dumps(labeled_financial_assumptions, indent=2)
        )
        response_text = self.llm.generate_text(prompt, max_tokens=500)

        if response_text:
            yaml_content = extract_yaml_from_text(response_text)
            if yaml_content:
                suggestion_data = load_yaml(yaml_content)
                if isinstance(suggestion_data, dict) and "suggested_scenario_variables" in suggestion_data:
                    variables = suggestion_data["suggested_scenario_variables"]
                    if isinstance(variables, list):
                        return variables
                    else:
                        print(f"Warning: 'suggested_scenario_variables' is not a list in YAML response. Found: {type(variables)}")
                else:
                    print(f"Warning: Could not parse YAML or 'suggested_scenario_variables' key missing. Raw YAML: {yaml_content[:200]}")
            else:
                print(f"Warning: Could not extract YAML from LLM response in suggest_scenario_variables. Raw response: {response_text[:200]}")
        return None

    # Placeholder for future narrative generation
    # def generate_scenario_narrative(self, ...):
    #     pass

if __name__ == "__main__":
    try:
        llm_api = LLMInterface()
    except Exception as e:
        print(f"Failed to initialize LLMInterface: {e}. Ensure API key is set.")
        llm_api = None

    if llm_api:
        sae = ScenarioAnalysisEngine(llm_interface=llm_api)

        sample_biz_assumptions = {
            "business_model": "E-commerce platform for handmade crafts.",
            "revenue_streams": ["Direct sales", "Premium listings for sellers"],
            "target_market": "Consumers interested in unique gifts, crafters seeking a sales channel."
        }
        sample_model_structure = {
            "template_name": "E-commerce 3-Statement Model",
            "components": ["Assumptions", "Sales Forecast", "COGS", "Marketing Spend", "Income Statement", "Balance Sheet", "Cash Flow"],
            "kpis": ["Average Order Value (AOV)", "Conversion Rate", "Traffic Growth", "Seller Commission Rate"]
        }
        sample_fm_inputs = {
            "revenue_y1": 75000,
            "revenue_growth_y2": 0.80, # 80%
            "cogs_percent": 0.55,      # 55%
            "opex_y1": 25000,
            "opex_growth_y2": 0.15,
            # Adding a key that might be in ASSUMPTION_FIELD_DETAILS for better context
            "initial_inventory": 5000 
        }
        # Ensure all keys in sample_fm_inputs are in ASSUMPTION_FIELD_DETAILS or handle missing ones
        # For this test, we assume ASSUMPTION_FIELD_DETAILS is comprehensive enough or the default label is used.


        print("--- Suggestion for Scenario Variables (E-commerce) ---")
        suggestions = sae.suggest_scenario_variables(
            sample_biz_assumptions, sample_model_structure, sample_fm_inputs
        )
        if suggestions:
            for i, suggestion in enumerate(suggestions):
                print(f"{i+1}. {suggestion}")
        else:
            print("No scenario variable suggestions generated or an error occurred.")

        # Another example: SaaS
        sample_biz_assumptions_saas = {
            "business_model": "B2B SaaS for HR management.",
            "revenue_streams": ["Tiered monthly subscriptions (Basic, Pro, Enterprise)"],
            "cost_structure": "Cloud hosting (AWS), R&D, Sales & Marketing, Customer Support.",
            "target_market": "Medium-sized businesses (50-500 employees)."
        }
        sample_model_structure_saas = {
            "template_name": "SaaS Basic 3-Statement Model",
            "components": ["Assumptions", "Customer Acquisition Funnel", "MRR Forecast", "Income Statement", "Balance Sheet", "Cash Flow"],
            "kpis": ["MRR", "ARR", "CAC", "LTV", "Churn Rate"]
        }
        sample_fm_inputs_saas = {
            "revenue_y1": 250000, # Corresponds to MRR * 12 roughly
            "revenue_growth_y2": 0.60, # 60%
            "cogs_percent": 0.15,      # 15% (typical for SaaS, mostly hosting/support)
            "opex_y1": 100000,
            "opex_growth_y2": 0.25,
        }
        print("\n--- Suggestion for Scenario Variables (SaaS) ---")
        suggestions_saas = sae.suggest_scenario_variables(
            sample_biz_assumptions_saas, sample_model_structure_saas, sample_fm_inputs_saas
        )
        if suggestions_saas:
            for i, suggestion in enumerate(suggestions_saas):
                print(f"{i+1}. {suggestion}")
        else:
            print("No SaaS scenario variable suggestions generated or an error occurred.")
    else:
        print("Skipping ScenarioAnalysisEngine example usage as LLMInterface failed to initialize.")
