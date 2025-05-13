# prompts/firecrawl_processing_prompts.py

PROMPT_EXTRACT_INVESTOR_INFO_FROM_SCRAPED_PAGE = """
**Role:** You are an AI assistant specialized in extracting structured investor information from the text content of a scraped webpage.

**Context:** The user has provided Markdown text content scraped from a potential investor's website or a platform listing investors.

**Scraped Page Content (Markdown):**
---
{scraped_markdown_content}
---

**Source URL (if available, for context):** {source_url}

**Task:**
Analyze the provided "Scraped Page Content". Your goal is to identify and extract key information about one or more investors or investment firms mentioned on the page.
If the page is a list of investors, try to extract details for each distinct investor. If it's a single firm's page, extract details for that firm.

For each identified investor/firm, extract the following information if available. If a piece of information is not clearly present for an investor, use `null` or an empty string for its value.

**Information to Extract per Investor/Firm:**
-   `name`: The name of the investment firm or individual investor.
-   `description`: A brief description of the investor/firm, their mission, or focus.
-   `investor_type`: Type of investor (e.g., "VC Firm", "Angel Network", "Individual Angel", "Accelerator", "Impact Investor", "Corporate VC").
-   `industry_focus`: Specific industries or sectors they invest in (e.g., ["Fintech", "Healthcare AI", "SaaS B2B"]). List if multiple.
-   `stage_focus`: Preferred investment stages (e.g., ["Seed", "Series A", "Early Stage"]). List if multiple.
-   `geographical_focus`: Specific regions or countries they focus on (e.g., ["Africa", "Sub-Saharan Africa", "Global", "North America"]). List if multiple.
-   `contact_email`: A contact email address, if found.
-   `website_url`: The primary website URL for the investor/firm. If the `source_url` is the main site, use that.
-   `key_people`: Names of key partners or team members, if listed (e.g., ["Jane Doe (Partner)", "John Smith (Analyst)"]).
-   `portfolio_examples`: A few examples of companies they've invested in, if mentioned.
-   `notes`: Any other relevant notes or specific criteria mentioned (e.g., "Minimum investment $100k", "Focus on female founders").

**Output Format:**
Return the information as a single, valid YAML object. The top-level key MUST be "extracted_profiles", and its value should be a list of YAML objects, where each object represents an extracted investor/firm profile.

IMPORTANT: Your response MUST be a valid YAML object that can be parsed with yaml.safe_load(). Do not include any explanatory text before or after the YAML.

If no specific investor information can be reliably extracted, return an empty list for "extracted_profiles":
```yaml
extracted_profiles: []
```

**Example YAML Output (if one investor found):**
```yaml
extracted_profiles:
  - name: Future Africa Fund
    description: Investing in mission-driven founders building the future of Africa.
    investor_type: VC Firm
    industry_focus:
      - Technology
      - Fintech
      - Healthcare
      - Clean Energy
    stage_focus:
      - Pre-Seed
      - Seed
    geographical_focus:
      - Africa
    contact_email: connect@future.africa
    website_url: https://future.africa
    key_people:
      - Iyinoluwa Aboyeji (Founding Partner)
    portfolio_examples:
      - Andela
      - Flutterwave
    notes: Looking for companies with strong local impact.
```
**Example YAML Output (if multiple investors on a list page):**
```yaml
extracted_profiles:
  - name: Investor A Capital
    investor_type: VC Firm
    industry_focus:
      - SaaS
    description: ""
    stage_focus: []
    geographical_focus: []
    contact_email: ""
    website_url: ""
    key_people: []
    portfolio_examples: []
    notes: ""
  - name: Angel Group B
    investor_type: Angel Network
    geographical_focus:
      - East Africa
    industry_focus: []
    description: ""
    stage_focus: []
    contact_email: ""
    website_url: ""
    key_people: []
    portfolio_examples: []
    notes: ""
```
```

**Begin Extraction:**
"""

if __name__ == '__main__':
    example_content = """
    # About Us - Africa Ventures
    Welcome to Africa Ventures! We are a leading venture capital firm dedicated to empowering innovative startups across the African continent.
    Our focus is on early-stage technology companies in Fintech, Agritech, and Renewable Energy. We typically invest in Seed and Series A rounds.
    Contact us at info@africaventures.com. Our main site is africaventures.com.
    Key team: Maria Zola (Managing Partner), David Kim (Investment Director).
    Some of our success stories include PayFast Africa and SolarGrid Ltd.
    We look for strong teams and scalable solutions.
    """
    print(PROMPT_EXTRACT_INVESTOR_INFO_FROM_SCRAPED_PAGE.format(
        scraped_markdown_content=example_content,
        source_url="https://africaventures.com/about"
    ))
