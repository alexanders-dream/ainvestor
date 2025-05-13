# PROMPT TEMPLATES FOR INVESTOR SCOUT AGENT
# These are examples if an LLM were used for more advanced matching,
# generating outreach messages, or summarizing investor profiles.
# The current investor_scout_logic.py uses direct CSV filtering.

PROMPT_MATCH_INVESTOR_PROFILE = """
**Role:** You are an AI assistant helping a startup founder find suitable investors.
**Task:** Analyze the startup's profile and the investor's profile below. Determine if there is a good potential match.
Provide a brief justification for your assessment (2-3 sentences).

**Startup Profile:**
*   Industry: {startup_industry}
*   Stage: {startup_stage}
*   Desired Investment: {startup_investment_ask}
*   Key Characteristics/Keywords: {startup_keywords}
*   Brief Description: {startup_description}

**Investor Profile:**
*   Investor Name: {investor_name}
*   Focus Industries: {investor_focus_industries}
*   Preferred Stages: {investor_preferred_stages}
*   Typical Investment Range: {investor_investment_range}
*   Portfolio Examples/Interests: {investor_notes}

**Output Format:**
*   **Match Assessment:** (e.g., Strong Match, Potential Match, Weak Match, Unlikely Match)
*   **Justification:** Briefly explain your reasoning.
---
**Match Assessment for {investor_name}:**
"""

PROMPT_GENERATE_INVESTOR_OUTREACH_INTRO = """
**Role:** You are an AI assistant helping a startup founder draft a concise and compelling introductory email snippet for an investor.
**Task:** Based on the startup's details and the investor's known interests, draft a 2-3 sentence personalized opening for an email.
The goal is to grab the investor's attention by highlighting alignment.

**Startup Details:**
*   Company Name: {company_name}
*   One-liner: {company_one_liner}
*   Key reason for reaching out to THIS investor (e.g., portfolio synergy, stated interest): {reason_for_outreach}

**Investor Details (if known):**
*   Investor Name: {investor_name}
*   Investor Firm: {investor_firm}
*   Known Interest/Portfolio Company: {investor_specific_interest}

**Output Format:**
A 2-3 sentence email introduction.
---
**Suggested Email Introduction for {investor_name} at {investor_firm}:**
"""

PROMPT_SUMMARIZE_INVESTOR_FOCUS = """
**Role:** You are an AI research assistant.
**Task:** Read the following investor's "About" or "Thesis" text and summarize their primary investment focus in 1-2 sentences.
Identify key industries, stages, and types of companies they typically invest in.

**Investor Text:**
```
{investor_about_text}
```

**Output Format:**
A 1-2 sentence summary.
---
**Summary of Investor Focus:**
"""

if __name__ == '__main__':
    print("--- MATCH INVESTOR PROFILE PROMPT ---")
    print(PROMPT_MATCH_INVESTOR_PROFILE.format(
        startup_industry="AI in Healthcare",
        startup_stage="Seed",
        startup_investment_ask="$500,000 - $1,000,000",
        startup_keywords="diagnostic tools, machine learning, medical imaging",
        startup_description="We are developing an AI platform to improve the accuracy of early cancer detection from medical scans.",
        investor_name="HealthTech Ventures",
        investor_focus_industries="Healthcare IT, Digital Health, Medical Devices",
        investor_preferred_stages="Seed, Series A",
        investor_investment_range="$250,000 - $2,000,000",
        investor_notes="Portfolio includes 'ScanAI' (AI for radiology) and 'MedRecords Inc.' (EHR systems). Keen on AI applications in diagnostics."
    ))

    print("\n--- GENERATE INVESTOR OUTREACH INTRO PROMPT ---")
    print(PROMPT_GENERATE_INVESTOR_OUTREACH_INTRO.format(
        company_name="PulseAI",
        company_one_liner="PulseAI is revolutionizing cardiac care with AI-powered predictive diagnostics.",
        reason_for_outreach="Your firm's investment in 'CardioTrack' and stated interest in preventative health tech aligns perfectly with our mission.",
        investor_name="Dr. Emily Carter",
        investor_firm="Vitality Ventures",
        investor_specific_interest="preventative health technology, AI in cardiology"
    ))

    print("\n--- SUMMARIZE INVESTOR FOCUS PROMPT ---")
    print(PROMPT_SUMMARIZE_INVESTOR_FOCUS.format(
        investor_about_text="Future Forward Capital invests in early-stage (Seed to Series A) technology companies in North America, primarily focusing on B2B SaaS, enterprise software, and AI/ML applications that disrupt traditional industries. We look for strong technical teams and scalable business models."
    ))
