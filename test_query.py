import os
import unittest
from unittest.mock import MagicMock, patch
from .chronosgraph_sdk import ChronosGraphSDK

class TestQueryEngine(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_query.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        
        # Mock OpenAI
        self.mock_openai = MagicMock()
        self.sdk = ChronosGraphSDK(self.db_path, openai_client=self.mock_openai)
        
        # Mock Embedding Response
        mock_embedding_data = MagicMock()
        mock_embedding_data.embedding = [0.1] * 1536
        self.mock_openai.embeddings.create.return_value.data = [mock_embedding_data]

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    @patch('chronosgraph.query_engine.QueryEngine._parse_query')
    def test_ask_interface(self, mock_parse):
        """Test the high-level ask interface in the SDK."""
        agent_id = self.sdk.initialize_agent("QueryAgent")
        
        # Mock LLM Plan
        mock_parse.return_value = {
            "semantic_search": True,
            "graph_traversal": True,
            "target_entity": "London",
            "semantic_query": "weather in London",
            "semantic_search_required": True
        }
        
        # Add some data to avoid EntityNotFoundError
        self.sdk.add_knowledge(agent_id, "London", "A city", type="location")
        
        # Call ask
        response = self.sdk.ask(agent_id, "What's the weather in London?")
        
        # Verify response
        self.assertIn("semantic_results", response)
        self.assertIn("graph_context", response)
        self.assertEqual(response["plan"]["target_entity"], "London")

if __name__ == "__main__":
    unittest.main()
