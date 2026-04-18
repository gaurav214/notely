"""
OCR Module: Extract text from images using OCR.space API
Free and reliable cloud-based OCR service
"""

import requests
import os
from typing import Optional
from pathlib import Path


def get_ocr_space_key() -> Optional[str]:
    """
    Get OCR.space API key from environment.
    Note: OCR.space has a free tier without API key (limited requests).

    Returns:
        API key or None for free tier
    """
    return os.getenv("OCR_SPACE_API_KEY")


def extract_text_from_image(image_path: str, preprocess: bool = True) -> dict:
    """
    Extract text from image using OCR.space API.

    Args:
        image_path: Path to the image file
        preprocess: Ignored (kept for compatibility)

    Returns:
        Dictionary with raw text and metadata
    """
    try:
        # Read image file
        with open(image_path, "rb") as image_file:
            image_data = image_file.read()

        # Get API key if available
        api_key = get_ocr_space_key()

        # Prepare request
        url = "https://api.ocr.space/parse/image"

        payload = {
            "isOverlayRequired": False,
            "apikey": api_key if api_key else "K87899142591",  # Free tier key
            "language": "eng"
        }

        files = {
            "filename": (Path(image_path).name, image_data)
        }

        print("[INFO] Sending image to OCR.space API...")
        response = requests.post(url, data=payload, files=files, timeout=60)

        if response.status_code != 200:
            error_msg = f"OCR.space API returned status {response.status_code}"
            print(f"ERROR: {error_msg}")
            return {
                "success": False,
                "raw_text": "",
                "error": error_msg
            }

        result = response.json()

        # Check if request was successful
        if not result.get("IsErroredOnProcessing", False) == False:
            error_msg = result.get("ErrorMessage", "Unknown OCR error")
            print(f"ERROR: {error_msg}")
            return {
                "success": False,
                "raw_text": "",
                "error": f"OCR processing failed: {error_msg}"
            }

        # Extract text
        raw_text = result.get("ParsedText", "").strip()

        if not raw_text:
            return {
                "success": False,
                "raw_text": "",
                "error": "No text detected in image. Try a clearer photo of the blackboard."
            }

        print(f"[OK] Extracted {len(raw_text)} characters from image")

        return {
            "success": True,
            "raw_text": raw_text
        }

    except requests.exceptions.Timeout:
        error_msg = "OCR.space API request timed out (took more than 60 seconds)"
        print(f"ERROR: {error_msg}")
        return {
            "success": False,
            "raw_text": "",
            "error": error_msg
        }
    except requests.exceptions.ConnectionError as e:
        error_msg = "Could not connect to OCR.space API. Check your internet connection."
        print(f"ERROR: {error_msg}")
        return {
            "success": False,
            "raw_text": "",
            "error": error_msg
        }
    except Exception as e:
        error_msg = f"OCR extraction failed: {str(e)}"
        print(f"ERROR: {error_msg}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "raw_text": "",
            "error": error_msg
        }
