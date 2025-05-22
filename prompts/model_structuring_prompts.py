# prompts/model_structuring_prompts.py

# flake8: noqa E501

MODEL_TEMPLATE_SUGGESTION_PROMPT = """
You are an expert financial modeling AI. Based on the provided business assumptions, your task is to suggest the most suitable financial model structure and template.

Business Assumptions:
---
{business_assumptions_json}
---

Available Model Templates:
---
{available_templates_json}
---

Consider the business model, revenue streams, cost structure, and target market to make your recommendation.
Explain your reasoning for suggesting a particular template or structure.
If multiple templates could be suitable, you can list them and explain the pros and cons of each in the context of the business.
Suggest essential components that should be included in their financial model (e.g., Assumptions, Income Statement, Balance Sheet, Cash Flow Statement, Key Performance Indicators (KPIs)).

Output your suggestion as a YAML object with the following keys:
- recommended_template_id: (String) The ID of the most suitable template from the available list (e.g., "saas_3_statement").
- reasoning: (String) A detailed explanation for your recommendation.
- alternative_template_ids: (List of Strings) Optional. IDs of other suitable templates.
- essential_components: (List of Strings) A list of essential financial model components (e.g., ["Assumptions", "Income Statement", "Balance Sheet", "Cash Flow Statement", "KPIs"]).
- suggested_kpis: (List of Strings) Optional. A list of 3-5 specific KPIs relevant to this business model (e.g., ["Monthly Recurring Revenue (MRR)", "Customer Acquisition Cost (CAC)", "Churn Rate"]).

Example for a SaaS business (output should be valid YAML):
```yaml
recommended_template_id: saas_3_statement_detailed_cohort
reasoning: "Given the SaaS business model with subscription revenue, a detailed 3-statement model with cohort analysis for customer retention and LTV is highly recommended. This will provide deep insights into unit economics."
alternative_template_ids:
  - saas_3_statement_basic
essential_components:
  - Assumptions
  - Revenue Forecast
  - Expense Budget
  - Income Statement
  - Balance Sheet
  - Cash Flow Statement
  - SaaS KPIs
suggested_kpis:
  - Monthly Recurring Revenue (MRR)
  - Customer Acquisition Cost (CAC)
  - Customer Lifetime Value (CLTV)
  - Churn Rate
  - Average Revenue Per User (ARPU)
```

If no specific template seems directly applicable from the list, recommend a "general_3_statement" and focus on customizing the essential components and KPIs.
Ensure your output is a single, valid YAML structure.

Suggested Model Structure (YAML):
"""

MODEL_COMPONENT_GUIDANCE_PROMPT = """
You are an expert financial modeling AI. The user is working on their financial model structure and needs guidance on a specific component.

Business Assumptions:
---
{business_assumptions_json}
---

Selected Model Template/Structure:
---
{model_structure_json}
---

Component in Question: "{component_name}"

Your task is to:
1. Explain the purpose and importance of the "{component_name}" in the context of their business.
2. List key sub-items or considerations for this component.
3. Provide a brief example if applicable.

Guidance for {component_name}:
"""
