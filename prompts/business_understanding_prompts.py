# prompts/business_understanding_prompts.py

# flake8: noqa E501

PITCH_DECK_EXTRACTION_PROMPT = """
You are an expert financial analyst AI. Your task is to carefully read the following pitch deck content and extract key business information.
Please identify and structure the information as a YAML object with the following keys:
- business_model: A concise description of how the business operates and creates value.
- revenue_streams: A list of primary ways the business generates revenue.
- cost_structure: A summary of the major costs and expenses the business incurs.
- target_market: A description of the primary customers or market segments the business targets.
- problem_solved: The specific problem or pain point the business addresses for its customers.
- solution_offered: How the business's product or service solves the identified problem.
- key_team_members: (Optional) List key team members and their roles if explicitly mentioned and relevant to the business's core strength.
- market_size_opportunity: (Optional) Any stated market size or growth opportunity.
- competitive_advantage: (Optional) What makes the business unique or provides an edge over competitors.

If some information is not clearly available in the pitch deck, use `null` or an empty list (e.g., `[]`) for the corresponding key.
Ensure the output is a single, valid YAML object. Example:
```yaml
business_model: "Direct-to-consumer (DTC) e-commerce platform for sustainable pet products."
revenue_streams:
  - "Online sales of physical products (toys, food, accessories)"
  - "Subscription boxes for monthly pet supplies"
cost_structure: "COGS (product manufacturing, sourcing), marketing and advertising (social media, influencers), platform fees (Shopify), shipping and fulfillment, payment processing fees, salaries (customer support, operations)."
target_market: "Environmentally conscious pet owners, primarily millennials and Gen Z, in urban areas."
problem_solved: "Difficulty for pet owners to find high-quality, eco-friendly pet products from a single, trusted source."
solution_offered: "A curated online marketplace offering a wide range of sustainable and ethically sourced pet products with convenient delivery."
key_team_members: null
market_size_opportunity: "The global pet care market is valued at $200 billion and projected to grow at 5% CAGR. The sustainable pet product segment is a rapidly growing niche within this market."
competitive_advantage: "Strong brand focus on sustainability and ethical sourcing, curated product selection, active community engagement."
```

Pitch Deck Content:
---
{pitch_deck_text}
---

Extracted YAML:
"""

CLARIFICATION_PROMPT_TEMPLATE = """
You are an AI assistant helping a user build a financial model.
Based on the initial information extracted from their pitch deck and our conversation so far, I need to ask some clarifying questions to better understand their business.

Previously Extracted Information:
{extracted_data}

Conversation History:
{conversation_history}

Your task is to:
1. Review the extracted information and conversation history.
2. Identify areas that are unclear, missing, or need more detail for financial modeling.
3. Formulate a concise, polite, and targeted question to the user to get the necessary clarification.
   Focus on one key area per question. For example, if revenue streams are vague, ask for more specific details about them.
   If cost structure is missing, ask about major operational or COGS expenses.

Example questions:
- "Could you elaborate on your primary revenue streams? For example, are they subscription-based, one-time sales, or usage-based?"
- "What are the main components of your cost of goods sold (COGS) or key operational expenses?"
- "Can you provide more detail about your target customer segments?"

Generate one clarifying question based on the current context.

Clarifying Question:
"""

UPDATE_ASSUMPTIONS_PROMPT_TEMPLATE = """
You are an AI assistant helping a user refine their business assumptions for a financial model.
The user has provided new information in response to a clarifying question.
Your task is to update the existing structured business assumptions based on this new information.

Current Business Assumptions (YAML format):
---
{current_assumptions_yaml}
---

User's Response to Clarification:
---
{user_response}
---

Based on the user's response, update the relevant fields in the current business assumptions.
Ensure the output is a single, valid YAML object representing the *complete* updated set of assumptions.
If the user's response doesn't clearly modify a specific field, keep the original value for that field.

Example of current assumptions (YAML):
```yaml
business_model: "Online subscription service for gourmet coffee beans."
revenue_streams:
  - "Monthly subscription fees"
target_market: "Coffee enthusiasts"
# ... other fields
```

Example of user response: "We also plan to sell brewing equipment as a one-time purchase."

Example of updated assumptions (YAML):
```yaml
business_model: "Online subscription service for gourmet coffee beans and related brewing equipment."
revenue_streams:
  - "Monthly subscription fees for coffee beans"
  - "One-time sales of brewing equipment"
target_market: "Coffee enthusiasts and home brewers"
# ... other fields remain, or are updated if relevant
```

Updated Business Assumptions (YAML):
"""
