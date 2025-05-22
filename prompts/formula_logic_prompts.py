# prompts/formula_logic_prompts.py

# flake8: noqa E501

FORMULA_EXPLANATION_PROMPT = """
You are an expert financial modeling AI. The user wants to understand a specific financial formula or concept relevant to their model.

Business Context:
---
{business_assumptions_json}
---

Selected Model Structure:
---
{model_structure_json}
---

User's Financial Assumptions (if available):
---
{financial_assumptions_json}
---

Formula/Concept in Question: "{formula_or_concept}"

Your task is to:
1. Briefly explain the formula or concept in simple terms.
2. Describe its purpose and why it's important in financial modeling or for this specific business type.
3. Provide a simple example of how it's calculated or applied, using hypothetical numbers if necessary.
4. If it relates to interdependencies between financial statements (e.g., Net Income linking to Retained Earnings and Cash Flow), explain that link.
5. Keep the explanation clear, concise, and actionable.

AI Explanation for "{formula_or_concept}":
"""

FINANCIAL_STATEMENT_INTERDEPENDENCY_PROMPT = """
You are an expert financial modeling AI. The user wants to understand how the main financial statements (Income Statement, Balance Sheet, Cash Flow Statement) are interconnected.

Business Context (Optional, but helpful):
---
{business_assumptions_json}
---

Explain the key linkages between:
1.  Income Statement and Balance Sheet (e.g., Net Income to Retained Earnings).
2.  Income Statement and Cash Flow Statement (e.g., Net Income as starting point for CFO, non-cash expenses).
3.  Balance Sheet and Cash Flow Statement (e.g., changes in BS accounts affecting cash, ending cash balance linking back to BS).

Provide a clear, step-by-step explanation of these connections. You can use a common example like a retail or SaaS business to illustrate.

AI Explanation of Financial Statement Interdependencies:
"""
