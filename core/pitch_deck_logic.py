from typing import List, Optional
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

def _yaml_format_instructions(model_cls) -> str:
    """Build YAML format instructions from a Pydantic model's field descriptions."""
    import yaml
    fields = model_cls.model_fields
    example = {}
    for name, field in fields.items():
        desc = field.description or name
        if field.annotation is not None and hasattr(field.annotation, '__origin__'):
            # It's a list type
            example[name] = [f"<{desc} item>"]
        else:
            example[name] = f"<{desc}>"
    instructions = (
        "Respond ONLY with valid YAML that matches this structure (no markdown fences, no extra text):\n"
        + yaml.dump(example, default_flow_style=False).strip()
    )
    return instructions


def _parse_yaml_to_model(raw_text: str, model_cls):
    """Strip markdown fences and parse YAML text into a Pydantic model."""
    import yaml, re
    # Strip ```yaml ... ``` or ``` ... ``` fences if present
    clean = re.sub(r"^```[a-zA-Z]*\n?", "", raw_text.strip())
    clean = re.sub(r"\n?```$", "", clean.strip())
    data = yaml.safe_load(clean)
    if isinstance(data, dict):
        return model_cls(**data)
    raise ValueError(f"Expected a YAML mapping, got: {type(data)}")


def extract_structured_data_from_deck_text(full_deck_text: str, provider: str, model: str = None, **kwargs):
    """
    Extracts structured data (company name, industry, stage, USP, etc.) from the pitch deck text using an LLM
    and Pydantic for robust parsing.

    Strategy:
      1. For capable providers (OpenAI, Anthropic, Google, Groq) try native
         `with_structured_output` — zero-shot reliable JSON/tool-calling.
      2. Fallback for all others (Ollama, OpenRouter, …): ask the LLM to emit
         plain YAML (easier for small models than JSON), then parse with pyyaml.

    Args:
        full_deck_text (str): The full extracted text from the pitch deck.
        provider (str): The LLM provider to use.
        model (str, optional): The specific model name. Defaults to provider's default.
        **kwargs: Additional keyword arguments to pass to the LLM.

    Returns:
        StartupProfile | None: Parsed Pydantic object, or None if parsing fails.
    """
    from langchain_core.prompts import PromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from .llm_interface import get_llm

    # Low temperature for deterministic structured extraction
    llm_params = {"temperature": kwargs.get("temperature", 0.1)}
    llm_params.update(kwargs)

    llm = get_llm(provider_name=provider, model_name=model, **llm_params)
    if not llm:
        print(f"Failed to initialize LLM for {provider}")
        return None

    prompt_variables = {"full_deck_text": full_deck_text}

    # --- Strategy 1: Native structured output (tool-calling / JSON mode) ---
    if provider.lower() in ["openai", "anthropic", "google", "groq"]:
        try:
            structured_llm = llm.with_structured_output(StartupProfile)
            prompt = PromptTemplate.from_template(
                pitch_deck_advisor_prompts.PROMPT_EXTRACT_STRUCTURED_DATA
            )
            result = (prompt | structured_llm).invoke(prompt_variables)
            return result.model_dump() if result else None
        except Exception as e:
            print(f"Native structured output failed for {provider}, falling back to YAML: {e}")

    # --- Strategy 2: YAML fallback (works with any model that can output text) ---
    yaml_instructions = _yaml_format_instructions(StartupProfile)
    prompt_with_yaml = (
        pitch_deck_advisor_prompts.PROMPT_EXTRACT_STRUCTURED_DATA
        + "\n\n"
        + yaml_instructions
    )
    prompt = PromptTemplate.from_template(prompt_with_yaml)
    chain = prompt | llm | StrOutputParser()

    try:
        raw_text = chain.invoke(prompt_variables)
        parsed_model = _parse_yaml_to_model(raw_text, StartupProfile)
        return parsed_model.model_dump() if parsed_model else None
    except Exception as e:
        print(f"Error parsing YAML fallback output: {e}")
        return None
