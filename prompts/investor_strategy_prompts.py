# prompts/investor_strategy_prompts.py

# Prompt to help the LLM develop an investor search strategy
GET_STRATEGY_DEVELOPMENT_PROMPT = """
**Role:** You are an AI-powered Investment Strategy Analyst for startups.
Your goal is to help a startup define a targeted and effective strategy to find relevant investors.

**Startup Profile:**
- Industry/Sector: {startup_industry}
- Stage: {startup_stage}
- Desired Investment: {startup_funding_needed}
- Unique Selling Proposition (USP)/Key Differentiators: {startup_usp}

**Contextual Information (Optional):**
- Key Market Trends to Consider: {market_trends}
- Specific Investor Preferences or Exclusions: {investor_preferences}
- Pre-identified Potential Investors (if any, for context):
  ```yaml
  {selected_investors_context}
  ```

**Task:**
Based on the startup profile and ALL contextual information (including any pre-identified investors), develop a concise and actionable investor search strategy.
If pre-identified investors are provided, consider how they fit into the overall strategy. For example, should the strategy focus on finding similar investors, or different types to complement them?
The strategy should include:
1.  **Strategy Summary:** A brief overview of the recommended approach (e.g., types of investors to target, geographical focus if applicable).
2.  **Keywords for Search:** A list of 3-5 effective keywords or phrases to use when searching online databases, LinkedIn, or general web search (e.g., "seed stage fintech investor New York", "angel investor healthcare AI").
3.  **Potential Data Sources:** A list of 3-4 types of platforms or methods to find investors (e.g., "Crunchbase", "AngelList", "LinkedIn Sales Navigator", "Industry-specific investor networks", "VC firm websites").
4.  **Key Outreach Angle/Focus:** A suggestion on what key aspects of the startup to highlight when first reaching out or what makes the startup attractive for the targeted investors.

**Output Format:**
Provide the strategy as a YAML object with the following keys: "summary", "keywords_for_search" (as a list of strings), "data_sources_to_check" (as a list of strings), and "outreach_angle".

**Example Output (Illustrative):**
```yaml
summary: Focus on early-stage VCs and angel groups in North America specializing in SaaS. Prioritize those with a history of investing in B2B solutions.
keywords_for_search:
  - early stage SaaS VC North America
  - B2B software angel investors
  - seed funding enterprise software
data_sources_to_check:
  - Crunchbase Pro
  - AngelList Syndicates
  - LinkedIn (searching for partners at relevant VC firms)
  - Niche SaaS investor databases
outreach_angle: Emphasize the strong MVP traction, the clear problem being solved in the B2B space, and the scalable business model. Highlight the team's expertise if relevant.
```

**Begin Strategy Development:**
"""

# Prompt to help the LLM refine or analyze search results (example)
GET_RESULTS_REFINEMENT_PROMPT = """
**Role:** You are an AI Data Analyst specializing in investor information.
Your task is to process a list of potential investors found through various search methods and refine it or extract key insights.

**Raw Search Results (YAML format):**
```yaml
{raw_results_yaml}
```
Each item in the list above might contain fields like 'name', 'source', 'description', 'focus_areas', 'website', etc.

**Task:**
1.  **Identify Top Matches:** Based on the provided data, identify the top 3-5 most promising investor leads.
2.  **Summarize Relevance:** For each top match, provide a brief (1-2 sentences) explanation of why they might be a good fit for a startup in the "{startup_industry}" sector at the "{startup_stage}" stage, with a USP of "{startup_usp}".
3.  **Suggest Next Steps:** For each top match, suggest a potential next step for engagement (e.g., "Research recent investments on their website", "Look for a warm introduction via LinkedIn").

**Output Format:**
Provide your analysis as a YAML object with a main key "refined_investors", which is a list of objects. Each object should have "name", "summary_of_relevance", and "suggested_next_step".

**Example Output (Illustrative):**
```yaml
refined_investors:
  - name: Investor Alpha
    summary_of_relevance: Investor Alpha focuses on seed-stage SaaS companies, aligning well with the startup's profile. Their recent investments show interest in AI-driven B2B solutions.
    suggested_next_step: Review their portfolio on their website for similar companies and identify a relevant partner to target for an introduction.
  - name: Beta Angels Group
    summary_of_relevance: This angel group has a strong network in the {startup_industry} space and often invests in companies with strong technical USPs.
    suggested_next_step: Check if any of the startup's advisors have connections to members of Beta Angels Group.
```

**Begin Analysis (using the provided startup_industry, startup_stage, and startup_usp for context):**
"""

# You can add more specific prompts here, for example:
# - A prompt to generate targeted search queries for Firecrawl based on the strategy.
# - A prompt to summarize scraped web content from an investor's website.
# - A prompt to draft a cold outreach email template based on the strategy and investor profile.

def get_strategy_development_prompt():
    """Returns the prompt template for strategy development."""
    return GET_STRATEGY_DEVELOPMENT_PROMPT

def get_results_refinement_prompt():
    """Returns the prompt template for refining search results."""
    # This prompt expects startup_industry, startup_stage, and startup_usp to be filled in
    # along with raw_results_json.
    return GET_RESULTS_REFINEMENT_PROMPT

if __name__ == '__main__':
    # Example of how to use the prompts (for testing)
    print("--- Strategy Development Prompt ---")
    # Example variables for formatting
    profile_vars = {
        "startup_industry": "Renewable Energy Tech",
        "startup_stage": "Seed",
        "startup_funding_needed": "$750k",
        "startup_usp": "Patented solar panel efficiency technology (25% improvement).",
        "market_trends": "Increased government incentives for green tech, corporate ESG initiatives.",
        "investor_preferences": "Investors with a cleantech portfolio, impact investors."
    }
    # Manually format for this test, Langchain would handle this in llm_interface
    # Add the new context variable for testing
    profile_vars["selected_investors_context"] = """
- name: Acme Ventures
  focus: Early-stage B2B SaaS
  notes: Already had a brief intro call.
- name: Beta Growth Partners
  focus: Series A, Fintech
  notes: Found through Investor Scout.
"""
    formatted_strategy_prompt = GET_STRATEGY_DEVELOPMENT_PROMPT.format(**profile_vars)
    # print(formatted_strategy_prompt) # Commented out to keep output clean
    print("Strategy prompt template is available.")


    print("\n--- Results Refinement Prompt ---")
    refinement_vars = {
        "raw_results_yaml": """
- name: Green Ventures
  description: Invests in early-stage green tech.
""",
        "startup_industry": "Renewable Energy Tech",
        "startup_stage": "Seed",
        "startup_usp": "Patented solar panel efficiency technology (25% improvement)."
    }
    formatted_refinement_prompt = GET_RESULTS_REFINEMENT_PROMPT.format(**refinement_vars)
    # print(formatted_refinement_prompt) # Commented out
    print("Results refinement prompt template is available.")
