"""
Utility functions for YAML parsing and generation.
This module provides a consistent interface for handling YAML data throughout the application.
"""

import yaml
import streamlit as st
from typing import Any, Dict, List, Union, Optional
from io import StringIO, BytesIO

def load_yaml(yaml_str: str) -> Union[Dict, List, None]:
    """
    Parse a YAML string into a Python object.

    Args:
        yaml_str (str): The YAML string to parse.

    Returns:
        Union[Dict, List, None]: The parsed YAML data as Python objects, or None if parsing fails.
    """
    try:
        return yaml.safe_load(yaml_str)
    except yaml.YAMLError as e:
        st.error(f"Error parsing YAML: {e}")
        return None

def dump_yaml(data: Any) -> str:
    """
    Convert a Python object to a YAML string.

    Args:
        data (Any): The Python object to convert to YAML.

    Returns:
        str: The YAML string representation of the data.
    """
    try:
        return yaml.dump(data, default_flow_style=False, sort_keys=False)
    except Exception as e:
        st.error(f"Error converting to YAML: {e}")
        return ""

def extract_yaml_from_text(text: str) -> Optional[str]:
    """
    Extract YAML content from text that might contain other content.
    Useful for extracting YAML from LLM responses.

    Args:
        text (str): The text that might contain YAML.

    Returns:
        Optional[str]: The extracted YAML string, or None if no YAML is found.
    """
    if not text:
        return None

    # Handle markdown code blocks (most common case)
    if "```yaml" in text or "```yml" in text:
        # Extract content between ```yaml and ```
        start_marker = "```yaml" if "```yaml" in text else "```yml"
        parts = text.split(start_marker, 1)
        if len(parts) > 1:
            yaml_part = parts[1].split("```", 1)[0].strip()
            # Validate that it's actually YAML
            try:
                if yaml.safe_load(yaml_part):
                    return yaml_part
            except yaml.YAMLError:
                # If parsing fails, continue to other methods
                pass

    # Handle generic code blocks that might contain YAML
    if "```" in text:
        parts = text.split("```", 1)
        if len(parts) > 1:
            code_part = parts[1].split("```", 1)[0].strip()
            # Check if this looks like YAML
            if ":" in code_part and ("-" in code_part or "{" in code_part or "}" in code_part):
                try:
                    if yaml.safe_load(code_part):
                        return code_part
                except yaml.YAMLError:
                    # If parsing fails, continue to other methods
                    pass

    # If no markdown code blocks, try to find YAML-like content
    if ":" in text and ("-" in text or "{" in text or "}" in text):
        # Try to find the start of what looks like YAML
        lines = text.split("\n")
        start_idx = 0
        for i, line in enumerate(lines):
            line = line.strip()
            if line and (":" in line or line.startswith("-")):
                start_idx = i
                break

        # Try to find the end of what looks like YAML
        end_idx = len(lines)
        for i in range(len(lines) - 1, start_idx, -1):
            line = lines[i].strip()
            if line and not line.startswith("#") and (":" in line or line.startswith("-")):
                end_idx = i + 1
                break

        yaml_content = "\n".join(lines[start_idx:end_idx])

        # Validate that it's actually YAML
        try:
            if yaml.safe_load(yaml_content):
                return yaml_content
        except yaml.YAMLError:
            # If parsing fails, try one more approach
            pass

    # Last resort: try to parse the entire text as YAML
    try:
        if yaml.safe_load(text):
            return text
    except yaml.YAMLError:
        pass

    # If all attempts fail, return None
    return None

def create_default_investor_yaml() -> str:
    """
    Create a default YAML structure for investor data.
    Useful as a fallback when parsing fails.

    Args:
        url (str, optional): The source URL to include in the data.

    Returns:
        str: A YAML string with default investor data.
    """
    default_data = {
        "extracted_profiles": [
            {
                "name": "Parsing Error",
                "description": "Failed to parse YAML from LLM response",
                "investor_type": "Unknown",
                "industry_focus": [],
                "stage_focus": [],
                "geographical_focus": [],
                "contact_email": "",
                "website_url": "",
                "key_people": [],
                "portfolio_examples": [],
                "notes": "This is a placeholder due to YAML parsing error."
            }
        ]
    }
    return dump_yaml(default_data)

def create_investor_strategy_template() -> str:
    """
    Create a template YAML structure for investor search strategy.
    This can be used to generate a downloadable template file.

    Returns:
        str: A YAML string with the template structure.
    """
    template_data = {
        "startup_profile": {
            "industry": "Technology",
            "stage": "Seed",
            "funding_needed": "$500k - $2M",
            "usp": "Our AI-powered platform helps businesses reduce customer churn by 30% through predictive analytics."
        },
        "market_trends": "AI analytics adoption, SaaS growth, focus on customer retention metrics",
        "investor_preferences": "Focus on impact investors, exclude VCs from region X"
    }
    return dump_yaml(template_data)

def parse_uploaded_yaml_file(uploaded_file: st.runtime.uploaded_file_manager.UploadedFile) -> Union[Dict, None]:
    """
    Parse an uploaded YAML file and extract its contents.

    Args:
        uploaded_file: The file object from st.file_uploader.

    Returns:
        Union[Dict, None]: The parsed YAML data as a Python dictionary, or None if parsing fails.
    """
    try:
        # Get the file content as a string
        file_content = uploaded_file.getvalue().decode('utf-8')

        # Parse the YAML content
        yaml_data = load_yaml(file_content)

        return yaml_data
    except Exception as e:
        st.error(f"Error parsing uploaded YAML file: {e}")
        return None

def save_assumptions_yaml(assumptions_dict: Dict[str, Any], file_path: str) -> bool:
    """
    Saves a dictionary of financial assumptions to a YAML file.

    Args:
        assumptions_dict (Dict[str, Any]): The dictionary of assumptions to save.
        file_path (str): The path to save the YAML file to.

    Returns:
        bool: True if saving was successful, False otherwise.
    """
    try:
        yaml_string = dump_yaml(assumptions_dict)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(yaml_string)
        return True
    except Exception as e:
        st.error(f"Error saving assumptions to YAML file {file_path}: {e}")
        return False

def load_assumptions_yaml(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Loads a dictionary of financial assumptions from a YAML file.

    Args:
        file_path (str): The path to the YAML file to load.

    Returns:
        Optional[Dict[str, Any]]: The loaded dictionary of assumptions, or None if loading fails.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            yaml_content = f.read()
        
        if not yaml_content.strip():
            st.warning(f"Assumption file {file_path} is empty.")
            return None # Or an empty dict {} depending on desired behavior

        assumptions_dict = load_yaml(yaml_content)
        if not isinstance(assumptions_dict, dict):
            st.error(f"Content of {file_path} is not a valid assumptions dictionary (expected dict, got {type(assumptions_dict)}).")
            return None
        return assumptions_dict
    except FileNotFoundError:
        st.error(f"Assumptions file not found: {file_path}")
        return None
    except Exception as e:
        st.error(f"Error loading assumptions from YAML file {file_path}: {e}")
        return None
