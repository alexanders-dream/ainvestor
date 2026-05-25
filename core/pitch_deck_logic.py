from typing import List, Optional
try:
    from langchain_core.pydantic_v1 import BaseModel, Field
except ImportError:
    from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from .llm_interface import get_llm_response
from prompts import pitch_deck_advisor_prompts

# Define Pydantic model for structured data
class StartupProfile(BaseModel):
    company_name: str = Field(description="The name of the startup company.")
    industry_sector: str = Field(description="The primary industry or sector the startup operates in.")
    current_stage: str = Field(description="The current stage of the startup (e.g., Pre-Seed, Seed, Series A).")
    funding_ask_amount: str = Field(description="The amount of funding being requested (e.g., $500k, $2M).")
    usp: str = Field(description="The Unique Selling Proposition or key differentiator of the startup.")
    keywords_for_investor_search: List[str] = Field(description="List of slightly broader keywords suitable for searching for potential investors.")

def get_deck_feedback_from_llm(extracted_sections_data: dict, provider: str, model: str = None, **kwargs):
    """
    Generates overall feedback for a pitch deck using an LLM.

    Args:
        extracted_sections_data (dict): A dictionary containing text from various pitch deck sections.
                                        Expected keys match placeholders in the prompt template.
        provider (str): The LLM provider to use.
        model (str, optional): The specific model name. Defaults to provider's default.
        **kwargs: Additional keyword arguments to pass to the LLM.

    Returns:
        str: The LLM-generated feedback.
    """
    prompt_variables = {
        "full_deck_text": extracted_sections_data.get('raw_full_text', '')
    }

    response = get_llm_response(
        prompt_template_str=pitch_deck_advisor_prompts.PROMPT_OVERALL_FEEDBACK,
        input_variables=prompt_variables,
        llm_provider=provider,
        llm_model=model,
        **kwargs
    )
    return response

def get_section_refinement_from_llm(section_name: str, section_text: str, startup_usp: str, 
                                    provider: str, model: str = None, **kwargs):
    """
    Refines a specific section of a pitch deck using an LLM.

    Args:
        section_name (str): The name of the section (e.g., "Problem Statement").
        section_text (str): The original text of the section.
        startup_usp (str): The startup's Unique Selling Proposition.
        provider (str): The LLM provider.
        model (str, optional): The specific model name.
        **kwargs: Additional keyword arguments for the LLM.

    Returns:
        str: The LLM-generated refined text.
    """
    prompt_template = pitch_deck_advisor_prompts.get_messaging_refinement_prompt_template()
    
    input_vars = {
        "section_name": section_name,
        "section_text": section_text,
        "startup_usp": startup_usp
    }
    
    response = get_llm_response(
        prompt_template_str=prompt_template,
        input_variables=input_vars,
        llm_provider=provider,
        llm_model=model,
        **kwargs
    )
    return response

def extract_structured_data_from_deck_text(full_deck_text: str, provider: str, model: str = None, **kwargs):
    """
    Extracts structured data (company name, industry, stage, USP, etc.) from the pitch deck text using an LLM
    and Pydantic for robust parsing.

    Args:
        full_deck_text (str): The full extracted text from the pitch deck.
        provider (str): The LLM provider to use.
        model (str, optional): The specific model name. Defaults to provider's default.
        **kwargs: Additional keyword arguments to pass to the LLM.

    Returns:
        dict: A dictionary containing the extracted structured data.
              Returns None if parsing fails.
    """
    # Initialize the parser
    parser = JsonOutputParser(pydantic_object=StartupProfile)
    
    # Get format instructions
    format_instructions = parser.get_format_instructions()
    
    # Inject format instructions into the prompt
    prompt_with_format = pitch_deck_advisor_prompts.PROMPT_EXTRACT_STRUCTURED_DATA + "\n\n" + format_instructions

    prompt_variables = {
        "full_deck_text": full_deck_text
    }

    # Default to lower temp for Pydantic/JSON
    llm_params = {"temperature": kwargs.get("temperature", 0.1)} 
    llm_params.update(kwargs)

    try:
        raw_response = get_llm_response(
            prompt_template_str=prompt_with_format,
            input_variables=prompt_variables,
            llm_provider=provider,
            llm_model=model,
            **llm_params 
        )
        
        # Pydantic parser can parse the string output from the LLM
        parsed_obj = parser.parse(raw_response)
        return parsed_obj
    except Exception as e:
        print(f"Error parsing structured extraction output: {e}")
        return None
