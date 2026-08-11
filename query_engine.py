import json
from typing import Any, Dict, List, Optional
from openai import OpenAI
from .logger import logger

class QueryEngine:
    """
    Advanced Natural-Language Query Engine for ChronosGraph.
    Translates natural language questions into structured graph and semantic queries.
    """
    def __init__(self, engine, openai_client: Optional[OpenAI] = None):
        self.engine = engine
        self.client = openai_client or OpenAI()
        self.model = "gpt-4o"

    def query(self, agent_id: str, nl_query: str) -> Dict[str, Any]:
        """
        Executes a natural language query against the agent's memory.
        """
        logger.info(f"Processing NL query for agent {agent_id}: {nl_query}", extra={"agent_id": agent_id})
        
        try:
            # 1. Parse the query using LLM
            plan = self._parse_query(nl_query)
            logger.debug(f"Query plan generated: {plan}", extra={"agent_id": agent_id, "plan": plan})
            
            results = {}
            
            # 2. Execute Semantic Search if needed
            if plan.get("semantic_search"):
                # We need embeddings for the query. 
                # For simplicity in this v1 implementation, we assume the SDK handles embedding generation.
                # Here we just flag that a semantic search was requested.
                results["semantic_search_required"] = True
                results["semantic_query"] = plan.get("semantic_query", nl_query)

            # 3. Execute Graph Traversal if needed
            if plan.get("graph_traversal"):
                entity_name = plan.get("target_entity")
                if entity_name:
                    try:
                        graph_context = self.engine.get_graph_context(agent_id, entity_name)
                        results["graph_context"] = graph_context
                    except Exception as e:
                        logger.warning(f"Graph traversal failed for {entity_name}: {e}")
                        results["graph_error"] = str(e)

            # 4. Execute Relational Queries (Episodes)
            if plan.get("episode_lookup"):
                limit = plan.get("limit", 5)
                episodes = self.engine.get_episodes(agent_id, limit=limit)
                results["recent_episodes"] = episodes

            results["plan"] = plan
            return results
        except Exception as e:
            logger.error(f"Query processing failed: {e}", extra={"agent_id": agent_id, "error_type": "QueryError"})
            raise e

    def _parse_query(self, nl_query: str) -> Dict[str, Any]:
        """
        Uses LLM to break down a NL query into structured components.
        """
        system_prompt = """
        You are the query parser for ChronosGraph, an agentic memory system.
        Translate the user's natural language query into a structured JSON plan.
        
        Available operations:
        - semantic_search: True if the query asks for concepts or vague memories.
        - graph_traversal: True if the query asks about a specific entity or relationship.
        - episode_lookup: True if the query asks for recent events or a timeline.
        
        Fields to extract:
        - semantic_query: The core concept to search for.
        - target_entity: The name of the specific entity to look up in the graph.
        - limit: Number of results to return (default 5).
        
        Example: "What do we know about the project Apollo?"
        Output: {"semantic_search": true, "graph_traversal": true, "target_entity": "Apollo", "semantic_query": "project Apollo"}
        """
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": nl_query}
            ],
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
