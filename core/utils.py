import streamlit as st
from io import BytesIO
# For PDF parsing
from PyPDF2 import PdfReader # Example, or use pdfminer.six for more robust extraction
# For PPTX parsing
from pptx import Presentation # Example

# --- FILE PARSING UTILITIES ---

def parse_pitch_deck(uploaded_file: st.runtime.uploaded_file_manager.UploadedFile):
    """
    Parses an uploaded pitch deck file (PDF or PPTX) and extracts text content.
    This is a placeholder and needs actual implementation of PDF/PPTX parsing.

    Args:
        uploaded_file: The file object from st.file_uploader.

    Returns:
        dict: A dictionary where keys are slide numbers or section titles (simplified)
              and values are the extracted text from those parts.
              Returns a simple structure with 'full_text' for now.
    Raises:
        ValueError: If the file type is not supported.
    """
    file_name = uploaded_file.name
    file_bytes = uploaded_file.getvalue() # Get bytes for processing

    extracted_data = {"file_name": file_name, "slides": {}} # Placeholder for structured data
    full_text_content = ""

    if file_name.lower().endswith(".pdf"):
        full_text_content = extract_text_from_pdf(BytesIO(file_bytes))
    elif file_name.lower().endswith(".pptx"):
        full_text_content = extract_text_from_pptx(BytesIO(file_bytes))
    else:
        raise ValueError("Unsupported file type. Please upload a PDF or PPTX file.")

    # For now, we return the full text. Section identification is a future enhancement.
    simple_sections = {
        'problem': "Section-specific extraction for 'Problem' not yet implemented. See full text.",
        'solution': "Section-specific extraction for 'Solution' not yet implemented. See full text.",
        'product': "Section-specific extraction for 'Product' not yet implemented. See full text.",
        'market': "Section-specific extraction for 'Market' not yet implemented. See full text.",
        'business_model': "Section-specific extraction for 'Business Model' not yet implemented. See full text.",
        'team': "Section-specific extraction for 'Team' not yet implemented. See full text.",
        'financials': "Section-specific extraction for 'Financials' not yet implemented. See full text.",
        'ask': "Section-specific extraction for 'Ask' not yet implemented. See full text.",
        'raw_full_text': full_text_content
    }
    return simple_sections


# Actual PDF text extraction
def extract_text_from_pdf(pdf_file_obj: BytesIO) -> str:
    """Extracts all text from a PDF file."""
    text = ""
    try:
        reader = PdfReader(pdf_file_obj)
        for page_num, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += f"--- Page {page_num + 1} ---\n{page_text}\n\n"
        if not text:
            return "No text could be extracted from the PDF. It might be image-based or scanned."
        return text
    except Exception as e:
        st.error(f"Error parsing PDF: {e}")
        # Return a more informative error or raise it
        return f"Error parsing PDF: {e}. The file might be corrupted or password-protected."


# Actual PPTX text extraction
def extract_text_from_pptx(pptx_file_obj: BytesIO) -> str:
    """Extracts all text from a PPTX file."""
    text = ""
    try:
        prs = Presentation(pptx_file_obj)
        for i, slide in enumerate(prs.slides):
            slide_text_parts = []
            for shape in slide.shapes:
                if hasattr(shape, "text_frame") and shape.text_frame and shape.text_frame.text:
                    slide_text_parts.append(shape.text_frame.text)
                elif hasattr(shape, "text") and shape.text: # For shapes with direct text attribute
                    slide_text_parts.append(shape.text)
            
            if slide_text_parts: # Only add slide header if there's text
                 text += f"--- Slide {i+1} ---\n"
                 text += "\n".join(slide_text_parts) + "\n\n"

        if not text:
            return "No text could be extracted from the PPTX. Slides might be empty or contain only images."
        return text
    except Exception as e:
        st.error(f"Error parsing PPTX: {e}")
        return f"Error parsing PPTX: {e}. The file might be corrupted."


# --- OTHER UTILITY FUNCTIONS ---

def format_currency(value, currency_symbol="$", decimals=0):
    """Formats a number as currency."""
    if decimals == 0:
        return f"{currency_symbol}{value:,.0f}"
    else:
        return f"{currency_symbol}{value:,.{decimals}f}"

# Add any other common utility functions here as the project grows.
# For example, data validation, specific string manipulations, etc.

def styled_card(title, content, icon=None, title_tag="h3"):
    """
    Displays content in a styled card with an optional icon and customizable title tag.

    Args:
        title (str): The title of the card.
        content (str): The HTML content to display within the card.
        icon (str, optional): An emoji or short icon string to prepend to the title. Defaults to None.
        title_tag (str, optional): The HTML tag to use for the title (e.g., "h3", "h4"). Defaults to "h3".
    """
    import streamlit as st # Ensure streamlit is imported locally for this function
    
    icon_html = f'<span style="margin-right: 10px;">{icon}</span>' if icon else ""
    
    card_html = f"""
    <div style="border: 1px solid #e0e0e0; 
                border-radius: 8px; 
                padding: 20px; 
                margin-bottom: 20px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                background-color: #ffffff;">
        <{title_tag} style="margin-top: 0; margin-bottom: 15px; color: #333; display: flex; align-items: center;">
            {icon_html}{title}
        </{title_tag}>
        <div style="color: #555; line-height: 1.6;">
            {content}
        </div>
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)

if __name__ == "__main__":
    # Test functions if needed
    # print(format_currency(1234567.89, decimals=2)) # $1,234,567.89
    # print(format_currency(50000)) # $50,000
    
    # To test file parsing, you'd need sample files and uncomment the actual
    # parsing libraries and functions.
    # For now, this module mainly contains placeholders for file parsing.
    st.write("Utils module loaded. Contains placeholders for file parsing.")
    st.write("Run Streamlit pages to test integration of these utils.")
