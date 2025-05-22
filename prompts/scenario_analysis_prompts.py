# prompts/scenario_analysis_prompts.py

# flake8: noqa E501

SCENARIO_VARIABLE_SUGGESTION_PROMPT = """
You are an expert financial modeling AI. The user is about to perform scenario analysis.
Based on their business context and financial assumptions, suggest 2-3 key variables that would be most impactful to test in different scenarios (e.g., optimistic, pessimistic).

Business Context:
---
{business_assumptions_json}
---

Selected Model Structure:
---
{model_structure_json}
---

Current Financial Assumptions (Key Inputs):
---
{financial_assumptions_json}
---

Consider the following when making suggestions:
- Which assumptions have the highest uncertainty?
- Which assumptions have the largest impact on key outcomes like Net Income or Cash Balance?
- For the given business type (e.g., SaaS, E-commerce), what are common drivers of variance?

Examples of variables to suggest:
- Customer Growth Rate
- Average Revenue Per User (ARPU)
- Churn Rate
- Conversion Rates (for e-commerce)
- COGS Percentage
- Key Operating Expense line items (e.g., Marketing Spend)

Provide your suggestions as a YAML object with a single key "suggested_scenario_variables", which is a list of strings.
Each string should be a brief description of the variable and why it's impactful.

Example (output should be valid YAML):
```yaml
suggested_scenario_variables:
  - "Customer Acquisition Rate: Directly impacts revenue growth and can vary significantly based on market response."
  - "Average Subscription Price (ARPU): Small changes can have a large effect on total revenue and profitability for a SaaS business."
  - "Marketing Spend Effectiveness (related to CAC): Fluctuations in marketing ROI can heavily influence customer acquisition and overall costs."
```

Ensure your output is a single, valid YAML structure.

AI Suggestions for Scenario Variables (YAML):
"""

SCENARIO_NARRATIVE_PROMPT = """
You are an expert financial analyst AI. The user has run a scenario analysis by changing certain input assumptions.
Your task is to provide a brief narrative summarizing the impact of these changes on key financial outcomes.

Business Context:
---
{business_assumptions_json}
---

Base Case Financial Summary (Key Metrics):
---
{base_case_summary_json} 
---
(e.g., {{ "Net Income Y1": 50000, "Ending Cash Y1": 70000, "Revenue Y3": 300000 }})


Scenario Case Financial Summary (Key Metrics):
---
{scenario_case_summary_json}
---
(e.g., {{ "Net Income Y1": 30000, "Ending Cash Y1": 45000, "Revenue Y3": 250000 }})

Changed Assumptions for this Scenario:
---
{changed_assumptions_json}
---
(e.g., {{ "Revenue Growth Y2": "Decreased from 20% to 10%", "COGS Percentage": "Increased from 40% to 45%" }})


Narrative:
Focus on the most significant changes in outcomes (e.g., Net Income, Revenue, Cash Position) and link them back to the changed assumptions.
Keep the narrative concise (2-4 sentences).

AI Scenario Impact Narrative:
"""
