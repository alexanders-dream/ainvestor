import pytest
from unittest.mock import patch, MagicMock

# Import functions to test from core module
# Assuming core modules are in PYTHONPATH or using relative imports if tests are run as a package
# For simplicity, if running pytest from the project root, `core.` should work.
from core import pitch_deck_logic
from prompts import pitch_deck_advisor_prompts

# Mock data for testing
# Updated to reflect that PROMPT_OVERALL_FEEDBACK now expects 'full_deck_text'
# which comes from 'raw_full_text' in the data passed to get_deck_feedback_from_llm
mock_extracted_data_full = {
    'raw_full_text': "The problem is significant. Our solution is innovative. The product has features A, B, C. The market is large and growing. We use a subscription model. Our team is experienced. We project $1M ARR in 3 years. We are seeking $500k."
    # Other keys like 'problem', 'solution' might still be present from parsing
    # but are not directly used by the current PROMPT_OVERALL_FEEDBACK template.
}

mock_extracted_data_partial = {
    'raw_full_text': "Only the problem is defined. Other sections are missing or very brief."
}

@patch('core.pitch_deck_logic.get_llm_response')
def test_get_deck_feedback_from_llm_success(mock_get_llm_response):
    """Test successful feedback generation."""
    mock_llm_feedback = "This is great feedback from the LLM."
    mock_get_llm_response.return_value = mock_llm_feedback

    feedback = pitch_deck_logic.get_deck_feedback_from_llm(
        extracted_sections_data=mock_extracted_data_full,
        provider="openai",
        model="gpt-3.5-turbo"
    )

    assert feedback == mock_llm_feedback
    mock_get_llm_response.assert_called_once_with(
        prompt_template_str=pitch_deck_advisor_prompts.PROMPT_OVERALL_FEEDBACK,
        input_variables={
            "full_deck_text": mock_extracted_data_full['raw_full_text']
        },
        llm_provider="openai",
        llm_model="gpt-3.5-turbo"
    )

@patch('core.pitch_deck_logic.get_llm_response')
def test_get_deck_feedback_from_llm_partial_data(mock_get_llm_response):
    """Test feedback generation with partial data (empty strings for missing sections)."""
    mock_llm_feedback = "Feedback on partially filled deck."
    mock_get_llm_response.return_value = mock_llm_feedback

    feedback = pitch_deck_logic.get_deck_feedback_from_llm(
        extracted_sections_data=mock_extracted_data_partial, # Uses the one with empty strings
        provider="anthropic",
        model="claude-3-haiku"
    )
    assert feedback == mock_llm_feedback
    mock_get_llm_response.assert_called_once_with(
        prompt_template_str=pitch_deck_advisor_prompts.PROMPT_OVERALL_FEEDBACK,
        input_variables={
            "full_deck_text": mock_extracted_data_partial['raw_full_text']
        },
        llm_provider="anthropic",
        llm_model="claude-3-haiku"
    )


@patch('core.pitch_deck_logic.get_llm_response')
def test_get_section_refinement_from_llm_success(mock_get_llm_response):
    """Test successful section refinement."""
    mock_refined_text = "This section is now much clearer."
    mock_get_llm_response.return_value = mock_refined_text

    section_name = "Problem Statement"
    section_text = "The problem is very complex and hard to understand for users."
    startup_usp = "We simplify complexity."

    refined_text = pitch_deck_logic.get_section_refinement_from_llm(
        section_name=section_name,
        section_text=section_text,
        startup_usp=startup_usp,
        provider="openai",
        model="gpt-4"
    )

    assert refined_text == mock_refined_text
    mock_get_llm_response.assert_called_once_with(
        prompt_template_str=pitch_deck_advisor_prompts.get_messaging_refinement_prompt_template(),
        input_variables={
            "section_name": section_name,
            "section_text": section_text,
            "startup_usp": startup_usp
        },
        llm_provider="openai",
        llm_model="gpt-4"
    )

# To run these tests:
# 1. Ensure pytest and unittest.mock are installed (pip install pytest mock)
# 2. Navigate to the root directory of the project in your terminal.
# 3. Run the command: pytest
#
# If core modules are not found, you might need to adjust PYTHONPATH or run pytest with specific options:
# Example: python -m pytest
# Or ensure your project structure allows for direct imports (e.g. by having an __init__.py in the root
# and installing the project in editable mode: pip install -e .)

@patch('core.pitch_deck_logic.get_llm_response')
def test_extract_structured_data_from_deck_text_success(mock_get_llm_response):
    """Test successful structured data extraction using Pydantic."""
    # Mock LLM response as a JSON string, which the Pydantic parser often expects/handles
    mock_json_response = '''
    {
        "company_name": "TechStartup",
        "industry_sector": "AI",
        "current_stage": "Seed",
        "funding_ask_amount": "$1M",
        "usp": "Revolutionary AI",
        "keywords_for_investor_search": ["AI", "Tech", "Seed"]
    }
    '''
    mock_get_llm_response.return_value = mock_json_response

    full_deck_text = "We are TechStartup. We do AI."
    
    extracted_data = pitch_deck_logic.extract_structured_data_from_deck_text(
        full_deck_text=full_deck_text,
        provider="openai",
        model="gpt-3.5-turbo"
    )

    assert extracted_data is not None
    assert extracted_data['company_name'] == "TechStartup"
    assert extracted_data['industry_sector'] == "AI"
    assert "AI" in extracted_data['keywords_for_investor_search']

@patch('core.pitch_deck_logic.get_llm_response')
def test_extract_structured_data_from_deck_text_failure(mock_get_llm_response):
    """Test extraction failure with invalid JSON."""
    mock_get_llm_response.return_value = "Not a valid JSON"

    extracted_data = pitch_deck_logic.extract_structured_data_from_deck_text(
        full_deck_text="Some text",
        provider="openai"
    )

    # Depending on how parser handles it, it might raise or return None if we catch it.
    # In implementation we catch exceptions and return None.
    assert extracted_data is None
