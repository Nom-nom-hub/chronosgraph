from typing import Any, Dict, List, Optional
import numpy as np
from openai import OpenAI
from .chronosgraph_engine import ChronosGraphEngine
from .fact_extractor import FactExtractor
from .exceptions import (
    AgentNotFoundError,
    DatabaseError,
    EpisodeNotFoundError,
    EntityNotFoundError,
    RelationshipNotFoundError,
    InvalidEpisodeDataError,
    EmbeddingGenerationError,
    FactExtractionError
)
from .logger import logger

class ChronosGraphSDK:
    """
    Universal SDK for AI agents to interact with ChronosGraph.
    This layer handles embedding generation, fact extraction, and high-level logic.
    """
    def __init__(self, db_path: str = "chronosgraph.db", openai_client: Optional[OpenAI] = None):
        try:
            self.engine = ChronosGraphEngine(db_path)
            self.client = openai_client or OpenAI()
            self.extractor = FactExtractor(self.client)
            logger.info(f"ChronosGraphSDK initialized with database: {db_path}")
        except Exception as e:
            logger.error(f"Failed to initialize ChronosGraphSDK: {e}", extra={"error_type": "InitializationError"})
            raise DatabaseError(e) from e

    def _generate_embedding(self, text: str) -> List[float]:
        """Generates a semantic embedding for the given text using OpenAI."""
        try:
            response = self.client.embeddings.create(
                input=[text.replace("\n", " ")],
                model="text-embedding-3-small"
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}", extra={"error_type": "EmbeddingGenerationError", "text": text})
            raise EmbeddingGenerationError(f"Failed to generate embedding for text: {text}") from e

    def initialize_agent(self, name: str, description: str = "", shared_group: str = None) -> str:
        """Register a new agent and return its ID."""
        try:
            agent_id = self.engine.register_agent(name, description, shared_group)
            logger.info(f"Agent initialized via SDK: {name} with ID {agent_id}", extra={"agent_id": agent_id, "agent_name": name})
            return agent_id
        except Exception as e:
            logger.error(f"Failed to initialize agent {name} via SDK: {e}", extra={"agent_name": name, "error_type": "SDKInitializationError"})
            raise e

    def check_in(self, agent_id: str, episode_data: Dict[str, Any], auto_extract: bool = True) -> str:
        """Store a new episode and optionally extract facts."""
        try:
            content = episode_data.get("content", "")
            if "type" not in episode_data:
                episode_data["type"] = "observation"
                
            if content and "embedding" not in episode_data:
                episode_data["embedding"] = self._generate_embedding(content)
            
            episode_id = self.engine.add_episode(agent_id, episode_data)
            
            if auto_extract and content:
                self._process_auto_extraction(agent_id, episode_id, content)
                
            logger.info(f"Agent {agent_id} checked in new episode {episode_id}.", extra={"agent_id": agent_id, "episode_id": episode_id})
            return episode_id
        except (AgentNotFoundError, InvalidEpisodeDataError, EmbeddingGenerationError, FactExtractionError, DatabaseError) as e:
            logger.error(f"Failed to check in episode for agent {agent_id}: {e}", extra={"agent_id": agent_id, "error_type": e.__class__.__name__})
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred during check-in for agent {agent_id}: {e}", extra={"agent_id": agent_id, "error_type": "UnexpectedError"})
            raise e

    def _process_auto_extraction(self, agent_id: str, episode_id: str, content: str):
        """Extract and store facts from an episode."""
        try:
            facts = self.extractor.extract_facts(content)
            entity_map = {}
            for ent in facts.get('entities', []):
                try:
                    ent_id = self.add_knowledge(agent_id, ent['name'], ent.get('description', ''), ent.get('type', 'concept'))
                    entity_map[ent['name']] = ent_id
                    self.relate(agent_id, episode_id, ent_id, "MENTIONS")
                    logger.debug(f"Extracted and added entity {ent['name']} for agent {agent_id}.", extra={"agent_id": agent_id, "entity_name": ent['name']})
                except Exception as e:
                    logger.error(f"Failed to process extracted entity {ent.get('name')}: {e}", extra={"agent_id": agent_id, "entity_data": ent, "error_type": e.__class__.__name__})

            for rel in facts.get('relationships', []):
                try:
                    source_id = entity_map.get(rel['source'])
                    target_id = entity_map.get(rel['target'])
                    if source_id and target_id:
                        self.relate(agent_id, source_id, target_id, rel['type'], rel.get('strength', 1.0))
                        logger.debug(f"Extracted and added relationship between {rel['source']} and {rel['target']} for agent {agent_id}.", extra={"agent_id": agent_id, "relationship_data": rel})
                except Exception as e:
                    logger.error(f"Failed to process extracted relationship {rel.get('source')}->{rel.get('target')}: {e}", extra={"agent_id": agent_id, "relationship_data": rel, "error_type": e.__class__.__name__})
            logger.info(f"Auto-extraction completed for episode {episode_id} for agent {agent_id}.", extra={"agent_id": agent_id, "episode_id": episode_id})
        except FactExtractionError as e:
            logger.error(f"Fact extraction failed for episode {episode_id}: {e}", extra={"agent_id": agent_id, "episode_id": episode_id, "error_type": "FactExtractionError"})
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred during auto-extraction for episode {episode_id}: {e}", extra={"agent_id": agent_id, "episode_id": episode_id, "error_type": "UnexpectedError"})
            raise e

    def recall(self, agent_id: str, query: str, context_type: str = 'semantic', limit: int = 5, include_shared: bool = True) -> List[Dict[str, Any]]:
        """Retrieve memories based on query and context type."""
        try:
            if context_type == 'semantic':
                query_embedding = self._generate_embedding(query)
                results = self.engine.semantic_search(agent_id, query_embedding, limit, include_shared)
                logger.debug(f"Semantic recall for agent {agent_id}, query '{query}', found {len(results)} results.", extra={"agent_id": agent_id, "query": query, "context_type": context_type, "results_count": len(results)})
                return results
            elif context_type == 'relational':
                # Query is treated as an entity name to find its neighborhood
                results = self.engine.get_graph_context(agent_id, query)
                logger.debug(f"Relational recall for agent {agent_id}, query '{query}', found {len(results)} results.", extra={"agent_id": agent_id, "query": query, "context_type": context_type, "results_count": len(results)})
                return results
            elif context_type == 'episodic':
                results = self.engine.get_episodes(agent_id, limit)
                logger.debug(f"Episodic recall for agent {agent_id}, found {len(results)} results.", extra={"agent_id": agent_id, "context_type": context_type, "results_count": len(results)})
                return results
            else:
                logger.error(f"Unsupported context_type: {context_type}", extra={"agent_id": agent_id, "context_type": context_type, "error_type": "ValueError"})
                raise ValueError(f"Unsupported context_type: {context_type}")
        except (AgentNotFoundError, DatabaseError, EmbeddingGenerationError, EntityNotFoundError) as e:
            logger.error(f"Failed to recall memories for agent {agent_id} with query '{query}' and context type '{context_type}': {e}", extra={"agent_id": agent_id, "query": query, "context_type": context_type, "error_type": e.__class__.__name__})
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred during recall for agent {agent_id} with query '{query}' and context type '{context_type}': {e}", extra={"agent_id": agent_id, "query": query, "context_type": context_type, "error_type": "UnexpectedError"})
            raise e

    def add_knowledge(self, agent_id: str, name: str, description: str, type: str = "concept", visibility: int = 0) -> str:
        """Manually add an entity with deduplication and visibility control."""
        try:
            # 1. Deduplication Check
            existing_entity = self.engine.find_entity_by_name(agent_id, name)
            if existing_entity:
                logger.debug(f"Entity '{name}' already exists for agent {agent_id}. Skipping creation.", extra={"agent_id": agent_id, "entity_name": name, "entity_id": existing_entity['entity_id']})
                return existing_entity['entity_id']

            # 2. Create new entity
            entity_data = {
                "name": name,
                "description": description,
                "type": type,
                "visibility": visibility,
                "embedding": self._generate_embedding(f"{name} {description}")
            }
            entity_id = self.engine.add_entity(agent_id, entity_data)
            logger.info(f"Knowledge added: entity {name} with ID {entity_id} for agent {agent_id}.", extra={"agent_id": agent_id, "entity_id": entity_id, "entity_name": name})
            return entity_id
        except (AgentNotFoundError, InvalidEpisodeDataError, EmbeddingGenerationError, DatabaseError) as e:
            logger.error(f"Failed to add knowledge for agent {agent_id}, entity {name}: {e}", extra={"agent_id": agent_id, "entity_name": name, "error_type": e.__class__.__name__})
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred while adding knowledge for agent {agent_id}, entity {name}: {e}", extra={"agent_id": agent_id, "entity_name": name, "error_type": "UnexpectedError"})
            raise e

    def relate(self, agent_id: str, source_id: str, target_id: str, rel_type: str, strength: float = 1.0) -> str:
        """Relate two elements."""
        try:
            rel_data = {"source_id": source_id, "target_id": target_id, "type": rel_type, "strength": strength}
            relationship_id = self.engine.add_relationship(agent_id, rel_data)
            logger.info(f"Relationship added: {rel_type} between {source_id} and {target_id} for agent {agent_id}.", extra={"agent_id": agent_id, "source_id": source_id, "target_id": target_id, "rel_type": rel_type, "relationship_id": relationship_id})
            return relationship_id
        except (AgentNotFoundError, InvalidEpisodeDataError, DatabaseError) as e:
            logger.error(f"Failed to relate elements for agent {agent_id}, source {source_id}, target {target_id}: {e}", extra={"agent_id": agent_id, "source_id": source_id, "target_id": target_id, "rel_type": rel_type, "error_type": e.__class__.__name__})
            raise e
        except Exception as e:
            logger.error(f"An unexpected error occurred while relating elements for agent {agent_id}, source {source_id}, target {target_id}: {e}", extra={"agent_id": agent_id, "source_id": source_id, "target_id": target_id, "rel_type": rel_type, "error_type": "UnexpectedError"})
            raise e

    def get_context(self, agent_id: str, current_task: str, mode: str = "hybrid") -> str:
        """High-level helper for formatted context."""
        context = "Relevant past experiences (including shared knowledge):\n"
        
        # 1. Semantic Recall
        memories = self.recall(agent_id, current_task, context_type='semantic', limit=3)
        for i, mem in enumerate(memories, 1):
            source = f"Source: {mem['agent_name']}" if mem['agent_name'] != 'self' else "Source: Your Memory"
            context += f"- {mem['content']} ({source})\n"
            
        # 2. Relational Recall (if keywords found)
        # In a real system, we'd use an LLM to extract keywords from current_task
        # For now, we'll try to treat the whole task as a potential entity name
        try:
            relational = self.recall(agent_id, current_task, context_type='relational')
            if relational:
                context += "\nRelated Knowledge Graph connections:\n"
                for rel in relational:
                    context += f"- {rel['content']} (via {rel['rel_type']})\n"
        except EntityNotFoundError:
            # If the entity is not found, we just don't add relational context
            logger.debug(f"No relational context found for agent {agent_id} with query '{current_task}'", extra={"agent_id": agent_id, "query": current_task})
            pass
                
        return context
