"""
LLM Module: Claude Haiku via Anthropic API
Simplified single-model system for text and vision processing
"""

import anthropic
import base64
import os
from typing import Optional


# Initialize Anthropic client
def get_client() -> anthropic.Anthropic:
    """Get Anthropic client with API key from environment."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable not set. Get free key from: https://console.anthropic.com/")
    return anthropic.Anthropic(api_key=api_key)


def extract_content_from_image(image_path: str) -> dict:
    """
    Use Claude Haiku's vision capabilities to extract content from an image.
    Works for diagrams, whiteboards, text, mixed content, etc.

    Args:
        image_path: Path to the image file

    Returns:
        Dictionary with extracted content
    """
    try:
        client = get_client()

        # Read and encode image
        with open(image_path, "rb") as image_file:
            image_data = base64.standard_b64encode(image_file.read()).decode("utf-8")

        # Determine image type from extension
        extension = image_path.lower().split('.')[-1]
        media_type_map = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'bmp': 'image/bmp',
            'gif': 'image/gif'
        }
        media_type = media_type_map.get(extension, 'image/jpeg')

        system_prompt = """You are an expert content analyzer. Your task is to carefully examine an image and extract ALL written content, diagrams, text, and information visible.

For each element, describe:
1. What text is written (exactly as shown)
2. Any diagrams, flowcharts, or visual structures
3. Layout and organization
4. Key points and relationships

Be thorough and preserve all information exactly as shown. Format the output in a clear, structured way."""

        user_message = "Please analyze this image and extract all content, text, diagrams, and information you can see. Be comprehensive and accurate."

        # Make request with vision
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            system=system_prompt,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": media_type,
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": user_message
                        }
                    ],
                }
            ],
        )

        extracted_content = response.content[0].text.strip()

        return {
            "success": True,
            "extracted_content": extracted_content,
            "error": None
        }

    except ValueError as e:
        return {
            "success": False,
            "error": f"Configuration error: {str(e)}",
            "extracted_content": None
        }
    except anthropic.APIConnectionError as e:
        return {
            "success": False,
            "error": f"API connection error: {str(e)}",
            "extracted_content": None
        }
    except anthropic.APIStatusError as e:
        return {
            "success": False,
            "error": f"Claude API error: {e.status_code} - {e.message}",
            "extracted_content": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error extracting from image: {str(e)}",
            "extracted_content": None
        }


def correct_ocr_text(raw_text: str) -> dict:
    """
    Use Claude Haiku to correct OCR errors in the extracted text.

    Args:
        raw_text: Raw text extracted from Tesseract OCR

    Returns:
        Dictionary with corrected text
    """
    try:
        client = get_client()

        system_prompt = """You are an OCR error correction specialist. Your job is to fix common OCR mistakes while preserving the original content and structure.

Common OCR errors to fix:
- '0' (zero) misread as 'O' (letter)
- '1' (one) misread as 'l' or 'I'
- '8' misread as 'B'
- '|' (pipe) misread as 'l' (letter)
- Mixed up similar letters
- Broken words that should be together
- Numbers/symbols misread as letters

Instructions:
1. Correct obvious OCR errors
2. Fix spacing and word breaks
3. Preserve formatting and structure
4. Keep the content exactly as written (don't add or remove information)
5. Only output the corrected text, no explanations

If you're uncertain about a correction, keep it as is."""

        user_message = f"Please correct the OCR errors in this text:\n\n{raw_text}"

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            temperature=0.3,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        corrected_text = response.content[0].text.strip()

        return {
            "success": True,
            "corrected_text": corrected_text,
            "error": None
        }

    except ValueError as e:
        return {
            "success": False,
            "error": f"Configuration error: {str(e)}",
            "corrected_text": raw_text
        }
    except anthropic.APIStatusError as e:
        return {
            "success": False,
            "error": f"Claude API error: {e.status_code} - {e.message}",
            "corrected_text": raw_text
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Error correcting text: {str(e)}",
            "corrected_text": raw_text
        }


def generate_notes_and_summary(raw_text: str) -> dict:
    """
    Use Claude Haiku to generate structured notes and summary from text.

    Args:
        raw_text: Raw text extracted from OCR (or corrected text)

    Returns:
        Dictionary with cleaned notes and summary
    """
    try:
        client = get_client()

        # Craft the prompt for Claude
        system_prompt = """You are an expert teacher and note-taker specializing in converting raw handwritten notes into structured, clear study materials.

Your task:
1. Organize content with clear headings and sections
2. Convert into bullet points where appropriate
3. Highlight key definitions, formulas, and important concepts
4. Provide brief explanations where content is unclear
5. Create a clean, professional study guide

Output format (use markdown):
# [Subject/Topic Title]

## Key Concepts
- [Key point 1]: [explanation]
- [Key point 2]: [explanation]

## Main Content
[Organized notes with headings and bullet points]

## Important Definitions
- [Term]: [Definition]

## Summary
[5-7 line concise summary of the entire topic]
"""

        user_message = f"Please process these blackboard notes and create structured study material:\n\n{raw_text}"

        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=2000,
            temperature=0.7,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )

        full_response = response.content[0].text

        # Extract summary (look for ## Summary section)
        lines = full_response.strip().split("\n")
        summary_start = -1
        for i, line in enumerate(lines):
            if "## Summary" in line or "**Summary**" in line:
                summary_start = i + 1
                break

        if summary_start > 0:
            summary = "\n".join(lines[summary_start:]).strip()
        else:
            # If no explicit summary section, take last 5-7 lines
            summary = "\n".join(lines[-7:]).strip()

        return {
            "success": True,
            "cleaned_notes": full_response,
            "summary": summary,
            "error": None
        }

    except ValueError as e:
        return {
            "success": False,
            "error": f"Configuration error: {str(e)}",
            "cleaned_notes": None,
            "summary": None
        }
    except anthropic.APIStatusError as e:
        return {
            "success": False,
            "error": f"Claude API error: {e.status_code} - {e.message}",
            "cleaned_notes": None,
            "summary": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "cleaned_notes": None,
            "summary": None
        }
