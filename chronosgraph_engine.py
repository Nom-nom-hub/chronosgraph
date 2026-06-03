import sqlite3
import json
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional
import numpy as np

class ChronosGraphEngine:
    def __init__(self, db_path: str = "chronosgraph.db"):
        self.db_path = db_path
        self._initialize_db()

    def _initialize_db(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create Agents table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT
                )
            ''')
            
            # Create Episodes table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS episodes (
                    episode_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding BLOB,
                    tool_name TEXT,
                    tool_input TEXT,
                    tool_output TEXT,
                    success BOOLEAN,
                    parent_episode_id TEXT,
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id),
                    FOREIGN KEY (parent_episode_id) REFERENCES episodes(episode_id)
                )
            ''')
            
            # Create Entities table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS entities (
                    entity_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    description TEXT,
                    embedding BLOB,
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            ''')
            
            # Create Relationships table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS relationships (
                    relationship_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    strength REAL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            ''')
            conn.commit()

    def register_agent(self, name: str, description: str = "") -> str:
        agent_id = str(uuid.uuid4())
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO agents (agent_id, name, description) VALUES (?, ?, ?)",
                (agent_id, name, description)
            )
            conn.commit()
        return agent_id

    def add_episode(self, agent_id: str, episode_data: Dict[str, Any]) -> str:
        episode_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        # Serialize embedding if present
        embedding = episode_data.get('embedding')
        if embedding is not None:
            embedding = np.array(embedding, dtype=np.float32).tobytes()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
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
        return episode_id

    def add_entity(self, agent_id: str, entity_data: Dict[str, Any]) -> str:
        entity_id = str(uuid.uuid4())
        
        embedding = entity_data.get('embedding')
        if embedding is not None:
            embedding = np.array(embedding, dtype=np.float32).tobytes()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO entities (
                    entity_id, agent_id, name, type, description, embedding
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                entity_id, agent_id, 
                entity_data.get('name'),
                entity_data.get('type'),
                entity_data.get('description'),
                embedding
            ))
            conn.commit()
        return entity_id

    def add_relationship(self, agent_id: str, rel_data: Dict[str, Any]) -> str:
        relationship_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO relationships (
                    relationship_id, agent_id, source_id, target_id, type, strength, timestamp
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                relationship_id, agent_id,
                rel_data.get('source_id'),
                rel_data.get('target_id'),
                rel_data.get('type'),
                rel_data.get('strength', 1.0),
                timestamp
            ))
            conn.commit()
        return relationship_id

    def get_episodes(self, agent_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM episodes WHERE agent_id = ? ORDER BY timestamp DESC LIMIT ?",
                (agent_id, limit)
            )
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

    def semantic_search(self, agent_id: str, query_embedding: List[float], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Simple cosine similarity search in SQLite. 
        Note: For a production system, a dedicated vector index would be used.
        """
        query_vec = np.array(query_embedding, dtype=np.float32)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT episode_id, content, embedding FROM episodes WHERE agent_id = ? AND embedding IS NOT NULL", (agent_id,))
            rows = cursor.fetchall()
            
            results = []
            for row in rows:
                stored_vec = np.frombuffer(row['embedding'], dtype=np.float32)
                # Calculate cosine similarity
                similarity = np.dot(query_vec, stored_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(stored_vec))
                results.append({
                    'episode_id': row['episode_id'],
                    'content': row['content'],
                    'similarity': float(similarity)
                })
            
            # Sort by similarity descending
            results.sort(key=lambda x: x['similarity'], reverse=True)
            return results[:limit]

    def get_related_entities(self, agent_id: str, source_id: str) -> List[Dict[str, Any]]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute('''
                SELECT e.*, r.type as rel_type, r.strength 
                FROM entities e
                JOIN relationships r ON e.entity_id = r.target_id
                WHERE r.agent_id = ? AND r.source_id = ?
            ''', (agent_id, source_id))
            rows = cursor.fetchall()
            return [dict(row) for row in rows]

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
