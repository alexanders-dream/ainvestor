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
        # Extract YAML from the LLM response
        yaml_content = extract_yaml_from_text(response_str)

        if not yaml_content:
            st.warning("Could not extract YAML from LLM strategy response. Using fallback.")
            # Fallback mock strategy
            strategy_dict = {
                "summary": "Error: Could not extract YAML from LLM response. Using fallback.",
                "keywords_for_search": [f"{profile.get('industry', 'tech')} investor", f"{profile.get('stage', 'seed')} funding"],
                "data_sources_to_check": AFRICAN_INVESTOR_PLATFORMS + ["General Web Search via Firecrawl"],
                "outreach_angle": "Focus on core value proposition."
            }
        else:
            # Try to parse the YAML
            strategy_dict = load_yaml(yaml_content)
            if not strategy_dict or not isinstance(strategy_dict, dict):
                st.warning("Invalid YAML structure from LLM strategy response. Using fallback.")
                # Fallback mock strategy
                strategy_dict = {
                    "summary": "Error: Invalid YAML structure from LLM. Using fallback.",
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
    except yaml.YAMLError as e:
        st.error(f"Failed to parse YAML strategy from LLM response: {e}. Raw response: {response_str[:500]}")
        # Fallback mock strategy if parsing fails
        return {
            "summary": "Error: Could not parse LLM strategy YAML. Using fallback.",
            "keywords_for_search": [f"{profile.get('industry', 'tech')} investor", f"{profile.get('stage', 'seed')} funding"],
            "data_sources_to_check": AFRICAN_INVESTOR_PLATFORMS + ["General Web Search via Firecrawl"],
            "outreach_angle": "Focus on core value proposition."
        }
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
                            llm_provider: str = None, llm_model: str = None, **llm_kwargs):
    """
    Executes the investor search based on the developed strategy.
    This would involve using FirecrawlAPI for web searches and potentially an LLM for refining queries or results.

    Args:
        strategy (dict): The strategy developed by develop_strategy_with_llm.
        firecrawl_client (FirecrawlAPI, optional): An instance of the FirecrawlAPI client.
                                                 If None, one might be initialized here or error.
        llm_provider (str, optional): The selected LLM provider for any refinement tasks.
        llm_model (str, optional): The specific LLM model for refinement.
        **llm_kwargs: Additional arguments for the LLM.


    Returns:
        list: A list of dictionaries, where each dictionary represents a found investor.
              Example: [{"name": "Investor X", "type": "VC", "focus": "SaaS", ...}, ...]
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
        elif source in AFRICAN_INVESTOR_PLATFORMS: # Check if it's a known platform name
             urls_to_scrape.append(source) # The find_investors_firecrawl will resolve this if it's a direct URL

    # Add AFRICAN_INVESTOR_PLATFORMS if "africa" keyword is present or implied
    if any("africa" in kw.lower() for kw in keywords_for_search) or \
       any("africa" in ds.lower() for ds in data_sources):
        urls_to_scrape.extend(AFRICAN_INVESTOR_PLATFORMS)

    # Remove duplicates from urls_to_scrape
    urls_to_scrape = list(set(urls_to_scrape))

    # Debug logging
    st.write(f"Debug: Strategy includes {len(keywords_for_search)} search keywords and {len(urls_to_scrape)} URLs to scrape")

    # Check if we have a valid Firecrawl client
    if not firecrawl_client:
        st.error("Firecrawl client initialization failed. Check your API key.")
        return [{"name": "API Error", "details": "Firecrawl API client could not be initialized. Check your API key."}]

    urls_to_scrape = sorted(list(set(urls_to_scrape))) # Unique URLs

    # Scrape direct URLs
    if urls_to_scrape:
        st.write(f"Strategy suggests scraping {len(urls_to_scrape)} specific URLs...")
        for i, url in enumerate(urls_to_scrape):
            st.write(f"Processing URL ({i+1}/{len(urls_to_scrape)}): {url}")
            try:
                scraped_data = firecrawl_client.scrape_url(url, params={'pageOptions': {'onlyMainContent': True, 'maxPagesToScrape': 1}})
                if scraped_data and scraped_data.get("success") and scraped_data.get("data"):
                    markdown_content = scraped_data["data"].get("markdown", scraped_data["data"].get("content", ""))
                    if not markdown_content: continue

                    prompt_vars = {"scraped_markdown_content": markdown_content[:15000], "source_url": url, "extracted_profiles": []}
                    llm_response_str = get_llm_response(
                        prompt_template_str=firecrawl_processing_prompts.PROMPT_EXTRACT_INVESTOR_INFO_FROM_SCRAPED_PAGE,
                        input_variables=prompt_vars, llm_provider=llm_provider, llm_model=llm_model,
                        temperature=llm_kwargs.get("temperature", 0.1), max_tokens=llm_kwargs.get("max_tokens", 3000)
                    )
                    try:
                        # Extract YAML from the LLM response
                        yaml_content = extract_yaml_from_text(llm_response_str)

                        if not yaml_content:
                            st.warning(f"Could not extract YAML from LLM response for {url}. Creating default structure.")
                            # Create a default YAML structure
                            default_yaml = create_default_investor_yaml()
                            extracted_data = load_yaml(default_yaml)
                            # Add source information
                            extracted_data["extracted_profiles"][0]["name"] = f"Parsing Error for {url.split('/')[-1]}"
                            extracted_data["extracted_profiles"][0]["description"] = f"LLM did not return YAML format for {url}"
                            extracted_data["extracted_profiles"][0]["source_platform"] = url
                            extracted_data["extracted_profiles"][0]["notes"] = f"Raw LLM response: {llm_response_str[:100]}..."
                        else:
                            # Try to parse the YAML
                            extracted_data = load_yaml(yaml_content)
                            if not extracted_data or not isinstance(extracted_data, dict):
                                st.warning(f"Invalid YAML structure from LLM for {url}. Creating default structure.")
                                default_yaml = create_default_investor_yaml()
                                extracted_data = load_yaml(default_yaml)
                                # Add source information
                                extracted_data["extracted_profiles"][0]["name"] = f"Parsing Error for {url.split('/')[-1]}"
                                extracted_data["extracted_profiles"][0]["description"] = f"Invalid YAML structure from LLM for {url}"
                                extracted_data["extracted_profiles"][0]["source_platform"] = url
                                extracted_data["extracted_profiles"][0]["notes"] = f"Raw YAML: {yaml_content[:100]}..."

                        investors_on_page = extracted_data.get("extracted_profiles", [])

                        for inv in investors_on_page: inv["source_platform"] = url
                        all_found_investors.extend(investors_on_page)
                    except yaml.YAMLError as yaml_err:
                        st.warning(f"Could not parse LLM YAML for {url}. Error: {yaml_err}. Raw: {llm_response_str[:200]}")
                        # Try a fallback approach - create a default structure
                        all_found_investors.append({
                            "name": f"Parsing Error for {url.split('/')[-1]}",
                            "description": f"Failed to parse YAML from LLM response for {url}",
                            "investor_type": "Unknown",
                            "source_platform": url,
                            "notes": "This is a placeholder due to YAML parsing error. Please try again or check the URL manually."
                        })
                    except Exception as e_json:
                        st.warning(f"Could not parse LLM JSON for {url}: {e_json}. Response: {llm_response_str[:200]}")
            except Exception as e_scrape_url:
                st.error(f"Error scraping direct URL {url}: {e_scrape_url}")

    # Perform Firecrawl general searches using keywords
    if "General Web Search via Firecrawl" in data_sources or not urls_to_scrape: # If no specific URLs, do general search
        st.write(f"Performing general Firecrawl web searches for keywords: {', '.join(keywords_for_search)}")
        for i, keyword in enumerate(keywords_for_search):
            st.write(f"Firecrawl searching for: '{keyword}' ({i+1}/{len(keywords_for_search)})")
            try:
                # Firecrawl search returns a list of search results, not directly scrape content
                search_results = firecrawl_client.search(query=keyword, params={"pageOptions": {"limit": 3}}) # Limit to top 3 results per keyword

                # Debug the search results structure
                st.write(f"Debug: Firecrawl search returned structure: {list(search_results.keys()) if isinstance(search_results, dict) else type(search_results)}")

                # Handle different response formats
                search_data = []
                if search_results and isinstance(search_results, dict):
                    # Check for the new response format with 'success', 'data', 'returnCode'
                    if "success" in search_results and search_results.get("success") and "data" in search_results:
                        search_data = search_results.get("data", [])
                        if not isinstance(search_data, list):
                            st.warning(f"Unexpected data format in search results: {type(search_data)}")
                            search_data = []
                        else:
                            st.success(f"Found {len(search_data)} search results for '{keyword}'")
                    # Check for the original expected format with direct 'results' field
                    elif "results" in search_results:
                        search_data = search_results.get("results", [])
                        st.success(f"Found {len(search_data)} search results for '{keyword}' (original format)")
                    else:
                        st.warning(f"Unexpected search result format for '{keyword}': {list(search_results.keys())}")

                # Process each search result
                for result_item in search_data:
                    # Extract URL and content, handling different possible field names
                    page_url = None
                    if isinstance(result_item, dict):
                        # Try different possible field names for URL
                        for url_field in ['url', 'link', 'href']:
                            if url_field in result_item:
                                page_url = result_item.get(url_field)
                                if page_url:
                                    break

                        # Try different possible field names for content
                        page_markdown = None
                        for content_field in ['markdown', 'content', 'text', 'snippet']:
                            if content_field in result_item:
                                page_markdown = result_item.get(content_field)
                                if page_markdown:
                                    break
                    else:
                        st.warning(f"Search result item is not a dictionary: {type(result_item)}")
                        continue

                    # Check if we have a valid URL
                    if not page_url:
                        st.warning(f"No URL found in search result item")
                        continue

                    # If no content was found in the search result, scrape the URL
                    if not page_markdown:
                        st.write(f"Search result for '{keyword}' lacks direct content, scraping URL: {page_url}")
                        scraped_page = firecrawl_client.scrape_url(page_url, params={'pageOptions': {'onlyMainContent': True, 'maxPagesToScrape': 1}})
                        if scraped_page and scraped_page.get("success") and scraped_page.get("data"):
                            page_markdown = scraped_page["data"].get("markdown", scraped_page["data"].get("content", ""))
                        else:
                            st.warning(f"Could not scrape search result URL: {page_url}")
                            continue

                    # Skip if we still don't have content
                    if not page_markdown:
                        st.warning(f"No content found for URL: {page_url}")
                        continue

                    # Process the content with LLM
                    prompt_vars = {"scraped_markdown_content": page_markdown[:15000], "source_url": page_url, "extracted_profiles": []}
                    llm_response_str = get_llm_response(
                        prompt_template_str=firecrawl_processing_prompts.PROMPT_EXTRACT_INVESTOR_INFO_FROM_SCRAPED_PAGE,
                        input_variables=prompt_vars,
                        llm_provider=llm_provider,
                        llm_model=llm_model,
                        temperature=llm_kwargs.get("temperature", 0.1),
                        max_tokens=llm_kwargs.get("max_tokens", 3000)
                    )

                    try:
                        # Extract YAML from the LLM response
                        yaml_content = extract_yaml_from_text(llm_response_str)

                        if not yaml_content:
                            st.warning(f"Could not extract YAML from LLM response for search result {page_url}. Creating default structure.")
                            # Create a default YAML structure
                            default_yaml = create_default_investor_yaml()
                            extracted_data = load_yaml(default_yaml)
                            # Add source information
                            extracted_data["extracted_profiles"][0]["name"] = f"Parsing Error for {page_url.split('/')[-1]}"
                            extracted_data["extracted_profiles"][0]["description"] = f"LLM did not return YAML format for search result"
                            extracted_data["extracted_profiles"][0]["source_platform"] = f"Firecrawl Search: {keyword} ({page_url})"
                            extracted_data["extracted_profiles"][0]["notes"] = f"Raw LLM response: {llm_response_str[:100]}..."
                        else:
                            # Try to parse the YAML
                            extracted_data = load_yaml(yaml_content)
                            if not extracted_data or not isinstance(extracted_data, dict):
                                st.warning(f"Invalid YAML structure from LLM for search result {page_url}. Creating default structure.")
                                default_yaml = create_default_investor_yaml()
                                extracted_data = load_yaml(default_yaml)
                                # Add source information
                                extracted_data["extracted_profiles"][0]["name"] = f"Parsing Error for {page_url.split('/')[-1]}"
                                extracted_data["extracted_profiles"][0]["description"] = f"Invalid YAML structure from LLM for search result"
                                extracted_data["extracted_profiles"][0]["source_platform"] = f"Firecrawl Search: {keyword} ({page_url})"
                                extracted_data["extracted_profiles"][0]["notes"] = f"Raw YAML: {yaml_content[:100]}..."

                        investors_on_page = extracted_data.get("extracted_profiles", [])

                        for inv in investors_on_page:
                            inv["source_platform"] = f"Firecrawl Search: {keyword} ({page_url})"
                        all_found_investors.extend(investors_on_page)
                    except yaml.YAMLError as yaml_err:
                        st.warning(f"Could not parse LLM YAML for search result {page_url}. Error: {yaml_err}. Raw: {llm_response_str[:200]}")
                        # Try a fallback approach - create a default structure
                        all_found_investors.append({
                            "name": f"Parsing Error for {page_url.split('/')[-1]}",
                            "description": f"Failed to parse YAML from LLM response for search result",
                            "investor_type": "Unknown",
                            "source_platform": f"Firecrawl Search: {keyword} ({page_url})",
                            "notes": "This is a placeholder due to YAML parsing error. Please try again or check the URL manually."
                        })
                    except Exception as e:
                        st.warning(f"Could not parse LLM YAML for search result {page_url}: {e}. Response: {llm_response_str[:200]}")
            except Exception as e_search:
                st.error(f"Error during Firecrawl search for '{keyword}': {e_search}")

    # Debug logging
    st.write(f"Debug: Searched {len(urls_to_scrape)} URLs and {len(keywords_for_search)} keywords")
    st.write(f"Debug: Found {len(all_found_investors)} investors before deduplication")

    if not all_found_investors:
        st.warning("No investors were found during the search. This could be due to API limitations, parsing issues, or no matching results.")

        # Create fallback investors based on the strategy
        fallback_investors = []

        # Add a fallback investor for each keyword
        for i, keyword in enumerate(keywords_for_search[:3]):  # Limit to first 3 keywords
            fallback_investors.append({
                "name": f"Potential {keyword.title()} Investor",
                "description": f"This is a placeholder investor based on your search for '{keyword}'. No actual investors were found during the search.",
                "investor_type": "Unknown",
                "industry_focus": [keyword.split()[0]] if keyword.split() else [],
                "stage_focus": [strategy.get("stage", "Seed")],
                "geographical_focus": [],
                "contact_email": "",
                "website_url": "",
                "key_people": [],
                "portfolio_examples": [],
                "notes": "This is a placeholder due to no search results. Try refining your search strategy or checking the Firecrawl API connection.",
                "source_platform": "Fallback Generator"
            })

        if fallback_investors:
            st.info("Created placeholder investors based on your search keywords. These are not real investors but suggestions for search directions.")
            return fallback_investors
        else:
            return [{"name": "No Investors Found", "details": "Strategy execution with Firecrawl yielded no results."}]

    # Convert to DataFrame for consistency if needed by UI, though list of dicts is fine
    # df_results = pd.DataFrame(all_found_investors)
    # df_results = df_results.drop_duplicates(subset=['name', 'website_url']).reset_index(drop=True)
    # return df_results.to_dict('records')

    # Deduplicate based on name and website_url
    unique_investors = []
    seen_keys = set()
    for investor in all_found_investors:
        # Create a unique key for deduplication, preferring website_url if available
        key_tuple = (investor.get('name','').lower(), investor.get('website_url','').lower().replace("www.","").rstrip('/'))
        if key_tuple not in seen_keys or not investor.get('website_url'): # Allow if no website for more leniency
            unique_investors.append(investor)
            seen_keys.add(key_tuple)

    return unique_investors

# Example of how these functions might be called (for testing purposes)
if __name__ == "__main__":
    # This block will only run if the script is executed directly
    # It won't run when imported as a module by Streamlit pages.

    # Mock st.secrets for local testing if needed, or ensure secrets.toml is populated
    class MockSecrets(dict):
        def get(self, key, default=None):
            return self.get(key, default)

    # st.secrets = MockSecrets(FIRECRAWL_API_KEY="YOUR_FIRECRAWL_KEY_HERE_IF_TESTING_REAL_API")
    # st.secrets = MockSecrets() # No key, will trigger warning in execute_investor_search

    mock_profile = {
        "industry": "AI-driven Healthcare",
        "stage": "Seed",
        "funding_needed": "$1M",
        "usp": "Novel diagnostic algorithm with 99% accuracy"
    }
    mock_market_trends = "Telemedicine adoption, AI in drug discovery"
    mock_investor_preferences = "Investors with portfolio in HealthTech, Series A follow-on potential"

    print("--- Testing Strategy Development (Mock LLM) ---")
    # Assuming llm_interface and prompts are structured to be importable
    # and SUPPORTED_PROVIDERS is available for selection.
    # For direct script execution, these would need to be handled carefully.
    # We'll pass dummy provider/model for now.
    strategy = develop_strategy_with_llm(
        mock_profile, mock_market_trends, mock_investor_preferences,
        llm_provider="mock_provider", llm_model="mock_model"
    )
    print(f"Generated Strategy: {strategy}")

    print("\n--- Testing Investor Search Execution (Mock Firecrawl & LLM) ---")
    # To test with a real FirecrawlAPI, you'd initialize it:
    # try:
    #     firecrawl_api_key = st.secrets.get("FIRECRAWL_API_KEY")
    #     if not firecrawl_api_key:
    #         print("FIRECRAWL_API_KEY not in st.secrets. Skipping real Firecrawl test.")
    #         fc_client = None
    #     else:
    #         fc_client = FirecrawlAPI(api_key=firecrawl_api_key)
    # except Exception as e:
    #     print(f"Error initializing FirecrawlAPI for test: {e}")
    #     fc_client = None

    fc_client = None # Forcing mock search without API key for this example run

    search_results = execute_investor_search(
        strategy,
        firecrawl_client=fc_client, # Pass None to simulate no API key or mock
        llm_provider="mock_refinement_provider",
        llm_model="mock_refinement_model"
    )
    print(f"Search Results ({len(search_results)}):")
    for res in search_results:
        print(res)

    # To run this test: python -m core.investor_strategy_logic
    # (assuming your project root is the parent of 'core')
    # You might need to adjust imports or PYTHONPATH if running directly like this,
    # or use a test runner that handles imports correctly.
