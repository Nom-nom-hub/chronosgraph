from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

class VectorStore(ABC):
    """
    Abstract Base Class for Vector Stores in ChronosGraph.
    This interface allows switching between local (SQLite) and external (Pinecone, Weaviate) backends.
    """
    
    @abstractmethod
    def add_vector(self, vector_id: str, agent_id: str, embedding: List[float], metadata: Optional[Dict[str, Any]] = None) -> None:
        """Adds a vector with its associated ID and metadata to the store."""
        pass

    @abstractmethod
    def search(self, agent_id: str, query_embedding: List[float], limit: int = 5, include_shared: bool = True, shared_group: Optional[str] = None) -> List[Dict[str, Any]]:
        """Performs a similarity search and returns a list of results with scores."""
        pass

    @abstractmethod
    def delete_vector(self, vector_id: str) -> None:
        """Removes a vector from the store."""
        pass

    @abstractmethod
    def clear_agent_memory(self, agent_id: str) -> None:
        """Removes all vectors associated with a specific agent."""
        pass

import sqlite3
import numpy as np
from .logger import logger
from .exceptions import DatabaseError, AgentNotFoundError

class LocalVectorStore(VectorStore):
    """
    Default implementation of VectorStore using the local SQLite database and NumPy.
    """
    def __init__(self, db_path: str):
        self.db_path = db_path

    def add_vector(self, vector_id: str, agent_id: str, embedding: List[float], metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        In the local implementation, embeddings are stored directly in the episodes table.
        This method is a no-op as ChronosGraphEngine handles the storage in SQL for now.
        Future refactoring could separate the embedding storage into a dedicated table.
        """
        pass

    def search(self, agent_id: str, query_embedding: List[float], limit: int = 5, include_shared: bool = True, shared_group: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Vectorized cosine similarity search using SQLite and NumPy.
        """
        try:
            query_vec = np.array(query_embedding, dtype=np.float32)
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if include_shared and shared_group:
                    # Search episodes: self or shared in group
                    cursor.execute("""
                        SELECT e.episode_id, e.content, e.embedding, a.name as agent_name 
                        FROM episodes e
                        JOIN agents a ON e.agent_id = a.agent_id
                        WHERE (e.agent_id = ? OR a.shared_group = ?) AND e.embedding IS NOT NULL
                    """, (agent_id, shared_group))
                else:
                    cursor.execute("""
                        SELECT episode_id, content, embedding, 'self' as agent_name 
                        FROM episodes 
                        WHERE agent_id = ? AND embedding IS NOT NULL
                    """, (agent_id,))
                
                rows = cursor.fetchall()
                if not rows:
                    return []

                # Vectorized cosine similarity calculation
                episode_ids = [row["episode_id"] for row in rows]
                contents = [row["content"] for row in rows]
                agent_names = [row["agent_name"] for row in rows]
                
                # Stack all stored embeddings into a single matrix
                stored_matrix = np.stack([np.frombuffer(row["embedding"], dtype=np.float32) for row in rows])
                
                # Calculate norms
                query_norm = np.linalg.norm(query_vec)
                stored_norms = np.linalg.norm(stored_matrix, axis=1)
                
                # Avoid division by zero
                stored_norms[stored_norms == 0] = 1e-10
                if query_norm == 0:
                    query_norm = 1e-10
                
                # Cosine similarity: (A . B) / (||A|| * ||B||)
                dot_products = np.dot(stored_matrix, query_vec)
                similarities = dot_products / (query_norm * stored_norms)
                
                results = []
                for i in range(len(rows)):
                    results.append({
                        "episode_id": episode_ids[i],
                        "content": contents[i],
                        "agent_name": agent_names[i],
                        "similarity": float(similarities[i])
                    })
                
                # Sort by similarity descending
                results.sort(key=lambda x: x["similarity"], reverse=True)
                return results[:limit]
        except sqlite3.Error as e:
            logger.error(f"LocalVectorStore search failed: {e}", extra={"agent_id": agent_id, "error_type": "DatabaseError"})
            raise DatabaseError(e) from e

    def delete_vector(self, vector_id: str) -> None:
        """Handled by SQL cascade/deletion logic in the engine."""
        pass

    def clear_agent_memory(self, agent_id: str) -> None:
        """Handled by SQL deletion logic in the engine."""
        pass

class PineconeVectorStore(VectorStore):
    """
    Scaffold for Pinecone integration.
    Requires 'pinecone-client' package.
    """
    def __init__(self, api_key: str, environment: str, index_name: str):
        # self.pc = Pinecone(api_key=api_key)
        # self.index = self.pc.Index(index_name)
        logger.info(f"PineconeVectorStore initialized for index: {index_name}")

    def add_vector(self, vector_id: str, agent_id: str, embedding: List[float], metadata: Optional[Dict[str, Any]] = None) -> None:
        # self.index.upsert(vectors=[(vector_id, embedding, {"agent_id": agent_id, **(metadata or {})})])
        pass

    def search(self, agent_id: str, query_embedding: List[float], limit: int = 5, include_shared: bool = True, shared_group: Optional[str] = None) -> List[Dict[str, Any]]:
        # filter = {"agent_id": agent_id}
        # if include_shared and shared_group:
        #     filter = {"$or": [{"agent_id": agent_id}, {"shared_group": shared_group}]}
        # response = self.index.query(vector=query_embedding, top_k=limit, filter=filter, include_metadata=True)
        # return [{"episode_id": match.id, "similarity": match.score, **match.metadata} for match in response.matches]
        return []

    def delete_vector(self, vector_id: str) -> None:
        # self.index.delete(ids=[vector_id])
        pass

    def clear_agent_memory(self, agent_id: str) -> None:
        # self.index.delete(filter={"agent_id": agent_id})
        pass
