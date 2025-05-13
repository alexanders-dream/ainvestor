# PROMPT TEMPLATES FOR PITCH DECK ADVISOR

PROMPT_OVERALL_FEEDBACK = """
**Role:** You are an expert pitch deck analyst and startup advisor. Your goal is to provide constructive, actionable feedback to help entrepreneurs improve their pitch decks.

**Context:** The user has provided the full extracted text from their pitch deck. Your first task is to try and discern the structure and content of common pitch deck sections within this text.

**Full Extracted Pitch Deck Text:**
---
{full_deck_text}
---

**Task:**
Based on the **Full Extracted Pitch Deck Text** provided above, perform a comprehensive analysis. Structure your feedback as follows:

1.  **Overall Impression & Key Strengths:** Start with a brief, encouraging overview. Highlight 2-3 strong points you can identify from the text.
2.  **Identified Deck Structure & Flow:** Based on the full text, attempt to identify common pitch deck sections (e.g., Problem, Solution, Product, Market, Team, Financials, Ask, Competition, Traction, etc.). Comment on the likely structure. Does it seem to follow a logical narrative? Are any standard sections obviously missing, unclear, or given disproportionate attention within the text?
3.  **Critical Areas for Improvement (Top 3-5):** Identify the most crucial weaknesses or gaps in the content. For each point, explain *why* it's an issue and suggest *specific actions* the user can take to address it. Be direct but constructive.
4.  **Section-Specific Feedback (Based on Your Interpretation):** For the sections you were able to identify (or infer), provide brief feedback. If you cannot clearly identify a section, note that.
    *   Problem: (Clarity, magnitude, validation, if identifiable)
    *   Solution: (Clarity, innovativeness, feasibility, if identifiable)
    *   Product: (Key features, differentiation, development stage, if identifiable)
    *   Market: (TAM/SAM/SOM clarity, target customer understanding, if identifiable)
    *   Business Model: (Clarity of revenue streams, pricing logic, scalability, if identifiable)
    *   Team: (Relevant experience, completeness, if identifiable)
    *   Financials: (Realism, key assumptions clarity, if identifiable)
    *   Ask: (Clarity of amount, justification, if identifiable)
    *   Competition: (Analysis depth, differentiation, if identifiable)
    *   Traction/Milestones: (Evidence of progress, clear goals, if identifiable)
5.  **Actionable Next Steps:** Summarize with 2-3 high-priority actions the entrepreneur should focus on next to improve their deck content and structure.
6.  **Guidance on Missing Sections:** If critical sections (like Competition, Team, or Financials) seem entirely absent or unidentifiable in the text, strongly recommend their inclusion.

**Output Format:**
Use well-structured Markdown. Employ headings, bullet points, and bold text for readability.
Be concise yet thorough. Avoid jargon where simpler terms suffice.
Maintain a supportive and advisory tone.
"""

def get_messaging_refinement_prompt_template():
    """
    Returns a Langchain-compatible prompt template string for messaging refinement.
    Placeholders: {section_name}, {section_text}, {startup_usp}
    """
    return """
**Role:** You are a master storyteller and an expert in crafting compelling business narratives for pitch decks.

**Task:** Refine the following text from the "{section_name}" section of a pitch deck. The goal is to make the messaging more clear, concise, impactful, and persuasive for potential investors.

**Original Text from "{section_name}" Section:**
```
{section_text}
```

**Startup's Stated Unique Selling Proposition (USP) (if provided, otherwise infer or focus on general clarity):**
"{startup_usp}"

**Instructions for Refinement:**
1.  **Clarity:** Is the core message immediately understandable? Eliminate jargon and ambiguity.
2.  **Conciseness:** Can the same message be conveyed in fewer words? Remove redundant phrases.
3.  **Impact:** Does the language grab attention and create a strong impression? Use strong verbs and vivid language where appropriate.
4.  **Persuasiveness:** Does the text effectively convince the reader of the section's key points? Highlight benefits and value.
5.  **Investor Focus:** Ensure the language resonates with an investor audience (e.g., focus on opportunity, scalability, market, return).
6.  **Alignment with USP:** If a USP is provided, ensure the refined text subtly reinforces or aligns with it.
7.  **Maintain Core Meaning:** Do not change the fundamental facts or intent of the original text, only enhance its delivery.

**Output Format:**
Provide only the **Refined Text** for the section. Do not include preambles like "Here's the refined text:".
If the original text is already excellent and needs no refinement, you can state: "The original text for the '{section_name}' section is already excellent and requires no significant refinement."
---
**Refined Text for "{section_name}":**
"""

# Example of another prompt, e.g., for generating slide ideas
PROMPT_GENERATE_SLIDE_IDEAS = """
**Role:** You are a pitch deck consultant.
**Task:** Based on the startup concept: "{startup_concept}", suggest 5 key slides that must be in their pitch deck, with a brief (1-2 sentence) description of what each slide should cover.
**Startup Concept:** {startup_concept}
**Output:**
Provide a numbered list of slide titles and their descriptions.
"""

if __name__ == '__main__':
    # This allows you to print and inspect the prompts if you run this file directly.
    print("--- PROMPT_OVERALL_FEEDBACK ---")
    print(PROMPT_OVERALL_FEEDBACK.format(
        full_deck_text="This is the entire pitch deck text. It talks about a problem, then a solution. The market is huge. Our team is great. We need money."
    ))
    print("\n--- MESSAGING REFINEMENT TEMPLATE ---")
    refinement_template = get_messaging_refinement_prompt_template()
    print(refinement_template.format(
        section_name="Problem Statement",
        section_text="The current solutions for task X are inefficient and costly for many users, leading to frustration.",
        startup_usp="We make task X 10x faster and 50% cheaper."
    ))
    print("\n--- GENERATE SLIDE IDEAS PROMPT ---")
    print(PROMPT_GENERATE_SLIDE_IDEAS.format(startup_concept="An AI-powered personal chef for busy professionals."))

PROMPT_EXTRACT_STRUCTURED_DATA = """
**Role:** You are an AI assistant specialized in extracting structured information from pitch deck text.

**Context:** The user has provided the full extracted text from their pitch deck.

**Full Extracted Pitch Deck Text:**
---
{full_deck_text}
---

**Task:**
Analyze the provided pitch deck text and extract the following key pieces of information.
If a piece of information is not clearly present, use `null` or an empty string for its value.
Return the information as a single, valid JSON object.

**Information to Extract:**
-   `company_name`: The name of the company or project.
-   `problem_statement`: A concise summary of the problem the startup is solving.
-   `solution_description`: A concise summary of the startup's solution.
-   `usp` (Unique Selling Proposition): What makes the startup unique or different?
-   `target_market`: A brief description of the target market or customer segment.
-   `industry_sector`: The primary industry or sector the startup operates in (e.g., "Fintech", "Healthcare AI", "SaaS B2B").
-   `current_stage`: The current stage of the startup (e.g., "Idea", "MVP", "Pre-Seed", "Seed", "Growth"). Try to infer if not explicitly stated.
-   `funding_ask_amount`: The amount of funding being sought, if mentioned (e.g., "$500k", "1.2M EUR").
-   `key_team_highlights`: Brief highlights about the team, if mentioned (e.g., "Experienced founders", "PhD in AI").
-   `traction_highlights`: Any mentioned traction or milestones (e.g., "1000 beta users", "LOIs signed").
-   `keywords_for_investor_search`: Based on the deck, suggest 3-5 keywords an investor might use to find this type of company (e.g., "AI for healthcare diagnostics", "sustainable packaging solution", "future of work SaaS").

**Output Format:**
A single, valid JSON object. Ensure all string values are properly escaped.

**Example JSON Output:**
```json
{{
  "company_name": "InnovateAI",
  "problem_statement": "Many businesses struggle with inefficient data analysis processes.",
  "solution_description": "An AI-powered platform that automates data analysis and provides actionable insights.",
  "usp": "Proprietary machine learning algorithms achieve 95% accuracy, 2x faster than competitors.",
  "target_market": "Small to medium-sized enterprises (SMEs) in the retail sector.",
  "industry_sector": "AI SaaS B2B",
  "current_stage": "MVP with pilot customers",
  "funding_ask_amount": "$750,000",
  "key_team_highlights": "CEO has 10+ years in retail tech, CTO is an AI PhD.",
  "traction_highlights": "5 pilot customers, $10k in pre-orders.",
  "keywords_for_investor_search": ["AI data analytics", "retail tech SaaS", "SME automation", "business intelligence AI"]
}}
```

**Begin Extraction:**
"""

if __name__ == '__main__':
    # This allows you to print and inspect the prompts if you run this file directly.
    print("--- PROMPT_OVERALL_FEEDBACK ---")
    # ... (rest of the if __name__ == '__main__' block remains the same)
    # print(PROMPT_OVERALL_FEEDBACK.format(
    #     full_deck_text="This is the entire pitch deck text. It talks about a problem, then a solution. The market is huge. Our team is great. We need money."
    # ))
    # print("\n--- MESSAGING REFINEMENT TEMPLATE ---")
    # refinement_template = get_messaging_refinement_prompt_template()
    # print(refinement_template.format(
    #     section_name="Problem Statement",
    #     section_text="The current solutions for task X are inefficient and costly for many users, leading to frustration.",
    #     startup_usp="We make task X 10x faster and 50% cheaper."
    # ))
    # print("\n--- GENERATE SLIDE IDEAS PROMPT ---")
    # print(PROMPT_GENERATE_SLIDE_IDEAS.format(startup_concept="An AI-powered personal chef for busy professionals."))
    print("\n--- EXTRACT STRUCTURED DATA PROMPT ---")
    print(PROMPT_EXTRACT_STRUCTURED_DATA.format(
        full_deck_text="Our company, Future Solutions, addresses the critical issue of outdated logistics software for small businesses. We offer a cloud-based SaaS platform that streamlines operations. Our USP is real-time tracking and predictive analytics, something competitors lack. We target e-commerce SMBs. We are in the SaaS B2B Logistics tech space. We have an MVP and are seeking $250k. Our team includes a logistics expert and a software architect. We have 20 beta sign-ups."
    ))
