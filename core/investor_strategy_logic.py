import streamlit as st
import yaml
import pandas as pd # To return a list of dicts, which can be easily converted to DataFrame
from .llm_interface import get_llm_response
from prompts import investor_strategy_prompts # For developing strategy
from prompts import firecrawl_processing_prompts # For processing scraped data
from .firecrawl_api import FirecrawlAPI
from .investor_scout_logic import AFRICAN_INVESTOR_PLATFORMS # Reuse the list
from .yaml_utils import load_yaml, dump_yaml, extract_yaml_from_text, create_default_investor_yaml

def develop_strategy_with_llm(profile: dict, market_trends: str, investor_preferences: str,
                              llm_provider: str, llm_model: str = None, 
                              selected_investors: list = None, # Moved parameter
                              **llm_kwargs):
    """
    Develops an investor search strategy using an LLM.

    Args:
        profile (dict): Startup profile (industry, stage, funding, USP).
        market_trends (str): Key market trends.
        investor_preferences (str): Specific investor preferences.
        llm_provider (str): The selected LLM provider.
        llm_model (str, optional): The specific LLM model.
        **llm_kwargs: Additional arguments for the LLM.

    Returns:
        dict: A dictionary containing the generated strategy.
              Example: {"summary": "...", "keywords_for_search": [...], ...}
    """
    # Actual LLM call for strategy development
    prompt_template = investor_strategy_prompts.GET_STRATEGY_DEVELOPMENT_PROMPT
    input_vars = {
        "startup_industry": profile.get('industry', 'N/A'),
        "startup_stage": profile.get('stage', 'N/A'),
        "startup_funding_needed": profile.get('funding_needed', 'N/A'),
        "startup_usp": profile.get('usp', 'N/A'),
        "market_trends": market_trends or "N/A",
        "investor_preferences": investor_preferences or "N/A",
        "selected_investors_context": yaml.dump(selected_investors, allow_unicode=True, default_flow_style=False, sort_keys=False) if selected_investors else "N/A (No pre-selected investors provided)"
    }

    # Ensure selected_investors_context is not excessively long
    if len(input_vars["selected_investors_context"]) > 3000: # Limit context length
        input_vars["selected_investors_context"] = input_vars["selected_investors_context"][:3000] + "\n... (list truncated)"


    response_str = get_llm_response(
        prompt_template_str=prompt_template,
        input_variables=input_vars,
        llm_provider=llm_provider,
        llm_model=llm_model,
        **llm_kwargs # temperature, max_tokens, api_key, base_url passed from UI
    )

    try:
        # Extract JSON from the LLM response
        from .utils import extract_json_from_response
        strategy_dict = extract_json_from_response(response_str)

        if not strategy_dict:
            st.warning("Could not extract JSON from LLM strategy response. Using fallback.")
            # Fallback mock strategy
            strategy_dict = {
                "summary": "Error: Could not extract JSON from LLM response. Using fallback.",
                "keywords_for_search": [f"{profile.get('industry', 'tech')} investor", f"{profile.get('stage', 'seed')} funding"],
                "data_sources_to_check": AFRICAN_INVESTOR_PLATFORMS + ["General Web Search via Firecrawl"],
                "outreach_angle": "Focus on core value proposition."
            }
        
        # Add a default for data_sources_to_check if not present or empty
        if not strategy_dict.get("data_sources_to_check"):
            strategy_dict["data_sources_to_check"] = ["General Web Search via Firecrawl"]
            # If African focus is detected in profile, add relevant platforms
            if "africa" in profile.get('industry', '').lower() or \
               "africa" in profile.get('usp', '').lower() or \
               "africa" in market_trends.lower() or \
               "africa" in investor_preferences.lower():
                strategy_dict["data_sources_to_check"].extend(AFRICAN_INVESTOR_PLATFORMS)
                strategy_dict["data_sources_to_check"] = list(set(strategy_dict["data_sources_to_check"])) # Unique

        return strategy_dict
    except Exception as e:
        st.error(f"Unexpected error processing LLM strategy response: {e}")
        # Fallback mock strategy if any other error occurs
        return {
            "summary": "Error: Unexpected error processing LLM response. Using fallback.",
            "keywords_for_search": [f"{profile.get('industry', 'tech')} investor", f"{profile.get('stage', 'seed')} funding"],
            "data_sources_to_check": AFRICAN_INVESTOR_PLATFORMS + ["General Web Search via Firecrawl"],
            "outreach_angle": "Focus on core value proposition."
        }

def execute_investor_search(strategy: dict, firecrawl_client=None,
                            llm_provider: str = None, llm_model: str = None, 
                            max_scrapes_per_keyword: int = 1, # Optimization: limit scrapes
                            **llm_kwargs):
    """
    Executes the investor search based on the developed strategy.
    
    Args:
        strategy (dict): The strategy developed by develop_strategy_with_llm.
        firecrawl_client (FirecrawlAPI, optional): An instance of the FirecrawlAPI client.
        llm_provider (str, optional): The selected LLM provider.
        llm_model (str, optional): The specific LLM model.
        max_scrapes_per_keyword (int): Maximum number of top results to scrape per keyword.
        **llm_kwargs: Additional arguments for the LLM.

    Returns:
        list: A list of dictionaries, where each dictionary represents a found investor.
    """
    all_found_investors = []

    if not firecrawl_client:
        try:
            firecrawl_api_key = st.secrets.get("FIRECRAWL_API_KEY")
            if not firecrawl_api_key:
                st.error("Firecrawl API key not found in st.secrets for Investor Strategy Agent.")
                return [{"name": "Config Error", "details": "Firecrawl API key missing."}]
            firecrawl_client = FirecrawlAPI(api_key=firecrawl_api_key)
        except Exception as e:
            st.error(f"Failed to initialize Firecrawl client: {e}")
            return [{"name": "Client Error", "details": str(e)}]

    urls_to_scrape = []
    keywords_for_search = strategy.get("keywords_for_search", [])
    data_sources = strategy.get("data_sources_to_check", [])

    # Add specific URLs from data_sources
    for source in data_sources:
        if source.startswith("http://") or source.startswith("https://"):
            urls_to_scrape.append(source)
        elif source in AFRICAN_INVESTOR_PLATFORMS: 
             urls_to_scrape.append(source)

    # Add AFRICAN_INVESTOR_PLATFORMS if "africa" implied
    if any("africa" in kw.lower() for kw in keywords_for_search) or \
       any("africa" in ds.lower() for ds in data_sources):
        urls_to_scrape.extend(AFRICAN_INVESTOR_PLATFORMS)

    # Remove duplicates
    urls_to_scrape = sorted(list(set(urls_to_scrape)))

    # Debug logging
    st.write(f"Debug: Strategy includes {len(keywords_for_search)} search keywords and {len(urls_to_scrape)} specific URLs to scrape")

    # Check if we have a valid Firecrawl client
    if not firecrawl_client:
        return [{"name": "API Error", "details": "Firecrawl API client not available."}]

    from .utils import extract_json_from_response # Import inside function to avoid circular imports

    # 1. Scrape specific URLs first (high priority)
    if urls_to_scrape:
        st.write(f"Strategy suggests scraping {len(urls_to_scrape)} specific URLs...")
        for i, url in enumerate(urls_to_scrape):
            st.write(f"Processing URL ({i+1}/{len(urls_to_scrape)}): {url}")
            try:
                scraped_data = firecrawl_client.scrape_url(url, params={'pageOptions': {'onlyMainContent': True, 'maxPagesToScrape': 1}})
                if scraped_data and scraped_data.get("success") and scraped_data.get("data"):
                    markdown_content = scraped_data["data"].get("markdown", scraped_data["data"].get("content", ""))
                    if not markdown_content: continue

                    prompt_vars = {"scraped_markdown_content": markdown_content[:15000], "source_url": url}
                    llm_response_str = get_llm_response(
                        prompt_template_str=firecrawl_processing_prompts.PROMPT_EXTRACT_INVESTOR_INFO_FROM_SCRAPED_PAGE,
                        input_variables=prompt_vars, llm_provider=llm_provider, llm_model=llm_model,
                        temperature=llm_kwargs.get("temperature", 0.1), max_tokens=llm_kwargs.get("max_tokens", 3000)
                    )
                    
                    extracted_data_json = extract_json_from_response(llm_response_str)
                    
                    if extracted_data_json and "extracted_profiles" in extracted_data_json:
                        investors_on_page = extracted_data_json.get("extracted_profiles", [])
                        for inv in investors_on_page: inv["source_platform"] = url
                        all_found_investors.extend(investors_on_page)
                    else:
                        st.warning(f"Could not extract JSON profiles for {url}")
            except Exception as e_scrape_url:
                st.error(f"Error scraping direct URL {url}: {e_scrape_url}")

    # 2. Perform General Searches (with limits)
    if "General Web Search via Firecrawl" in data_sources or (not urls_to_scrape and keywords_for_search):
        st.write(f"Performing general Firecrawl web searches for keywords: {', '.join(keywords_for_search)}")
        
        for i, keyword in enumerate(keywords_for_search):
            st.write(f"Searching: '{keyword}' ({i+1}/{len(keywords_for_search)})")
            try:
                # Search, limit to slightly more than max_scrapes to have options
                search_results = firecrawl_client.search(query=keyword, params={"pageOptions": {"limit": max_scrapes_per_keyword + 2}}) 
                
                search_data = []
                if search_results and isinstance(search_results, dict):
                    if "success" in search_results and search_results.get("success") and "data" in search_results:
                        search_data = search_results.get("data", [])
                    elif "results" in search_results:
                        search_data = search_results.get("results", [])
                
                st.success(f"Found {len(search_data)} search results for '{keyword}'")

                # Limit the number of scrapes per keyword to save credits
                count_scraped = 0
                for result_item in search_data:
                    if count_scraped >= max_scrapes_per_keyword:
                        break
                        
                    page_url = result_item.get('url') or result_item.get('link') or result_item.get('href')
                    if not page_url: continue

                    # Use content from search result if available/sufficient? 
                    # Usually snippets are too short (`markdown` field might be present though).
                    # Firecrawl /search often returns 'markdown' or 'content' in the result if configured?
                    # The current search call might just return snippets. We'll stick to scraping for quality for now, but limited.
                    
                    st.write(f"Scraping result: {page_url}")
                    scraped_page = firecrawl_client.scrape_url(page_url, params={'pageOptions': {'onlyMainContent': True, 'maxPagesToScrape': 1}})
                    
                    if scraped_page and scraped_page.get("success") and scraped_page.get("data"):
                        page_markdown = scraped_page["data"].get("markdown", scraped_page["data"].get("content", ""))
                        if page_markdown:
                            prompt_vars = {"scraped_markdown_content": page_markdown[:15000], "source_url": page_url}
                            llm_response_str = get_llm_response(
                                prompt_template_str=firecrawl_processing_prompts.PROMPT_EXTRACT_INVESTOR_INFO_FROM_SCRAPED_PAGE,
                                input_variables=prompt_vars,
                                llm_provider=llm_provider,
                                llm_model=llm_model,
                                temperature=llm_kwargs.get("temperature", 0.1),
                                max_tokens=llm_kwargs.get("max_tokens", 3000)
                            )
                            
                            extracted_data_json = extract_json_from_response(llm_response_str)
                            if extracted_data_json and "extracted_profiles" in extracted_data_json:
                                investors_on_page = extracted_data_json.get("extracted_profiles", [])
                                for inv in investors_on_page: 
                                    inv["source_platform"] = f"Firecrawl Search: {keyword} ({page_url})"
                                all_found_investors.extend(investors_on_page)
                                count_scraped += 1
                            else:
                                st.warning(f"No structured data extracted from {page_url}")

            except Exception as e_search:
                st.error(f"Error during Firecrawl search for '{keyword}': {e_search}")

    # Fallback if nothing found
    if not all_found_investors:
        st.warning("No investors were found during the search.")
        # Minimal placeholder generator
        fallback_investors = []
        for i, keyword in enumerate(keywords_for_search[:2]):
            fallback_investors.append({
                "name": f"Example {keyword.title()} Investor",
                "description": f"Placeholder for '{keyword}'. No actual results found.",
                "investor_type": "Unknown",
                "source_platform": "Fallback Generator"
            })
        return fallback_investors

    # Deduplicate
    unique_investors = []
    seen_keys = set()
    for investor in all_found_investors:
        key_tuple = (investor.get('name','').lower(), investor.get('website_url','').lower().replace("www.","").rstrip('/'))
        if key_tuple not in seen_keys or not investor.get('website_url'):
            unique_investors.append(investor)
            seen_keys.add(key_tuple)

    return unique_investors

# Example of how these functions might be called (for testing purposes)
if __name__ == "__main__":
    # Mocking get_llm_response for local testing to avoid API keys and provider checks
    import core.investor_strategy_logic as local_module
    
    def mock_get_llm_response(*args, **kwargs):
        # Return a valid JSON string compliant with what the logic expects
        import json
        if "strategy" in kwargs.get("prompt_template_str", ""):
            return json.dumps({
                "summary": "Mock Strategy Summary",
                "keywords_for_search": ["Mock Keyword 1", "Mock Keyword 2"],
                "data_sources_to_check": ["http://mock-source.com"],
                "outreach_angle": "Mock Outreach"
            })
        else: # Firecrawl processing mock
             return json.dumps({
                "extracted_profiles": [{
                    "name": "Mock Investor",
                    "description": "Mock Description",
                    "investor_type": "VC",
                    "website_url": "http://mock-investor.com"
                }]
             })

    # Monkeypatch the function in the module scope
    local_module.get_llm_response = mock_get_llm_response

    mock_profile = {
        "industry": "AI-driven Healthcare",
        "stage": "Seed",
        "funding_needed": "$1M",
        "usp": "Novel diagnostic algorithm with 99% accuracy"
    }
    mock_market_trends = "Telemedicine adoption, AI in drug discovery"
    mock_investor_preferences = "Investors with portfolio in HealthTech, Series A follow-on potential"

    print("--- Testing Strategy Development (Mock LLM) ---")
    strategy = develop_strategy_with_llm(
        mock_profile, mock_market_trends, mock_investor_preferences,
        llm_provider="mock_provider", llm_model="mock_model"
    )
    print(f"Generated Strategy: {strategy}")

    print("\n--- Testing Investor Search Execution (Mock Firecrawl & LLM) ---")
    
    # Mock Firecrawl client
    class MockFirecrawl:
        def scrape_url(self, url, params=None):
            return {"success": True, "data": {"markdown": "Mock page content about investors."}}
        def search(self, query, params=None):
            return {"success": True, "data": [{"url": "http://mock-result.com", "markdown": "Mock search result"}]}
            
    fc_client = MockFirecrawl()

    search_results = execute_investor_search(
        strategy,
        firecrawl_client=fc_client, 
        llm_provider="mock_refinement_provider",
        llm_model="mock_refinement_model"
    )
    print(f"Search Results ({len(search_results)}):")
    for res in search_results:
        print(res)
