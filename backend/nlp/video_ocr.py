import os
import easyocr
import logging

logger = logging.getLogger(__name__)

class VideoOCREngine:
    """OCR Engine for extracting text from video screenshots."""
    
    def __init__(self):
        self.reader = None

    def _initialize_reader(self):
        if self.reader is None:
            # Initialize EasyOCR for English and Hindi (common for Indian context)
            logger.info("Initializing EasyOCR Model (this may take a moment)...")
            self.reader = easyocr.Reader(['en', 'hi'], gpu=False) # Change gpu=True if CUDA is available

    def extract_text_from_image(self, image_path: str) -> str:
        """Runs OCR on a screenshot and returns the combined text."""
        if not os.path.exists(image_path):
            logger.error(f"Screenshot file not found: {image_path}")
            return ""

        try:
            self._initialize_reader()
            results = self.reader.readtext(image_path)
            
            extracted_text = []
            for (bbox, text, prob) in results:
                if prob > 0.3: # Filter out low-confidence reads
                    extracted_text.append(text)
            
            full_text = " ".join(extracted_text)
            return full_text
            
        except Exception as e:
            logger.error(f"Error extracting text with OCR: {e}")
            return ""

# Singleton instance
video_ocr = VideoOCREngine()
