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
from .vector_store import VectorStore, LocalVectorStore


class ChronosGraphEngine:
    def __init__(self, db_path: str = "chronosgraph.db", vector_store: Optional[VectorStore] = None):
        self.db_path = db_path
        self.migration_manager = MigrationManager(self.db_path)
        self._initialize_db()
        self.vector_store = vector_store or LocalVectorStore(self.db_path)
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
                        entity_id, agent_id, name, type, description, embedding, visibility, owner_agent_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entity_id, agent_id, 
                    entity_data.get("name"),
                    entity_data.get("type"),
                    entity_data.get("description"),
                    embedding,
                    entity_data.get("visibility", 0),
                    entity_data.get("owner_agent_id", agent_id)
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

    def get_episodes(self, agent_id: str, limit: int = 10, include_archived: bool = False) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                # Verify agent exists
                cursor.execute("SELECT 1 FROM agents WHERE agent_id = ?", (agent_id,))
                if not cursor.fetchone():
                    logger.warning(f"Cannot retrieve episodes: Agent not found: {agent_id}", extra={"agent_id": agent_id, "error_type": "AgentNotFoundError"})
                    raise AgentNotFoundError(agent_id)

                query = "SELECT * FROM episodes WHERE agent_id = ?"
                if not include_archived:
                    query += " AND (is_archived = 0 OR is_archived IS NULL)"
                query += " ORDER BY timestamp DESC LIMIT ?"
                
                cursor.execute(query, (agent_id, limit))
                rows = cursor.fetchall()
                logger.debug(f"Retrieved {len(rows)} episodes for agent {agent_id}", extra={"agent_id": agent_id, "count": len(rows), "include_archived": include_archived})
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve episodes for agent {agent_id}: {e}", extra={"agent_id": agent_id, "error_type": "DatabaseError"})
            raise DatabaseError(e) from e

    def archive_episodes(self, agent_id: str, episode_ids: List[str]) -> None:
        """Marks a list of episodes as archived."""
        if not episode_ids:
            return
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                placeholders = ','.join(['?'] * len(episode_ids))
                cursor.execute(
                    f"UPDATE episodes SET is_archived = 1 WHERE agent_id = ? AND episode_id IN ({placeholders})",
                    (agent_id, *episode_ids)
                )
                conn.commit()
                logger.info(f"Archived {len(episode_ids)} episodes for agent {agent_id}.", extra={"agent_id": agent_id, "count": len(episode_ids)})
        except sqlite3.Error as e:
            logger.error(f"Failed to archive episodes for agent {agent_id}: {e}", extra={"agent_id": agent_id, "error_type": "DatabaseError"})
            raise DatabaseError(e) from e

    def semantic_search(self, agent_id: str, query_embedding: List[float], limit: int = 5, include_shared: bool = True) -> List[Dict[str, Any]]:
        """
        Similarity search using the configured VectorStore.
        Supports searching across a shared group of agents.
        """
        try:
            # 1. Verify agent exists and find shared group
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT shared_group FROM agents WHERE agent_id = ?", (agent_id,))
                row = cursor.fetchone()
                if row is None:
                    logger.warning(f"Cannot perform semantic search: Agent not found: {agent_id}", extra={"agent_id": agent_id, "error_type": "AgentNotFoundError"})
                    raise AgentNotFoundError(agent_id)
                
                shared_group = row["shared_group"]

            # 2. Delegate search to the vector store
            results = self.vector_store.search(
                agent_id=agent_id,
                query_embedding=query_embedding,
                limit=limit,
                include_shared=include_shared,
                shared_group=shared_group
            )
            
            logger.debug(f"Semantic search performed for agent {agent_id}, found {len(results)} results.", extra={"agent_id": agent_id, "results_count": len(results)})
            return results
        except Exception as e:
            if isinstance(e, AgentNotFoundError):
                raise e
            logger.error(f"Failed to perform semantic search for agent {agent_id}: {e}", extra={"agent_id": agent_id, "error_type": e.__class__.__name__})
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

                # 1. Find the starting entity (own entity or shared/public)
                cursor.execute("""
                    SELECT entity_id, name, description 
                    FROM entities 
                    WHERE name = ? AND (agent_id = ? OR visibility >= 1)
                """, (entity_name, agent_id))
                start_node = cursor.fetchone()
                if not start_node:
                    logger.info(f"Starting entity not found for agent {agent_id} with name {entity_name}", extra={"agent_id": agent_id, "entity_name": entity_name})
                    raise EntityNotFoundError(f"Entity with name {entity_name} not found for agent {agent_id}")
                
                # 2. Find all related entities and episodes (1-hop for now, bi-directional)
                # Respects visibility: 0: Private, 1: Shared, 2: Public
                cursor.execute("""
                    -- Outgoing relationships to other entities
                    SELECT 'entity' as result_type, e.name as content, r.type as rel_type
                    FROM entities e
                    JOIN relationships r ON e.entity_id = r.target_id
                    WHERE r.source_id = ? AND (e.agent_id = ? OR e.visibility >= 1)
                    UNION
                    -- Incoming relationships from other entities
                    SELECT 'entity' as result_type, e.name as content, r.type as rel_type
                    FROM entities e
                    JOIN relationships r ON e.entity_id = r.source_id
                    WHERE r.target_id = ? AND (e.agent_id = ? OR e.visibility >= 1)
                    UNION
                    -- Outgoing relationships to episodes
                    SELECT 'episode' as result_type, ep.content as content, r.type as rel_type
                    FROM episodes ep
                    JOIN relationships r ON ep.episode_id = r.target_id
                    WHERE r.source_id = ? AND ep.agent_id = ?
                    UNION
                    -- Incoming relationships from episodes
                    SELECT 'episode' as result_type, ep.content as content, r.type as rel_type
                    FROM episodes ep
                    JOIN relationships r ON ep.episode_id = r.source_id
                    WHERE r.target_id = ? AND ep.agent_id = ?
                """, (start_node["entity_id"], agent_id, start_node["entity_id"], agent_id, start_node["entity_id"], agent_id, start_node["entity_id"], agent_id))
                
                rows = cursor.fetchall()
                logger.debug(f"Retrieved graph context for agent {agent_id} and entity {entity_name}, found {len(rows)} results.", extra={"agent_id": agent_id, "entity_name": entity_name, "count": len(rows)})
                return [dict(row) for row in rows]
        except sqlite3.Error as e:
            logger.error(f"Failed to retrieve graph context for agent {agent_id} and entity {entity_name}: {e}", extra={"agent_id": agent_id, "entity_name": entity_name, "error_type": "DatabaseError"})
            raise DatabaseError(e) from e

    def export_mermaid_graph(self, agent_id: str) -> str:
        """
        Exports the agent's knowledge graph as a Mermaid.js diagram string.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Verify agent exists
                cursor.execute("SELECT name FROM agents WHERE agent_id = ?", (agent_id,))
                agent_row = cursor.fetchone()
                if not agent_row:
                    raise AgentNotFoundError(agent_id)
                agent_name = agent_row["name"]

                # Fetch all entities
                cursor.execute("SELECT entity_id, name, type FROM entities WHERE agent_id = ?", (agent_id,))
                entities = cursor.fetchall()
                
                # Fetch all relationships
                cursor.execute("""
                    SELECT r.source_id, r.target_id, r.type, r.strength
                    FROM relationships r
                    WHERE r.agent_id = ?
                """, (agent_id,))
                relationships = cursor.fetchall()
                
                # Fetch recent episodes to link them if they are part of the graph
                cursor.execute("SELECT episode_id, content FROM episodes WHERE agent_id = ? LIMIT 20", (agent_id,))
                episodes = cursor.fetchall()
                
                mermaid = ["graph TD"]
                
                # Create a map for display names
                node_map = {}
                
                # Add entities to Mermaid
                for ent in entities:
                    eid = ent["entity_id"].replace("-", "_")
                    name = ent["name"]
                    etype = ent["type"]
                    mermaid.append(f"    {eid}[\"{name} ({etype})\"]")
                    node_map[ent["entity_id"]] = eid
                
                # Add episodes to Mermaid
                for ep in episodes:
                    epid = ep["episode_id"].replace("-", "_")
                    content = ep["content"][:30] + "..." if len(ep["content"]) > 30 else ep["content"]
                    mermaid.append(f"    {epid}(\"{content}\")")
                    node_map[ep["episode_id"]] = epid
                
                # Add relationships
                for rel in relationships:
                    src = rel["source_id"]
                    tgt = rel["target_id"]
                    rtype = rel["type"]
                    
                    if src in node_map and tgt in node_map:
                        mermaid.append(f"    {node_map[src]} -- \"{rtype}\" --> {node_map[tgt]}")
                
                return "\n".join(mermaid)
        except sqlite3.Error as e:
            logger.error(f"Failed to export Mermaid graph for agent {agent_id}: {e}", extra={"agent_id": agent_id, "error_type": "DatabaseError"})
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
