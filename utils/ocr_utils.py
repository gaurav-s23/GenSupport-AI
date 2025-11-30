import easyocr
import os


# Initialize EasyOCR only once (performance boost)
reader = easyocr.Reader(['en'], gpu=False)  # If GPU available then gpu=True


def extract_text_from_image(image_path: str) -> str:
    """
    Use EasyOCR to extract text from an image or screenshot.
    """
    if not os.path.isfile(image_path):
        raise FileNotFoundError(f"[OCR ERROR] Image not found: {image_path}")

    try:
        result = reader.readtext(image_path, detail=0)  # detail=0 returns only text
        text_output = " ".join(result).strip()

        if not text_output:
            return "[No readable text found in the image]"

        return text_output

    except Exception as e:
        return f"[OCR Failed] Error: {e}"
