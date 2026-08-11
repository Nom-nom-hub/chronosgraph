import json
from typing import Any, Dict, List, Optional
from openai import OpenAI
from .logger import logger
from .exceptions import FactExtractionError

class MemorySummarizer:
    """
    Uses an LLM to summarize a group of episodes into a concise memory summary.
    This helps in pruning context while retaining core information.
    """
    def __init__(self, openai_client: Optional[OpenAI] = None):
        self.client = openai_client or OpenAI()

    def summarize_episodes(self, episodes: List[Dict[str, Any]]) -> str:
        """
        Summarizes a list of episodes into a single descriptive paragraph.
        """
        if not episodes:
            return ""

        content_to_summarize = "\n".join([f"- {ep['content']}" for ep in episodes])
        
        prompt = f"""
        Summarize the following sequence of agent experiences into a single, concise, and informative paragraph.
        Focus on retaining key facts, decisions, and outcomes.
        
        Experiences:
        {content_to_summarize}
        
        Summary:
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are a memory summarization assistant. Provide concise and accurate summaries of events."},
                    {"role": "user", "content": prompt}
                ]
            )
            
            if not response or not response.choices:
                return ""
            
            summary = response.choices[0].message.content.strip()
            logger.info(f"Successfully summarized {len(episodes)} episodes.", extra={"episode_count": len(episodes)})
            return summary
        except Exception as e:
            logger.error(f"Error during memory summarization: {e}", extra={"error_type": "SummarizationError", "episode_count": len(episodes)})
            # Fallback to a simple concatenation if LLM fails
            return "Summary unavailable. " + content_to_summarize[:500] + "..."
