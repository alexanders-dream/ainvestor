# PROMPT TEMPLATES FOR FINANCIAL MODELING AGENT
# These prompts are examples if an LLM were to be used for guidance,
# assumption validation, or explaining financial concepts within the agent.
# The current financial_model_logic.py performs direct calculations without LLM.

PROMPT_EXPLAIN_FINANCIAL_TERM = """
**Role:** You are a helpful financial analyst AI.
**Task:** Explain the financial term "{term}" in simple terms for a startup founder.
Also, explain why it's important for their financial model or pitch deck.

**Term:** {term}

**Output Format:**
1.  **Simple Explanation:** Define the term clearly and concisely.
2.  **Importance for Startups:** Explain its relevance.
---
**Explanation for "{term}":**
"""

PROMPT_VALIDATE_ASSUMPTION = """
**Role:** You are an experienced financial analyst specializing in early-stage startups.
**Task:** Review the following financial assumption for a startup in the "{industry}" industry at the "{stage}" stage.
Provide feedback on its reasonableness and suggest potential considerations or alternative approaches if it seems off.

**Startup Profile:**
*   Industry: {industry}
*   Stage: {stage}
*   Brief Description (Optional): {description}

**Assumption to Validate:**
*   Metric: "{metric_name}"
*   Value/Projection: "{metric_value}"
*   User's Rationale (If Provided): "{user_rationale}"

**Output Format:**
1.  **Initial Assessment:** (e.g., Seems reasonable, Appears optimistic/conservative, Needs more context)
2.  **Key Considerations/Questions:** What factors should the founder consider regarding this assumption?
3.  **Industry Benchmarks (If Known/Applicable):** Mention any general benchmarks, if possible (qualify that these vary greatly).
4.  **Suggestions (If an issue is identified):**
---
**Feedback on "{metric_name}" Assumption:**
"""

PROMPT_GENERATE_FINANCIAL_NARRATIVE = """
**Role:** You are a financial storyteller for startups.
**Task:** Based on the provided key financial projections, generate a brief narrative (2-3 paragraphs) that a founder could use to explain their financial outlook in a pitch deck or to an investor. Highlight key growth drivers and profitability milestones.

**Key Financial Projections (Simplified):**
*   Year 1 Revenue: {revenue_y1}
*   Year 3 Revenue: {revenue_y3}
*   Year 1 Net Income: {net_income_y1}
*   Year 3 Net Income: {net_income_y3}
*   Key Revenue Drivers: {revenue_drivers} (e.g., "customer acquisition, new product launch")
*   Key Cost Drivers: {cost_drivers} (e.g., "marketing spend, team expansion")

**Output Format:**
A concise narrative.
---
**Financial Outlook Narrative:**
"""

if __name__ == '__main__':
    print("--- EXPLAIN FINANCIAL TERM PROMPT ---")
    print(PROMPT_EXPLAIN_FINANCIAL_TERM.format(term="Customer Acquisition Cost (CAC)"))

    print("\n--- VALIDATE ASSUMPTION PROMPT ---")
    print(PROMPT_VALIDATE_ASSUMPTION.format(
        industry="SaaS",
        stage="Seed",
        description="A B2B SaaS platform for project management.",
        metric_name="Monthly Recurring Revenue (MRR) Growth Rate (Year 1)",
        metric_value="25% month-over-month",
        user_rationale="Aggressive marketing and strong initial user feedback."
    ))

    print("\n--- GENERATE FINANCIAL NARRATIVE PROMPT ---")
    print(PROMPT_GENERATE_FINANCIAL_NARRATIVE.format(
        revenue_y1="$100,000",
        revenue_y3="$1,500,000",
        net_income_y1="-$50,000 (Loss)",
        net_income_y3="$250,000 (Profit)",
        revenue_drivers="Expanding sales team and launching two new product features.",
        cost_drivers="Hiring key personnel and increased marketing budget."
    ))
