import os
from utils.logger import logger

class DocumentValidator:
    @staticmethod
    def validate_file_exists_and_not_empty(file_path: str) -> bool:
        """Validates that a file at the specified path exists and is not empty (size > 0)."""
        if not os.path.exists(file_path):
            logger.error(f"Validation failed: File {file_path} does not exist.")
            return False
            
        file_size = os.path.getsize(file_path)
        if file_size == 0:
            logger.error(f"Validation failed: File {file_path} is empty (0 bytes).")
            return False
            
        logger.info(f"Validation succeeded: File {file_path} exists and is {file_size} bytes.")
        return True

    @staticmethod
    def validate_document_structure(content_data: dict, required_sections: list) -> list:
        """Checks if all required sections are present in the generated content dictionary."""
        missing = []
        for section in required_sections:
            if section not in content_data or not content_data[section]:
                missing.append(section)
        return missing
