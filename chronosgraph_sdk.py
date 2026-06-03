from chronosgraph_engine import ChronosGraphEngine
from typing import List, Dict, Any, Optional
import numpy as np

class ChronosGraphSDK:
    """
    Universal SDK for AI agents to interact with ChronosGraph.
    This layer handles embedding generation (simulated for now) and high-level logic.
    """
    def __init__(self, db_path: str = "chronosgraph.db"):
        self.engine = ChronosGraphEngine(db_path)

    def _generate_embedding(self, text: str) -> List[float]:
        """
        Generates a semantic embedding for the given text.
        In a production environment, this would call an embedding model (e.g., OpenAI, HuggingFace).
        For Part 1, we use a deterministic dummy embedding.
        """
        # Simple deterministic hashing to create a consistent dummy vector
        np.random.seed(sum(ord(c) for c in text) % 10000)
        return np.random.rand(128).tolist()

    def initialize_agent(self, name: str, description: str = "") -> str:
        """Register a new agent and return its ID."""
        return self.engine.register_agent(name, description)

    def check_in(self, agent_id: str, episode_data: Dict[str, Any]) -> str:
        """
        Store a new episode of agent experience.
        Automatically handles embedding generation for content.
        """
        if 'content' in episode_data and 'embedding' not in episode_data:
            episode_data['embedding'] = self._generate_embedding(episode_data['content'])
        
        episode_id = self.engine.add_episode(agent_id, episode_data)
        
        # Logic for auto-extracting entities and relationships could go here in Part 2+
        return episode_id

    def recall(self, agent_id: str, query: str, context_type: str = 'semantic', limit: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories based on query and context type.
        """
        if context_type == 'semantic':
            query_embedding = self._generate_embedding(query)
            results = self.engine.semantic_search(agent_id, query_embedding, limit)
            return results
        elif context_type == 'episodic':
            # For now, just return latest episodes
            return self.engine.get_episodes(agent_id, limit)
        else:
            raise ValueError(f"Unsupported context_type: {context_type}")

    def add_knowledge(self, agent_id: str, name: str, description: str, type: str = "concept") -> str:
        """Manually add an entity (knowledge) to the agent's memory."""
        entity_data = {
            "name": name,
            "description": description,
            "type": type,
            "embedding": self._generate_embedding(f"{name} {description}")
        }
        return self.engine.add_entity(agent_id, entity_data)

    def relate(self, agent_id: str, source_id: str, target_id: str, rel_type: str, strength: float = 1.0) -> str:
        """Establish a relationship between two memory elements."""
        rel_data = {
            "source_id": source_id,
            "target_id": target_id,
            "type": rel_type,
            "strength": strength
        }
        return self.engine.add_relationship(agent_id, rel_data)

    def get_context(self, agent_id: str, current_task: str) -> str:
        """
        A high-level helper for agents to get a formatted context string 
        of relevant past experiences to inject into their prompt.
        """
        memories = self.recall(agent_id, current_task, limit=3)
        if not memories:
            return "No relevant past experiences found."
        
        context = "Relevant past experiences:\n"
        for i, mem in enumerate(memories, 1):
            context += f"{i}. {mem['content']} (Relevance: {mem.get('similarity', 'N/A'):.2f})\n"
        return context

if __name__ == "__main__":
    # Demo the SDK
    sdk = ChronosGraphSDK("demo_chronos.db")
    aid = sdk.initialize_agent("ResearchBot", "An agent that researches AI memory.")
    
    # 1. Agent performs an action
    eid1 = sdk.check_in(aid, {
        "type": "action",
        "content": "I searched for 'AI agent memory frameworks' and found Mem0 and LangMem."
    })
    
    # 2. Agent has a thought
    eid2 = sdk.check_in(aid, {
        "type": "thought",
        "content": "Mem0 seems useful for personalization, while LangMem is good for LangGraph users.",
        "parent_episode_id": eid1
    })
    
    # 3. Agent recalls context for a new task
    task = "How should I design my own memory database?"
    context = sdk.get_context(aid, task)
    print(f"Context for task '{task}':\n{context}")
    
    # 4. Agent adds a specific entity and relates it
    ent_id = sdk.add_knowledge(aid, "ChronosGraph", "A hybrid episodic-relational memory database.", "system")
    sdk.relate(aid, eid2, ent_id, "INSPIRED_BY")
    
    print("Demo completed successfully.")
