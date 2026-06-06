import json
import sqlite3
import uuid
from datetime import UTC, datetime
from typing import Any, Dict, List, Optional

import numpy as np

from .exceptions import (
    AgentNotFoundError,
    DatabaseError,
    EpisodeNotFoundError,
    EntityNotFoundError,
    RelationshipNotFoundError,
    InvalidEpisodeDataError
)
from .logger import logger
from .migrations import MigrationManager


class ChronosGraphEngine:
    def __init__(self, db_path: str = "chronosgraph.db"):
        self.db_path = db_path
        self.migration_manager = MigrationManager(self.db_path)
        self._initialize_db()
        logger.info(f"ChronosGraphEngine initialized with database: {self.db_path}")

    def _initialize_db(self):
        """Initializes the database and applies pending migrations."""
        try:
            self.migration_manager.apply_migrations()
            logger.info("Database schema initialized and migrations applied successfully.")
        except Exception as e:
            logger.error(f"Database initialization or migration failed: {e}", extra={"error_type": "DatabaseError"})
            raise DatabaseError(e) from e

    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM agents WHERE agent_id = ?", (agent_id,))
                agent = cursor.fetchone()
                if agent is None:
                    logger.warning(f"Agent not found: {agent_id}", extra={"agent_id": agent_id, "error_type": "AgentNotFoundError"})
                    raise AgentNotFoundError(agent_id)
                logger.debug(f"Retrieved agent: {agent_id}", extra={"agent_id": agent_id})
                return dict(agent)
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve agent {agent_id}: {e}", extra={"agent_id": agent_id, "error_type": "DatabaseError"})
            raise DatabaseError(e) from e

    def register_agent(self, name: str, description: str = "", shared_group: str = None) -> str:
        agent_id = str(uuid.uuid4())
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO agents (agent_id, name, description, shared_group) VALUES (?, ?, ?, ?)",
                    (agent_id, name, description, shared_group)
                )
                conn.commit()
            logger.info(f"Agent registered: {name} with ID {agent_id}", extra={"agent_id": agent_id, "agent_name": name})
            return agent_id
        except sqlite3.IntegrityError as e:
            logger.error(f"Agent with name {name} already exists.", extra={"agent_name": name, "error_type": "IntegrityError"})
            raise ValueError(f"Agent with name \'{name}\' already exists.") from e
        except sqlite3.Error as e:
            logger.error(f"Failed to register agent {name}: {e}", extra={"agent_name": name, "error_type": "DatabaseError"})
            raise DatabaseError(e) from e

    def add_episode(self, agent_id: str, episode_data: Dict[str, Any]) -> str:
        if 'type' not in episode_data or 'content' not in episode_data:
            logger.error("Invalid episode data: missing 'type' or 'content'", extra={"agent_id": agent_id, "error_type": "InvalidEpisodeDataError"})
            raise InvalidEpisodeDataError("Episode data must contain 'type' and 'content'.")

        episode_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC).isoformat()
        
        # Serialize embedding if present
        embedding = episode_data.get('embedding')
        if embedding is not None:
            embedding = np.array(embedding, dtype=np.float32).tobytes()

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Verify agent exists
                cursor.execute("SELECT 1 FROM agents WHERE agent_id = ?", (agent_id,))
                if not cursor.fetchone():
                    logger.warning(f"Cannot add episode: Agent not found: {agent_id}", extra={"agent_id": agent_id, "error_type": "AgentNotFoundError"})
                    raise AgentNotFoundError(agent_id)

                cursor.execute('''
                    INSERT INTO episodes (
                        episode_id, agent_id, timestamp, type, content, embedding, 
                        tool_name, tool_input, tool_output, success, parent_episode_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    episode_id, agent_id, timestamp, 
                    episode_data.get('type'), 
                    episode_data.get('content'),
                    embedding,
                    episode_data.get('tool_name'),
                    json.dumps(episode_data.get('tool_input')) if episode_data.get('tool_input') else None,
                    json.dumps(episode_data.get('tool_output')) if episode_data.get('tool_output') else None,
                    episode_data.get('success'),
                    episode_data.get('parent_episode_id')
                ))
                conn.commit()
            logger.info(f"Episode added: {episode_id} for agent {agent_id}", extra={"agent_id": agent_id, "episode_id": episode_id})
            return episode_id
        except sqlite3.Error as e:
            logger.error(f"Failed to add episode for agent {agent_id}: {e}", extra={"agent_id": agent_id, "error_type": "DatabaseError"})
            raise DatabaseError(e) from e

    def find_entity_by_name(self, agent_id: str, name: str) -> Optional[Dict[str, Any]]:
        """Find an entity by name for a specific agent."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(
                    "SELECT * FROM entities WHERE agent_id = ? AND name = ?",
                    (agent_id, name)
                )
                row = cursor.fetchone()
                return dict(row) if row else None
        except sqlite3.Error as e:
            logger.error(f"Failed to find entity by name {name}: {e}", extra={"agent_id": agent_id, "entity_name": name, "error_type": "DatabaseError"})
            raise DatabaseError(e) from e

    def add_entity(self, agent_id: str, entity_data: Dict[str, Any]) -> str:
        if 'name' not in entity_data or 'type' not in entity_data:
            logger.error("Invalid entity data: missing 'name' or 'type'", extra={"agent_id": agent_id, "error_type": "InvalidEntityDataError"})
            raise InvalidEpisodeDataError("Entity data must contain 'name' and 'type'.")

        entity_id = str(uuid.uuid4())
        
        embedding = entity_data.get("embedding")
        if embedding is not None:
            embedding = np.array(embedding, dtype=np.float32).tobytes()

        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Verify agent exists
                cursor.execute("SELECT 1 FROM agents WHERE agent_id = ?", (agent_id,))
                if not cursor.fetchone():
                    logger.warning(f"Cannot add entity: Agent not found: {agent_id}", extra={"agent_id": agent_id, "error_type": "AgentNotFoundError"})
                    raise AgentNotFoundError(agent_id)

                cursor.execute("""
                    INSERT INTO entities (
                        entity_id, agent_id, name, type, description, embedding
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    entity_id, agent_id, 
                    entity_data.get("name"),
                    entity_data.get("type"),
                    entity_data.get("description"),
                    embedding
                ))
                conn.commit()
            logger.info(f"Entity added: {entity_data.get('name')} with ID {entity_id} for agent {agent_id}", extra={"agent_id": agent_id, "entity_id": entity_id, "entity_name": entity_data.get('name')})
            return entity_id
        except sqlite3.Error as e:
            logger.error(f"Failed to add entity for agent {agent_id}: {e}", extra={"agent_id": agent_id, "error_type": "DatabaseError"})
            raise DatabaseError(e) from e

    def add_relationship(self, agent_id: str, rel_data: Dict[str, Any]) -> str:
        if 'source_id' not in rel_data or 'target_id' not in rel_data or 'type' not in rel_data:
            logger.error("Invalid relationship data: missing source_id, target_id, or type", extra={"agent_id": agent_id, "error_type": "InvalidRelationshipDataError"})
            raise InvalidEpisodeDataError("Relationship data must contain source_id, target_id, and type.")

        relationship_id = str(uuid.uuid4())
        timestamp = datetime.now(UTC).isoformat()
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Verify agent exists
                cursor.execute("SELECT 1 FROM agents WHERE agent_id = ?", (agent_id,))
                if not cursor.fetchone():
                    logger.warning(f"Cannot add relationship: Agent not found: {agent_id}", extra={"agent_id": agent_id, "error_type": "AgentNotFoundError"})
                    raise AgentNotFoundError(agent_id)

                cursor.execute("""
                    INSERT INTO relationships (
                        relationship_id, agent_id, source_id, target_id, type, strength, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    relationship_id, agent_id,
                    rel_data.get("source_id"),
                    rel_data.get("target_id"),
                    rel_data.get("type"),
                    rel_data.get("strength", 1.0),
                    timestamp
                ))
                conn.commit()
            logger.info(f"Relationship added: {relationship_id} for agent {agent_id}", extra={"agent_id": agent_id, "relationship_id": relationship_id})
            return relationship_id
        except sqlite3.Error as e:
            logger.error(f"Failed to add relationship for agent {agent_id}: {e}", extra={"agent_id": agent_id, "error_type": "DatabaseError"})
            raise DatabaseError(e) from e

    def get_episodes(self, agent_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                # Verify agent exists
                cursor.execute("SELECT 1 FROM agents WHERE agent_id = ?", (agent_id,))
                if not cursor.fetchone():
                    logger.warning(f"Cannot retrieve episodes: Agent not found: {agent_id}", extra={"agent_id": agent_id, "error_type": "AgentNotFoundError"})
                    raise AgentNotFoundError(agent_id)

                cursor.execute(
                    "SELECT * FROM episodes WHERE agent_id = ? ORDER BY timestamp DESC LIMIT ?",
                    (agent_id, limit)
                )
                rows = cursor.fetchall()
                logger.debug(f"Retrieved {len(rows)} episodes for agent {agent_id}", extra={"agent_id": agent_id, "count": len(rows)})
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve episodes for agent {agent_id}: {e}", extra={"agent_id": agent_id, "error_type": "DatabaseError"})
            raise DatabaseError(e) from e

    def semantic_search(self, agent_id: str, query_embedding: List[float], limit: int = 5, include_shared: bool = True) -> List[Dict[str, Any]]:
        """
        Simple cosine similarity search in SQLite. 
        Supports searching across a shared group of agents.
        """
        try:
            query_vec = np.array(query_embedding, dtype=np.float32)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Verify agent exists
                cursor.execute("SELECT 1 FROM agents WHERE agent_id = ?", (agent_id,))
                if not cursor.fetchone():
                    logger.warning(f"Cannot perform semantic search: Agent not found: {agent_id}", extra={"agent_id": agent_id, "error_type": "AgentNotFoundError"})
                    raise AgentNotFoundError(agent_id)

                # Find shared group
                cursor.execute("SELECT shared_group FROM agents WHERE agent_id = ?", (agent_id,))
                row = cursor.fetchone()
                shared_group = row["shared_group"] if row else None
                
                if include_shared and shared_group:
                    cursor.execute("""
                        SELECT e.episode_id, e.content, e.embedding, a.name as agent_name 
                        FROM episodes e
                        JOIN agents a ON e.agent_id = a.agent_id
                        WHERE (e.agent_id = ? OR a.shared_group = ?) AND e.embedding IS NOT NULL
                    """, (agent_id, shared_group))
                else:
                    cursor.execute(
                        "SELECT episode_id, content, embedding, 'self' as agent_name FROM episodes WHERE agent_id = ? AND embedding IS NOT NULL",
                        (agent_id,)
                    )
                rows = cursor.fetchall()
                
                results = []
                for row in rows:
                    stored_vec = np.frombuffer(row["embedding"], dtype=np.float32)
                    # Calculate cosine similarity
                    similarity = np.dot(query_vec, stored_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(stored_vec))
                    results.append({
                        "episode_id": row["episode_id"],
                        "content": row["content"],
                        "agent_name": row["agent_name"],
                        "similarity": float(similarity)
                    })
                
                # Sort by similarity descending
                results.sort(key=lambda x: x["similarity"], reverse=True)
                logger.debug(f"Semantic search performed for agent {agent_id}, found {len(results)} results.", extra={"agent_id": agent_id, "query_embedding_len": len(query_embedding), "results_count": len(results)})
                return results[:limit]
        except sqlite3.Error as e:
            logger.error(f"Failed to perform semantic search for agent {agent_id}: {e}", extra={"agent_id": agent_id, "error_type": "DatabaseError"})
            raise DatabaseError(e) from e

    def get_related_entities(self, agent_id: str, source_id: str) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                # Verify agent exists
                cursor.execute("SELECT 1 FROM agents WHERE agent_id = ?", (agent_id,))
                if not cursor.fetchone():
                    logger.warning(f"Cannot retrieve related entities: Agent not found: {agent_id}", extra={"agent_id": agent_id, "error_type": "AgentNotFoundError"})
                    raise AgentNotFoundError(agent_id)

                cursor.execute("""
                    SELECT e.*, r.type as rel_type, r.strength 
                    FROM entities e
                    JOIN relationships r ON e.entity_id = r.target_id
                    WHERE r.agent_id = ? AND r.source_id = ?
                """, (agent_id, source_id))
                rows = cursor.fetchall()
                logger.debug(f"Retrieved {len(rows)} related entities for agent {agent_id} and source {source_id}", extra={"agent_id": agent_id, "source_id": source_id, "count": len(rows)})
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve related entities for agent {agent_id} and source {source_id}: {e}", extra={"agent_id": agent_id, "source_id": source_id, "error_type": "DatabaseError"})
            raise DatabaseError(e) from e

    def get_graph_context(self, agent_id: str, entity_name: str, depth: int = 1) -> List[Dict[str, Any]]:
        """
        Traverses the graph to find all related information for a given entity name.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Verify agent exists
                cursor.execute("SELECT 1 FROM agents WHERE agent_id = ?", (agent_id,))
                if not cursor.fetchone():
                    logger.warning(f"Cannot retrieve graph context: Agent not found: {agent_id}", extra={"agent_id": agent_id, "error_type": "AgentNotFoundError"})
                    raise AgentNotFoundError(agent_id)

                # 1. Find the starting entity
                cursor.execute(
                    "SELECT entity_id, name, description FROM entities WHERE agent_id = ? AND name = ?",
                    (agent_id, entity_name)
                )
                start_node = cursor.fetchone()
                if not start_node:
                    logger.info(f"Starting entity not found for agent {agent_id} with name {entity_name}", extra={"agent_id": agent_id, "entity_name": entity_name})
                    raise EntityNotFoundError(f"Entity with name {entity_name} not found for agent {agent_id}")
                
                # 2. Find all related entities and episodes (1-hop for now)
                cursor.execute("""
                    SELECT 'entity' as result_type, e.name as content, r.type as rel_type
                    FROM entities e
                    JOIN relationships r ON e.entity_id = r.target_id
                    WHERE r.agent_id = ? AND r.source_id = ?
                    UNION
                    SELECT 'episode' as result_type, ep.content as content, r.type as rel_type
                    FROM episodes ep
                    JOIN relationships r ON ep.episode_id = r.source_id
                    WHERE r.agent_id = ? AND r.target_id = ?
                """, (agent_id, start_node["entity_id"], agent_id, start_node["entity_id"]))
                
                rows = cursor.fetchall()
                logger.debug(f"Retrieved graph context for agent {agent_id} and entity {entity_name}, found {len(rows)} results.", extra={"agent_id": agent_id, "entity_name": entity_name, "count": len(rows)})
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve graph context for agent {agent_id} and entity {entity_name}: {e}", extra={"agent_id": agent_id, "entity_name": entity_name, "error_type": "DatabaseError"})
            raise DatabaseError(e) from e

if __name__ == "__main__":
    # Basic smoke test
    engine = ChronosGraphEngine("test_chronos.db")
    aid = engine.register_agent("TestAgent", "A test agent for ChronosGraph")
    print(f"Registered agent: {aid}")
    
    eid = engine.add_episode(aid, {
        "type": "thought",
        "content": "I need to build a database for AI agents.",
        "embedding": [0.1] * 128 # Dummy embedding
    })
    print(f"Added episode: {eid}")
    
    episodes = engine.get_episodes(aid)
    print(f"Retrieved {len(episodes)} episodes.")
    
    results = engine.semantic_search(aid, [0.1] * 128)
    print(f"Semantic search results: {len(results)}")
