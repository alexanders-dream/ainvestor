# core/model_structuring_logic.py

import json
from typing import Dict, Any, Optional, List

from core.llm_interface import LLMInterface
from prompts.model_structuring_prompts import (
    MODEL_TEMPLATE_SUGGESTION_PROMPT,
    MODEL_COMPONENT_GUIDANCE_PROMPT,
)
# from core.utils import extract_json_from_response # No longer needed
from core.yaml_utils import extract_yaml_from_text, load_yaml # Import YAML utilities

# Predefined library of financial model templates
# In a real application, this could be loaded from a YAML/JSON file or a database
AVAILABLE_MODEL_TEMPLATES = {
    "general_3_statement": {
        "name": "General 3-Statement Model",
        "description": "A standard model including Income Statement, Balance Sheet, and Cash Flow Statement. Suitable for most business types as a starting point.",
        "components": ["Assumptions", "Income Statement", "Balance Sheet", "Cash Flow Statement", "Supporting Schedules", "Summary & KPIs"],
        "default_kpis": ["Revenue Growth Rate", "Gross Profit Margin", "Net Profit Margin", "Current Ratio", "Debt-to-Equity Ratio"]
    },
    "saas_3_statement_basic": {
        "name": "SaaS Basic 3-Statement Model",
        "description": "A 3-statement model tailored for SaaS businesses, focusing on recurring revenue and key SaaS metrics.",
        "components": ["Assumptions", "User/Customer Forecast", "Revenue Forecast (MRR, ARR)", "COGS/COS", "Operating Expenses", "Income Statement", "Balance Sheet", "Cash Flow Statement", "SaaS KPIs"],
        "default_kpis": ["Monthly Recurring Revenue (MRR)", "Annual Recurring Revenue (ARR)", "Customer Acquisition Cost (CAC)", "Customer Lifetime Value (CLTV)", "Churn Rate", "ARPU/ARPA"]
    },
    "ecommerce_3_statement": {
        "name": "E-commerce 3-Statement Model",
        "description": "A model for e-commerce businesses, emphasizing inventory, COGS, marketing spend, and customer acquisition.",
        "components": ["Assumptions", "Traffic & Conversion Funnel", "Sales Forecast", "COGS (per unit/category)", "Marketing Budget", "Operating Expenses", "Income Statement", "Balance Sheet (incl. Inventory)", "Cash Flow Statement", "E-commerce KPIs"],
        "default_kpis": ["Average Order Value (AOV)", "Conversion Rate", "Customer Acquisition Cost (CAC)", "Inventory Turnover", "Gross Margin per Sale"]
    },
    "service_business_simple": {
        "name": "Service Business Simple P&L",
        "description": "A simpler model focusing on Profit & Loss for service-based businesses with less complex balance sheets (e.g., consulting, freelance).",
        "components": ["Assumptions", "Service Packages/Rates", "Client/Project Forecast", "Revenue Forecast", "Direct Costs (if any)", "Operating Expenses", "Income Statement", "Key Service KPIs"],
        "default_kpis": ["Billable Hours/Projects", "Average Revenue per Client/Project", "Utilization Rate", "Project Margin"]
    }
    # Add more templates as needed (e.g., manufacturing, real estate)
}

class ModelStructuringLogic:
    """
    Handles AI-driven logic for suggesting financial model structures and templates.
    """

    def __init__(self, llm_interface: LLMInterface):
        self.llm = llm_interface

    def get_available_templates_summary(self) -> Dict[str, str]:
        """Returns a summary of available templates (ID and name)."""
        return {id: data["name"] for id, data in AVAILABLE_MODEL_TEMPLATES.items()}

    def get_template_details(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Returns details for a specific template ID."""
        return AVAILABLE_MODEL_TEMPLATES.get(template_id)

    def suggest_model_template(self, business_assumptions: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Suggests a model template based on business assumptions using an LLM.

        Args:
            business_assumptions: A dictionary of business information.

        Returns:
            A dictionary containing the suggested template ID, reasoning, components, and KPIs,
            or None if suggestion fails.
        """
        if not business_assumptions:
            return None

        # Provide the LLM with a simplified list of templates for its context
        templates_for_prompt = {
            id: {"name": data["name"], "description": data["description"]}
            for id, data in AVAILABLE_MODEL_TEMPLATES.items()
        }

        prompt = MODEL_TEMPLATE_SUGGESTION_PROMPT.format(
            business_assumptions_json=json.dumps(business_assumptions, indent=2),
            available_templates_json=json.dumps(templates_for_prompt, indent=2)
        )
        response_text = self.llm.generate_text(prompt, max_tokens=1200)

        if response_text:
            yaml_content = extract_yaml_from_text(response_text)
            if yaml_content:
                suggestion_data = load_yaml(yaml_content)
                if isinstance(suggestion_data, dict):
                    # Further validation: ensure recommended_template_id exists if provided
                    if suggestion_data.get("recommended_template_id"):
                        if suggestion_data["recommended_template_id"] not in AVAILABLE_MODEL_TEMPLATES:
                            # If LLM hallucinates a template_id, default to general
                            suggestion_data["reasoning"] = suggestion_data.get("reasoning", "") + \
                                                           f" (LLM suggested non-existent ID '{suggestion_data['recommended_template_id']}', defaulting to general)."
                            suggestion_data["recommended_template_id"] = "general_3_statement"
                        return suggestion_data
                    elif suggestion_data: # LLM provided YAML dict but maybe not a specific template_id
                        return suggestion_data
            else:
                # Fallback or error logging if YAML extraction fails
                print(f"Warning: Could not extract YAML from LLM response in ModelStructuringLogic. Response: {response_text[:200]}")


        return None

    def get_component_guidance(
        self,
        business_assumptions: Dict[str, Any],
        model_structure: Dict[str, Any], # This would be the output from suggest_model_template
        component_name: str
    ) -> Optional[str]:
        """
        Provides LLM-generated guidance for a specific model component.

        Args:
            business_assumptions: The business context.
            model_structure: The currently selected/suggested model structure.
            component_name: The name of the component to get guidance for.

        Returns:
            A string containing AI-generated guidance, or None.
        """
        if not all([business_assumptions, model_structure, component_name]):
            return None

        prompt = MODEL_COMPONENT_GUIDANCE_PROMPT.format(
            business_assumptions_json=json.dumps(business_assumptions, indent=2),
            model_structure_json=json.dumps(model_structure, indent=2),
            component_name=component_name
        )
        guidance_text = self.llm.generate_text(prompt, max_tokens=800)
        return guidance_text.strip() if guidance_text else None


if __name__ == "__main__":
    try:
        llm_api = LLMInterface()
    except Exception as e:
        print(f"Failed to initialize LLMInterface: {e}. Ensure API key is set.")
        llm_api = None

    if llm_api:
        ms_logic = ModelStructuringLogic(llm_interface=llm_api)

        print("Available Model Templates:")
        print(json.dumps(ms_logic.get_available_templates_summary(), indent=2))

        sample_business_assumptions_saas = {
            "business_model": "B2B SaaS platform for project management.",
            "revenue_streams": ["Monthly subscriptions (tiered)", "Annual subscriptions (discounted)"],
            "cost_structure": "Cloud hosting, R&D (salaries), Sales & Marketing, Customer Support.",
            "target_market": "Small to medium-sized businesses (SMBs) globally.",
            "problem_solved": "Inefficient project tracking and collaboration in remote teams.",
            "solution_offered": "An intuitive, AI-enhanced project management tool.",
            "competitive_advantage": "AI-powered task scheduling and predictive analytics."
        }

        sample_business_assumptions_ecommerce = {
            "business_model": "Direct-to-consumer (DTC) e-commerce selling handmade artisanal goods.",
            "revenue_streams": ["Online sales of physical products."],
            "cost_structure": "Cost of goods sold (materials, labor), Shopify platform fees, marketing (social media ads, influencers), shipping & handling, payment processing fees.",
            "target_market": "Consumers aged 25-45 interested in unique, sustainable products.",
            "problem_solved": "Lack of access to high-quality, ethically sourced handmade goods.",
            "solution_offered": "A curated online marketplace with verified artisans and transparent sourcing."
        }

        print("\n--- SaaS Business Template Suggestion ---")
        saas_suggestion = ms_logic.suggest_model_template(sample_business_assumptions_saas)
        if saas_suggestion:
            print(json.dumps(saas_suggestion, indent=2))
            if saas_suggestion.get("essential_components"):
                comp_to_explain = saas_suggestion["essential_components"][0] # Explain the first one
                print(f"\n--- Guidance for Component: '{comp_to_explain}' (SaaS) ---")
                guidance = ms_logic.get_component_guidance(sample_business_assumptions_saas, saas_suggestion, comp_to_explain)
                print(guidance or "No guidance generated.")
        else:
            print("Failed to get SaaS template suggestion.")

        print("\n--- E-commerce Business Template Suggestion ---")
        ecommerce_suggestion = ms_logic.suggest_model_template(sample_business_assumptions_ecommerce)
        if ecommerce_suggestion:
            print(json.dumps(ecommerce_suggestion, indent=2))
            if ecommerce_suggestion.get("suggested_kpis"):
                # Let's try getting guidance for a KPI if it's treated as a component
                kpi_to_explain = ecommerce_suggestion["suggested_kpis"][0]
                print(f"\n--- Guidance for KPI (as component): '{kpi_to_explain}' (E-commerce) ---")
                # Note: The prompt might need adjustment if "component_name" is strictly for sections like "Income Statement"
                # For this test, we'll see how it handles a KPI name.
                guidance = ms_logic.get_component_guidance(sample_business_assumptions_ecommerce, ecommerce_suggestion, kpi_to_explain)
                print(guidance or "No guidance generated.")
        else:
            print("Failed to get E-commerce template suggestion.")
    else:
        print("Skipping ModelStructuringLogic example usage as LLMInterface failed to initialize.")
