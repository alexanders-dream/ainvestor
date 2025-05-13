import json
from .llm_interface import get_llm_response
from prompts import pitch_deck_advisor_prompts
# from .utils import extract_text_from_pdf, extract_text_from_pptx # utils.py now has parse_pitch_deck

def get_deck_feedback_from_llm(extracted_sections_data: dict, provider: str, model: str = None, **kwargs):
    """
    Generates overall feedback for a pitch deck using an LLM.

    Args:
        extracted_sections_data (dict): A dictionary containing text from various pitch deck sections.
                                        Expected keys match placeholders in the prompt template.
        provider (str): The LLM provider to use (e.g., "openai", "anthropic").
        model (str, optional): The specific model name. Defaults to provider's default.
        **kwargs: Additional keyword arguments to pass to the LLM.

    Returns:
        str: The LLM-generated feedback.
    """
    # The PROMPT_OVERALL_FEEDBACK now expects 'full_deck_text'.
    # extracted_sections_data from utils.parse_pitch_deck contains 'raw_full_text'.
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

# Example of how this might be used with file parsing (to be completed in utils.py)
# def analyze_uploaded_pitch_deck(uploaded_file, provider: str, model: str = None):
#     """
#     Parses an uploaded pitch deck file, extracts text, and gets LLM feedback.
#     """
#     file_extension = uploaded_file.name.split(".")[-1].lower()
#     raw_text = ""
#     if file_extension == "pdf":
#         raw_text = extract_text_from_pdf(uploaded_file) # Needs implementation in utils
#     elif file_extension in ["pptx"]:
#         raw_text = extract_text_from_pptx(uploaded_file) # Needs implementation in utils
#     else:
#         raise ValueError("Unsupported file type. Please upload PDF or PPTX.")

#     # This is a simplification. Real extraction would be more structured.
#     # For MVP, we might ask the user to paste text or have a very simple heuristic.
#     extracted_sections = {
#         "problem": "Section about the problem...", # Placeholder
#         "solution": "Section about the solution...", # Placeholder
#         # ... and so on
#         "full_text": raw_text # Or just pass the full text if sectioning is too complex for v1
#     }
    
#     feedback = get_deck_feedback_from_llm(extracted_sections, provider, model)
#     return feedback

def extract_structured_data_from_deck_text(full_deck_text: str, provider: str, model: str = None, **kwargs):
    """
    Extracts structured data (company name, industry, stage, USP, etc.) from the pitch deck text using an LLM.

    Args:
        full_deck_text (str): The full extracted text from the pitch deck.
        provider (str): The LLM provider to use.
        model (str, optional): The specific model name. Defaults to provider's default.
        **kwargs: Additional keyword arguments to pass to the LLM.

    Returns:
        dict: A dictionary containing the extracted structured data.
              Returns None if parsing fails or LLM response is not valid JSON.
    """
    prompt_variables = {
        "full_deck_text": full_deck_text
    }

    # Ensure a higher temperature might be better for extraction if the text is varied.
    # However, for JSON output, lower temperature might be more reliable.
    # Let's use the passed kwargs or a sensible default if not specified.
    llm_params = {"temperature": kwargs.get("temperature", 0.2)} # Default to lower temp for JSON
    llm_params.update(kwargs)


    raw_response = get_llm_response(
        prompt_template_str=pitch_deck_advisor_prompts.PROMPT_EXTRACT_STRUCTURED_DATA,
        input_variables=prompt_variables,
        llm_provider=provider,
        llm_model=model,
        **llm_params # Pass all relevant kwargs
    )

    try:
        # The LLM is asked to return a JSON string.
        # Clean up potential markdown code block fences if present
        if raw_response.strip().startswith("```json"):
            raw_response = raw_response.strip()[7:]
            if raw_response.strip().endswith("```"):
                raw_response = raw_response.strip()[:-3]
        
        extracted_info = json.loads(raw_response)
        return extracted_info
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON from LLM response for structured data extraction: {e}")
        print(f"Raw response was: {raw_response}")
        # Optionally, try to extract from a more lenient parsing if it's a common issue,
        # or return a specific error structure. For now, return None.
        return None
    except Exception as e:
        print(f"An unexpected error occurred during structured data extraction: {e}")
        return None
