import pandas as pd
import yaml # Keep for potential direct use if needed, though yaml_utils is preferred
import streamlit as st # For st.secrets and potentially st.error/st.info
from .llm_interface import get_llm_response
from prompts import firecrawl_processing_prompts # Using the new prompt
from .firecrawl_api import FirecrawlAPI
from .yaml_utils import load_yaml as load_yaml_util, dump_yaml as dump_yaml_util, extract_yaml_from_text, create_default_investor_yaml # Renamed to avoid conflict
import io # For reading file content

# Path to the local YAML database
INVESTOR_DB_PATH = "data/investor_db.yaml"

def load_investor_database():
    """
    Loads the investor database from a YAML file.

    Returns:
        pd.DataFrame: DataFrame containing investor data.
                      Returns an empty DataFrame if the file is not found, is empty, or parsing fails.
    Raises:
        FileNotFoundError: If the investor_db.yaml is not found.
        Exception: For other file reading or YAML parsing errors.
    """
    try:
        with open(INVESTOR_DB_PATH, 'r', encoding='utf-8') as f:
            yaml_content = f.read()
        
        if not yaml_content.strip(): # Check if file is empty or only whitespace
            print(f"Info: Investor database file {INVESTOR_DB_PATH} is empty.")
            return pd.DataFrame()

        data = load_yaml_util(yaml_content) # Use the renamed utility
        
        if data is None: # load_yaml_util returns None on error
            print(f"Error: Failed to parse YAML from {INVESTOR_DB_PATH}. load_yaml_util returned None.")
            return pd.DataFrame() # Return empty DataFrame if parsing failed

        if not isinstance(data, list):
            print(f"Error: YAML data in {INVESTOR_DB_PATH} is not a list as expected. Found type: {type(data)}")
            return pd.DataFrame()
        
        if not data: # Empty list in YAML
             print(f"Info: Investor database {INVESTOR_DB_PATH} contains an empty list.")
             return pd.DataFrame()

        df = pd.DataFrame(data)
        # Basic validation can remain similar if column names are consistent
        # Example:
        # if 'Investor Name' not in df.columns or 'Focus Industry' not in df.columns:
        #     st.warning("Investor database (YAML) is missing essential columns.") # Use st.warning or print
        #     # Depending on strictness, you might return an empty df or the df as is
        return df
    except FileNotFoundError:
        # This will be caught by the calling function in the Streamlit page
        raise FileNotFoundError(f"Investor database not found at {INVESTOR_DB_PATH}")
    except yaml.YAMLError as e_yaml: # Catch specific YAML errors if load_yaml_util re-raises them or if direct yaml use
        print(f"Error parsing YAML from {INVESTOR_DB_PATH}: {e_yaml}")
        raise Exception(f"YAML parsing error in {INVESTOR_DB_PATH}: {e_yaml}") # Re-raise as a general exception
    except Exception as e:
        # Catch other potential errors during file reading or DataFrame conversion
        print(f"Error loading investor database from YAML: {e}")
        raise # Re-raise the exception to be handled by the caller


def find_investors(industry: str, stage: str, min_investment: int, max_investment: int, keywords: str = "",
                   provider: str = None, model: str = None):
    """
    Finds investors based on specified criteria.
    Currently uses a local CSV database. Can be extended for API calls or LLM-based matching.

    Args:
        industry (str): The target industry.
        stage (str): The investment stage (e.g., Seed, Series A).
        min_investment (int): Minimum desired investment amount.
        max_investment (int): Maximum desired investment amount.
        keywords (str, optional): Additional keywords for searching (e.g., in notes, focus).
        provider (str, optional): LLM provider if LLM-based matching is used.
        model (str, optional): LLM model if LLM-based matching is used.

    Returns:
        pd.DataFrame: A DataFrame of matching investors.
    """
    try:
        investor_df = load_investor_database()
    except FileNotFoundError as e_fnf:
        # If DB not found, return an empty DataFrame immediately.
        # The Streamlit page will handle displaying the error message.
        print(f"Info: {e_fnf}") # Log this info
        return pd.DataFrame()
    except Exception as e_load: # Catch broader exceptions from load_investor_database
        print(f"Error during investor database loading: {e_load}")
        return pd.DataFrame()


    if investor_df.empty:
        return pd.DataFrame()

    # Normalize column names for filtering (e.g., handle spaces, case)
    # Assuming columns like 'Focus Industry', 'Typical Stage', 'Min Investment', 'Max Investment', 'Notes'
    # This requires the CSV to have consistent column naming.
    # For MVP, we'll assume exact matches or simple string contains.

    # Filter by industry (case-insensitive)
    # Ensure 'Focus Industry' column exists
    if 'Focus Industry' in investor_df.columns:
        filtered_df = investor_df[investor_df['Focus Industry'].str.contains(industry, case=False, na=False)]
    else:
        # If column doesn't exist, can't filter by it. Return current df or empty.
        # For now, let's assume if it's not there, no match is possible on this criteria.
        print(f"Warning: 'Focus Industry' column not found in {INVESTOR_DB_PATH}")
        filtered_df = investor_df # Or pd.DataFrame() if strict

    # Filter by stage (case-insensitive)
    if 'Typical Stage' in filtered_df.columns:
        filtered_df = filtered_df[filtered_df['Typical Stage'].str.contains(stage, case=False, na=False)]
    else:
        print(f"Warning: 'Typical Stage' column not found in {INVESTOR_DB_PATH}")


    # Filter by investment range (requires numeric conversion if stored as strings like "$100k - $1M")
    # This is a simplified filter. A real implementation would parse ranges like "$100k-$500k".
    # For MVP, let's assume 'Min Investment' and 'Max Investment' columns exist and are numeric.
    # If they are not numeric, this will fail or produce incorrect results.
    # A more robust solution would be to parse string ranges from a single 'Investment Range' column.

    # Example: If 'Min Investment' and 'Max Investment' columns exist and are numeric:
    if 'Min Investment' in filtered_df.columns and 'Max Investment' in filtered_df.columns:
        # Ensure columns are numeric, coercing errors to NaN (which are then dropped)
        filtered_df['Min Investment'] = pd.to_numeric(filtered_df['Min Investment'], errors='coerce')
        filtered_df['Max Investment'] = pd.to_numeric(filtered_df['Max Investment'], errors='coerce')
        filtered_df = filtered_df.dropna(subset=['Min Investment', 'Max Investment'])

        # Investor's min <= user's max AND Investor's max >= user's min
        # This means there's an overlap in desired investment ranges.
        filtered_df = filtered_df[
            (filtered_df['Min Investment'] <= max_investment) &
            (filtered_df['Max Investment'] >= min_investment)
        ]
    else:
        print(f"Warning: 'Min Investment' or 'Max Investment' columns not found or not numeric in {INVESTOR_DB_PATH}")


    # Filter by keywords (search in 'Notes' or a general 'Description' column, case-insensitive)
    if keywords and 'Notes' in filtered_df.columns: # Assuming keywords search in 'Notes'
        keyword_list = [kw.strip() for kw in keywords.split(',')]
        # Matches if any keyword is found
        filtered_df = filtered_df[
            filtered_df['Notes'].str.contains('|'.join(keyword_list), case=False, na=False)
        ]
    elif keywords:
        print(f"Warning: 'Notes' column not found for keyword search in {INVESTOR_DB_PATH}")

    # If LLM is to be used for more nuanced matching or ranking:
    # if provider and model and not filtered_df.empty:
    #     # 1. Prepare context from filtered_df (e.g., investor profiles)
    #     # 2. Create a prompt using investor_scout_prompts
    #     # 3. Call get_llm_response
    #     # 4. Parse LLM response to re-rank or further filter `filtered_df`
    #     pass # Placeholder for LLM-based refinement

    return filtered_df.reset_index(drop=True)


AFRICAN_INVESTOR_PLATFORMS = [
    "https://mercury.com/investor-database", # Mercury’s Investor Database (most active Seed & Pre-Seed investors)
    "https://app.folk.app/shared/Seed-and-Series-A-US-VC%27s-b6PIuvmTQF7Mdj4sM4TM1wbsP69DwQP0", # Seed & Series A US VCs (via Folk)
    "https://docs.google.com/spreadsheets/d/1BqNO7l4kXRhjG5jcB89FwRlhuRKBwBKtV7ZHwwLjPhk/edit?gid=1332796676#gid=1332796676", # Deep Tech Investors Mapping (from hello tomorrow)
    "https://docs.google.com/spreadsheets/d/1cRdFZhXLqat04xe7qO-p48wXQ00GWJyrzgHSb3YVIp0/edit?gid=2013669735#gid=2013669735", # European Tech VC Funds (by EuroVC)
    "https://docs.google.com/spreadsheets/d/1fD9cXnxe_zMKCRKouqUa-DugTNRAeN6rdfeaOOI6w-A/edit?gid=354066762#gid=354066762", # TravelTech Investor list
    "https://airtable.com/appi82OqC0sofDlcH/shrdqT0dM0vaIeO9u/tblyAK2VE4dS8O4dZ/viwiaTchRnMLqZqsS?backgroundColor=blue&blocks=hide", # HealthTech Venture Investor List
    "https://app.folk.app/shared/Pre-Seed-Angel-Investor-in-France-uUEIR4cXc3wiSmdsc9m9wCf7lBYPAyGJ", # Pre-Seed Angel Investors in France (via Folk)
    "https://app.folk.app/shared/US-VCs-oc71Oi94yB9vwbfh1XWIQPHTAGQE7FQ1", # 2000+ US VCs grouped by Fund stage, Fund focus, Location
    "https://airtable.com/appLi1yNqogms6CJS/shrWa2dHIwRjTTKwF/tblafXgz5pMd7w3Mn/viwg5FrKTjsTjlB3e?blocks=hide", # NYC Early Stage VC firms list
    "https://ultimatevclist.com/", # Ultimate VC list from Serena
    "https://airtable.com/appZlSZ7bSZeSHOnl/shrHvHjExnm3tFb4X/tblUdpjiyqtQCtiuR", # 107+ VC firms that invest in the Baltics
    "https://www.mountsideventures.com/investor-network", # Mountside Ventures’ list of 50+ VC firms with fresh capital and UK focus
    "https://goldeneggcheck.com/en/venture-capital-investors/", # VC investors in the Netherlands list
    "https://airtable.com/apph9tTMHZwV2BwWX/shrSHRMum8oJmDjFJ/tblQIsXHKoY0EtXO7", # Airtree’s 168+ Australian VC firms
]

def find_investors_firecrawl(
    target_urls: list = None,
    custom_search_query: str = None, # For a general Firecrawl search
    provider: str = None,
    model: str = None,
    **llm_kwargs):
    """
    Finds investors by scraping specified URLs or performing a Firecrawl search,
    then extracting structured data using an LLM.

    Args:
        target_urls (list, optional): A list of specific URLs to scrape.
                                      Defaults to AFRICAN_INVESTOR_PLATFORMS if None.
        custom_search_query (str, optional): A query for Firecrawl's general search if target_urls are not enough.
        provider (str): LLM provider for data extraction.
        model (str, optional): LLM model for data extraction.
        **llm_kwargs: Additional arguments for the LLM.

    Returns:
        pd.DataFrame: A DataFrame of extracted investor profiles.
    """
    if not provider or not model:
        st.error("LLM provider and model must be specified for Firecrawl-based investor scouting.")
        return pd.DataFrame()

    all_extracted_investors = []

    try:
        firecrawl_api_key = st.secrets.get("FIRECRAWL_API_KEY")
        if not firecrawl_api_key:
            st.error("Firecrawl API key not found in st.secrets. Cannot perform web scraping.")
            return pd.DataFrame()
        firecrawl_client = FirecrawlAPI(api_key=firecrawl_api_key)
    except Exception as e:
        st.error(f"Failed to initialize Firecrawl client: {e}")
        return pd.DataFrame()

    urls_to_process = target_urls if target_urls else AFRICAN_INVESTOR_PLATFORMS

    if not urls_to_process and not custom_search_query:
        st.info("No target URLs or custom search query provided for Firecrawl.")
        return pd.DataFrame()

    # Process direct URLs
    for i, url in enumerate(urls_to_process):
        st.write(f"Scraping URL ({i+1}/{len(urls_to_process)}): {url} ...")
        try:
            # Limit scrape for lists, maybe allow full for individual sites if logic is smarter
            scrape_params = {'pageOptions': {'maxPagesToScrape': 1, 'onlyMainContent': True}} if "list" in url.lower() or "platform" in url.lower() else {'pageOptions': {'onlyMainContent': True}}

            scraped_data = firecrawl_client.scrape_url(url, params=scrape_params)

            if scraped_data and scraped_data.get("success") and scraped_data.get("data"):
                markdown_content = scraped_data["data"].get("markdown", scraped_data["data"].get("content", ""))
                if not markdown_content:
                    st.warning(f"No markdown content extracted from {url}")
                    continue

                st.write(f"Extracting investor info from {url} using LLM ({provider}/{model})...")
                prompt_vars = {
                    "scraped_markdown_content": markdown_content[:15000], # Truncate to avoid excessive token usage
                    "source_url": url,
                    "extracted_profiles": [] # Add correct key to prevent missing input error
                }
                llm_response_str = get_llm_response(
                    prompt_template_str=firecrawl_processing_prompts.PROMPT_EXTRACT_INVESTOR_INFO_FROM_SCRAPED_PAGE,
                    input_variables=prompt_vars,
                    llm_provider=provider,
                    llm_model=model,
                    temperature=llm_kwargs.get("temperature", 0.1), # Lower temp for JSON
                    max_tokens=llm_kwargs.get("max_tokens", 3000)
                )

                try:
                    # Extract YAML from the LLM response
                    yaml_content = extract_yaml_from_text(llm_response_str)

                    if not yaml_content:
                        st.warning(f"Could not extract YAML from LLM response for {url}. Creating default structure.")
                        # Create a default YAML structure
                        default_yaml_str = create_default_investor_yaml() # Returns a string
                        extracted_data = load_yaml_util(default_yaml_str) # Parse the string
                        # Add source information
                        if extracted_data and "extracted_profiles" in extracted_data and extracted_data["extracted_profiles"]:
                            extracted_data["extracted_profiles"][0]["name"] = f"Parsing Error for {url.split('/')[-1]}"
                            extracted_data["extracted_profiles"][0]["description"] = f"LLM did not return YAML format for {url}"
                            extracted_data["extracted_profiles"][0]["source_platform"] = url
                            extracted_data["extracted_profiles"][0]["notes"] = f"Raw LLM response: {llm_response_str[:100]}..."
                        else: # Should not happen if create_default_investor_yaml is correct
                            st.error("Failed to create or structure default investor YAML.")
                            extracted_data = {"extracted_profiles": []} # Ensure it's a dict
                    else:
                        # Try to parse the YAML
                        extracted_data = load_yaml_util(yaml_content)
                        if not extracted_data or not isinstance(extracted_data, dict):
                            st.warning(f"Invalid YAML structure from LLM for {url}. Creating default structure.")
                            default_yaml_str = create_default_investor_yaml()
                            extracted_data = load_yaml_util(default_yaml_str)
                            # Add source information
                            if extracted_data and "extracted_profiles" in extracted_data and extracted_data["extracted_profiles"]:
                                extracted_data["extracted_profiles"][0]["name"] = f"Parsing Error for {url.split('/')[-1]}"
                                extracted_data["extracted_profiles"][0]["description"] = f"Invalid YAML structure from LLM for {url}"
                                extracted_data["extracted_profiles"][0]["source_platform"] = url
                                extracted_data["extracted_profiles"][0]["notes"] = f"Raw YAML: {yaml_content[:100]}..."
                            else:
                                st.error("Failed to create or structure default investor YAML after invalid LLM YAML.")
                                extracted_data = {"extracted_profiles": []} # Ensure it's a dict

                    investors_on_page = extracted_data.get("extracted_profiles", [])

                    if investors_on_page:
                        for inv in investors_on_page:
                            inv["source_platform"] = url # Add where it was found
                        all_extracted_investors.extend(investors_on_page)
                        st.success(f"Found {len(investors_on_page)} potential investors/mentions on {url}.")
                    else:
                        st.info(f"LLM did not identify distinct investors on {url} from the scraped content.")
                except yaml.YAMLError as yaml_err:
                    st.warning(f"Could not parse LLM YAML response for {url}. Error: {yaml_err}. Raw: {llm_response_str[:200]}...")
                    # Try a fallback approach - create a default structure
                    all_extracted_investors.append({
                        "name": f"Parsing Error for {url.split('/')[-1]}",
                        "description": f"Failed to parse YAML from LLM response for {url}",
                        "investor_type": "Unknown",
                        "source_platform": url,
                        "notes": "This is a placeholder due to YAML parsing error. Please try again or check the URL manually."
                    })
                except Exception as e_parse:
                    st.warning(f"Error processing LLM YAML response for {url}: {e_parse}")
            else:
                st.warning(f"Failed to scrape or get data from {url}. Response: {scraped_data.get('error') or 'No data'}")
        except Exception as e_scrape:
            st.error(f"Error scraping {url}: {e_scrape}")
            continue # Move to next URL

    # TODO: Implement custom_search_query logic if needed
    # This would involve firecrawl_client.search() and then potentially scraping result URLs

    if not all_extracted_investors:
        return pd.DataFrame()

    df_firecrawl = pd.DataFrame(all_extracted_investors)
    # Basic cleaning: drop if name is missing, ensure list types for relevant fields
    df_firecrawl = df_firecrawl.dropna(subset=['name'])
    for col in ['industry_focus', 'stage_focus', 'geographical_focus', 'portfolio_examples', 'key_people']:
        if col in df_firecrawl.columns:
            df_firecrawl[col] = df_firecrawl[col].apply(lambda x: x if isinstance(x, list) else ([x] if pd.notna(x) else []))

    return df_firecrawl.reset_index(drop=True)


# Example Usage (for testing this module directly):
if __name__ == '__main__':
    # Create a dummy data/investor_db.csv for testing
    dummy_data = {
        'Investor Name': ['TechGrowth Ventures', 'SeedSpark Capital', 'BioHealth Fund', 'Global Impact Investors', 'EarlyStage Angels'],
        'Focus Industry': ['Technology, SaaS', 'Technology, AI, Mobile', 'Healthcare, Biotech', 'Social Impact, Cleantech', 'Technology, Consumer'],
        'Typical Stage': ['Series A, Series B', 'Seed, Pre-Seed', 'Seed, Series A', 'All Stages', 'Seed'],
        'Min Investment': [1000000, 50000, 250000, 500000, 25000], # Numeric
        'Max Investment': [10000000, 500000, 5000000, 10000000, 200000], # Numeric
        'Investment Range (Text)': ['$1M - $10M', '$50k - $500k', '$250k - $5M', '$500k - $10M', '$25k - $200k'], # Text version
        'Contact/Website': ['techgrowth.vc', 'seedspark.com', 'biohealth.fund', 'globalimpact.org', 'earlyangels.net'],
        'Notes': ['Focus on enterprise SaaS solutions.', 'Looking for disruptive AI models.', 'Invests in novel drug discovery.', 'Requires strong ESG metrics.', 'Likes hardware and software consumer products. B2C focus.']
    }
    # Convert dummy_data (list of dicts) to YAML string
    yaml_string = dump_yaml_util(dummy_data_list) # Use the renamed utility

    import os
    if not os.path.exists('data'):
        os.makedirs('data')
    
    # Write the YAML string to the file
    with open(INVESTOR_DB_PATH, 'w', encoding='utf-8') as f:
        f.write(yaml_string)
    print(f"Created dummy YAML {INVESTOR_DB_PATH}")

    # Test data as a list of dictionaries, which is what YAML load should produce before DataFrame conversion
    dummy_data_list = [
        {'Investor Name': 'TechGrowth Ventures', 'Focus Industry': 'Technology, SaaS', 'Typical Stage': 'Series A, Series B', 'Min Investment': 1000000, 'Max Investment': 10000000, 'Investment Range (Text)': '$1M - $10M', 'Contact/Website': 'techgrowth.vc', 'Notes': 'Focus on enterprise SaaS solutions.'},
        {'Investor Name': 'SeedSpark Capital', 'Focus Industry': 'Technology, AI, Mobile', 'Typical Stage': 'Seed, Pre-Seed', 'Min Investment': 50000, 'Max Investment': 500000, 'Investment Range (Text)': '$50k - $500k', 'Contact/Website': 'seedspark.com', 'Notes': 'Looking for disruptive AI models.'},
        {'Investor Name': 'BioHealth Fund', 'Focus Industry': 'Healthcare, Biotech', 'Typical Stage': 'Seed, Series A', 'Min Investment': 250000, 'Max Investment': 5000000, 'Investment Range (Text)': '$250k - $5M', 'Contact/Website': 'biohealth.fund', 'Notes': 'Invests in novel drug discovery.'},
        {'Investor Name': 'Global Impact Investors', 'Focus Industry': 'Social Impact, Cleantech', 'Typical Stage': 'All Stages', 'Min Investment': 500000, 'Max Investment': 10000000, 'Investment Range (Text)': '$500k - $10M', 'Contact/Website': 'globalimpact.org', 'Notes': 'Requires strong ESG metrics.'},
        {'Investor Name': 'EarlyStage Angels', 'Focus Industry': 'Technology, Consumer', 'Typical Stage': 'Seed', 'Min Investment': 25000, 'Max Investment': 200000, 'Investment Range (Text)': '$25k - $200k', 'Contact/Website': 'earlyangels.net', 'Notes': 'Likes hardware and software consumer products. B2C focus.'}
    ]
    
    # Create the dummy investor_db.yaml for testing
    yaml_output_for_db = dump_yaml_util(dummy_data_list)
    if not os.path.exists('data'):
        os.makedirs('data')
    with open(INVESTOR_DB_PATH, 'w', encoding='utf-8') as f:
        f.write(yaml_output_for_db)
    print(f"Recreated dummy {INVESTOR_DB_PATH} for testing.")


    print("\n--- Test 1: Technology, Seed, $100k-$600k ---")
    results1 = find_investors(industry="Technology", stage="Seed", min_investment=100000, max_investment=600000, keywords="AI")
    print(results1)

    print("\n--- Test 2: Healthcare, Series A, $1M-$10M ---")
    results2 = find_investors(industry="Healthcare", stage="Series A", min_investment=1000000, max_investment=10000000)
    print(results2)

    print("\n--- Test 3: NonExistent, Seed, $10k-$50k ---")
    results3 = find_investors(industry="NonExistent", stage="Seed", min_investment=10000, max_investment=50000)
    print(results3) # Should be empty

    print("\n--- Test 4: Technology, Consumer, Keywords 'B2C' ---")
    results4 = find_investors(industry="Technology", stage="Seed", min_investment=20000, max_investment=250000, keywords="B2C, consumer")
    print(results4)

    # Test with a non-existent DB
    # os.remove(INVESTOR_DB_PATH)
    # print("\n--- Test 5: DB not found ---")
    # try:
    #     results5 = find_investors(industry="Technology", stage="Seed", min_investment=100000, max_investment=600000)
    #     print(results5) # Should be empty, error handled in Streamlit page
    # except FileNotFoundError as e:
    #     print(e) # This error should be caught by the UI layer
    # # Recreate for other potential tests
    # Recreate dummy YAML if it was removed for testing 'file not found'
    # yaml_output_for_db_recreate = dump_yaml_util(dummy_data_list)
    # with open(INVESTOR_DB_PATH, 'w', encoding='utf-8') as f:
    #     f.write(yaml_output_for_db_recreate)
