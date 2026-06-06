import os
import unittest
from unittest.mock import MagicMock
from .chronosgraph_sdk import ChronosGraphSDK

class TestDeduplication(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_deduplication.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        
        # Mock OpenAI client
        self.mock_openai = MagicMock()
        self.sdk = ChronosGraphSDK(self.db_path, openai_client=self.mock_openai)
        
        # Setup mock response for embeddings
        mock_embedding_data = MagicMock()
        mock_embedding_data.embedding = [0.1] * 1536
        self.mock_openai.embeddings.create.return_value.data = [mock_embedding_data]

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_entity_deduplication(self):
        """Test that adding the same entity twice returns the same ID and doesn't create a duplicate."""
        agent_id = self.sdk.initialize_agent("DedupeAgent")
        
        # Add entity first time
        entity_id_1 = self.sdk.add_knowledge(agent_id, "ChronosGraph", "A memory database.", "software")
        
        # Add entity second time (with same name)
        entity_id_2 = self.sdk.add_knowledge(agent_id, "ChronosGraph", "A different description.", "software")
        
        self.assertEqual(entity_id_1, entity_id_2)
        
        # Verify only one entity exists in DB
        import sqlite3
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM entities WHERE agent_id = ? AND name = ?", (agent_id, "ChronosGraph"))
            count = cursor.fetchone()[0]
            self.assertEqual(count, 1)

if __name__ == "__main__":
    unittest.main()
