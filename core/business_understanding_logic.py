# core/business_understanding_logic.py

import json # Still used for logging and formatting parts of prompts
import yaml # For dumping current assumptions to YAML for the prompt
from typing import Dict, Any, Optional, List

from core.llm_interface import LLMInterface
from prompts.business_understanding_prompts import (
    PITCH_DECK_EXTRACTION_PROMPT,
    CLARIFICATION_PROMPT_TEMPLATE,
    UPDATE_ASSUMPTIONS_PROMPT_TEMPLATE,
)
# from core.utils import extract_json_from_response # No longer needed for this file
from core.yaml_utils import extract_yaml_from_text, load_yaml # Import YAML utilities

class BusinessUnderstandingLogic:
    """
    Handles the AI-driven logic for understanding and contextualizing
    a user's business for financial modeling.
    """

    def __init__(self, llm_interface: LLMInterface):
        self.llm = llm_interface
        self.conversation_history: List[Dict[str, str]] = []

    def extract_from_pitch_deck(self, pitch_deck_text: str) -> Optional[Dict[str, Any]]:
        """
        Uses an LLM to extract foundational business information from pitch deck text.

        Args:
            pitch_deck_text: The text content of the user's pitch deck.

        Returns:
            A dictionary containing extracted business information, or None if extraction fails.
        """
        if not pitch_deck_text:
            return None

        response_text = self.llm.generate_text(
            PITCH_DECK_EXTRACTION_PROMPT,
            max_tokens=1000,
            pitch_deck_text=pitch_deck_text
        )

        if response_text:
            yaml_content = extract_yaml_from_text(response_text)
            if yaml_content:
                extracted_data = load_yaml(yaml_content)
                if isinstance(extracted_data, dict):
                    # Initialize conversation history for this session
                    self.conversation_history = [
                        {"role": "system", "content": "Initial business information extracted from pitch deck."},
                        # Log the structured data as JSON for readability in logs, or use yaml.dump
                        {"role": "assistant", "content": f"Extracted data: {json.dumps(extracted_data)}"}
                    ]
                    return extracted_data
                else:
                    print(f"Warning: Could not parse YAML from LLM response in extract_from_pitch_deck. Raw YAML content: {yaml_content[:200]}")
            else:
                print(f"Warning: Could not extract YAML from LLM response in extract_from_pitch_deck. Raw response: {response_text[:200]}")
        return None

    def initialize_assumptions_from_structured_data(self, structured_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Initializes business assumptions directly from a pre-extracted structured dictionary.

        Args:
            structured_data: A dictionary containing pre-extracted business information.

        Returns:
            The structured_data itself, or None if input is invalid.
        """
        if not structured_data or not isinstance(structured_data, dict):
            return None

        # Initialize conversation history for this session, noting data was pre-loaded
        self.conversation_history = [
            {"role": "system", "content": "Initial business information loaded from pre-extracted structured data from pitch deck analysis."},
            {"role": "assistant", "content": f"Loaded structured data: {json.dumps(structured_data)}"}
        ]
        # The structured_data is considered the initial set of business_assumptions
        return structured_data

    def get_clarification_question(self, extracted_data: Dict[str, Any]) -> Optional[str]:
        """
        Generates a clarifying question if the extracted data is incomplete or vague.

        Args:
            extracted_data: The currently understood business assumptions.

        Returns:
            A string containing a question for the user, or None if no clarification is needed
            or if an error occurs.
        """
        history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.conversation_history])
        question = self.llm.generate_text(
            CLARIFICATION_PROMPT_TEMPLATE,
            max_tokens=200,
            extracted_data=json.dumps(extracted_data, indent=2),
            conversation_history=history_str
        )
        if question:
            # Add AI's question to history
            self.conversation_history.append({"role": "assistant", "content": question.strip()})
            return question.strip()
        return None

    def update_assumptions_with_user_response(
        self,
        current_assumptions: Dict[str, Any],
        user_response: str
    ) -> Optional[Dict[str, Any]]:
        """
        Updates business assumptions based on the user's response to a clarification question.

        Args:
            current_assumptions: The existing dictionary of business assumptions.
            user_response: The user's textual response to the AI's question.

        Returns:
            An updated dictionary of business assumptions, or None if update fails.
        """
        if not user_response:
            return current_assumptions

        # Add user's response to history
        self.conversation_history.append({"role": "user", "content": user_response})

        response_text = self.llm.generate_text(
            UPDATE_ASSUMPTIONS_PROMPT_TEMPLATE,
            max_tokens=1000,
            current_assumptions_yaml=yaml.dump(current_assumptions, allow_unicode=True, default_flow_style=False, sort_keys=False),
            user_response=user_response
        )

        if response_text:
            yaml_content = extract_yaml_from_text(response_text)
            if yaml_content:
                updated_data = load_yaml(yaml_content)
                if isinstance(updated_data, dict):
                    # Add AI's understanding of updated assumptions to history
                    self.conversation_history.append(
                        {"role": "assistant", "content": f"Updated assumptions: {json.dumps(updated_data)}"} # Log as JSON for readability
                    )
                    return updated_data
                else:
                    print(f"Warning: Could not parse YAML from LLM response in update_assumptions_with_user_response. Raw YAML content: {yaml_content[:200]}")
            else:
                print(f"Warning: Could not extract YAML from LLM response in update_assumptions_with_user_response. Raw response: {response_text[:200]}")
        return None

    def get_full_conversation_history(self) -> List[Dict[str, str]]:
        """Returns the full conversation history."""
        return self.conversation_history

    def reset_conversation(self):
        """Resets the conversation history."""
        self.conversation_history = []

# Example Usage (for testing purposes, typically this would be integrated into Streamlit pages)
if __name__ == "__main__":
    # This requires OPENAI_API_KEY to be set in the environment
    try:
        llm_api = LLMInterface() # Assumes default provider (e.g., OpenAI)
    except Exception as e:
        print(f"Failed to initialize LLMInterface: {e}")
        print("Please ensure your LLM provider (e.g., OpenAI) API key is set.")
        llm_api = None

    if llm_api:
        bu_logic = BusinessUnderstandingLogic(llm_interface=llm_api)

        sample_pitch_deck = """
        **Our Company: Innovatech Solutions**

        **Problem:** Businesses struggle with inefficient data management and outdated analytics tools,
        leading to missed opportunities and poor decision-making.

        **Solution:** Innovatech offers a cutting-edge, AI-powered SaaS platform that centralizes
        data, provides real-time analytics, and generates actionable insights. Our platform is
        user-friendly and integrates seamlessly with existing enterprise systems.

        **Business Model:** We operate on a tiered subscription model (Basic, Pro, Enterprise)
        based on features and usage volume. We also offer premium support and custom
        integration services for larger clients.

        **Revenue Streams:**
        1. Monthly/Annual SaaS Subscriptions.
        2. Fees for custom development and integration.
        3. Premium support packages.

        **Target Market:** Medium to large enterprises across various sectors, particularly
        those in finance, healthcare, and retail who are looking to modernize their
        data infrastructure.

        **Cost Structure:** Major costs include R&D for platform development, cloud hosting
        (AWS), sales and marketing, and customer support personnel.

        **Team:** Led by Jane Doe (CEO, ex-Google) and John Smith (CTO, PhD in AI).
        """

        print("1. Extracting from Pitch Deck...")
        extracted_info = bu_logic.extract_from_pitch_deck(sample_pitch_deck)
        if extracted_info:
            print("   Extracted Info:", json.dumps(extracted_info, indent=2))

            print("\n2. Getting Clarification Question (if needed)...")
            # Simulate a scenario where more detail is needed, e.g., on competitive advantage
            # For this test, we'll assume the LLM might ask about it.
            # In a real scenario, the LLM decides based on the PITCH_DECK_EXTRACTION_PROMPT's optional fields.
            extracted_info["competitive_advantage"] = None # Simulate it wasn't found or is vague
            question = bu_logic.get_clarification_question(extracted_info)
            if question:
                print("   AI Question:", question)

                user_ans = input("   Your Answer: ")
                if user_ans:
                    print("\n3. Updating Assumptions with User Response...")
                    updated_assumptions = bu_logic.update_assumptions_with_user_response(
                        extracted_info,
                        user_ans
                    )
                    if updated_assumptions:
                        print("   Updated Assumptions:", json.dumps(updated_assumptions, indent=2))
                    else:
                        print("   Failed to update assumptions.")
            else:
                print("   No clarification question generated (or LLM error).")
        else:
            print("   Failed to extract info from pitch deck.")

        print("\nFull Conversation History:")
        for entry in bu_logic.get_full_conversation_history():
            print(f"- {entry['role']}: {entry['content']}")
    else:
        print("Skipping BusinessUnderstandingLogic example usage as LLMInterface failed to initialize.")
