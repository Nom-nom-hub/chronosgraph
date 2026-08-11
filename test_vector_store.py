import os
import unittest
import numpy as np
from .chronosgraph_engine import ChronosGraphEngine
from .vector_store import LocalVectorStore

class TestVectorStoreArchitecture(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_vector.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        
        self.engine = ChronosGraphEngine(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_local_vector_store_initialization(self):
        """Test that the engine correctly initializes with a LocalVectorStore."""
        self.assertIsInstance(self.engine.vector_store, LocalVectorStore)
        self.assertEqual(self.engine.vector_store.db_path, self.db_path)

    def test_semantic_search_delegation(self):
        """Test that semantic search is correctly delegated to the vector store."""
        agent_id = self.engine.register_agent("VectorAgent")
        
        # Add an episode with an embedding
        embedding = [0.1] * 1536
        self.engine.add_episode(agent_id, {
            "content": "Vector test episode",
            "type": "thought",
            "embedding": embedding
        })
        
        # Perform semantic search
        results = self.engine.semantic_search(agent_id, embedding, limit=1)
        
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['content'], "Vector test episode")
        self.assertGreater(results[0]['similarity'], 0.99)

if __name__ == "__main__":
    unittest.main()
