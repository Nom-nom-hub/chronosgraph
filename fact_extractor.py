import json
from typing import Any, Dict, List, Optional
from openai import OpenAI
from .exceptions import FactExtractionError
from .logger import logger

class FactExtractor:
    """
    Uses an LLM to automatically extract entities and relationships from agent episodes.
    This turns raw text into a structured knowledge graph.
    """
    def __init__(self, openai_client: Optional[OpenAI] = None):
        self.client = openai_client or OpenAI()

    def extract_facts(self, text: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Extracts entities and their relationships from the given text.
        """
        prompt = f"""
        Analyze the following agent experience and extract key entities and their relationships.
        
        Text: "{text}"
        
        Return the result in strict JSON format with two keys:
        1. "entities": A list of objects with "name", "type" (e.g., person, place, concept, object), and "description".
        2. "relationships": A list of objects with "source" (entity name), "target" (entity name), "type" (the relationship), and "strength" (0.0 to 1.0).
        
        Example Output:
        {{
            "entities": [
                {{"name": "ChronosGraph", "type": "software", "description": "A memory database for AI agents."}}
            ],
            "relationships": [
                {{"source": "Agent", "target": "ChronosGraph", "type": "DEVELOPED", "strength": 1.0}}
            ]
        }}
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a knowledge graph extractor. Return only JSON."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )
            
            if not response or not response.choices:
                return {"entities": [], "relationships": []}
            content = response.choices[0].message.content
            return json.loads(content)
        except Exception as e:
            logger.error(f"Error during fact extraction: {e}", extra={"error_type": "FactExtractionError", "text_length": len(text)})
            raise FactExtractionError(f"Failed to extract facts: {e}") from e
