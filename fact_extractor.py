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
        Refined for higher accuracy and better deduplication.
        """
        prompt = f"""
        Analyze the following agent experience and extract key entities and their relationships for a knowledge graph.
        
        Text: "{text}"
        
        Instructions:
        1. Identify unique entities (people, places, objects, concepts, software, events).
        2. For each entity, provide a clear, concise name and a brief description.
        3. Identify relationships between these entities or between the "Agent" and these entities.
        4. Relationship types should be in UPPERCASE (e.g., LIKES, LOCATED_IN, DEVELOPED, MENTIONS).
        5. Assign a strength (0.0 to 1.0) based on how explicit the relationship is in the text.
        6. DEDUPLICATION: Use standard names for common entities. If an entity is referred to by multiple names, choose the most formal or descriptive one.
        
        Return the result in strict JSON format:
        {{
            "entities": [
                {{"name": "Entity Name", "type": "entity_type", "description": "Brief description"}}
            ],
            "relationships": [
                {{"source": "Entity A", "target": "Entity B", "type": "RELATIONSHIP_TYPE", "strength": 0.9}}
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
