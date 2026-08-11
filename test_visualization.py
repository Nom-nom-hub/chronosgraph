import os
import unittest
from unittest.mock import MagicMock
from .chronosgraph_sdk import ChronosGraphSDK

class TestVisualization(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_visualization.db"
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

    def test_mermaid_export(self):
        """Test that the Mermaid graph is exported correctly."""
        agent_id = self.sdk.initialize_agent("VizAgent")
        
        # Add an episode
        episode_id = self.sdk.check_in(agent_id, {"content": "Viz episode", "type": "thought"}, auto_extract=False)
        
        # Add an entity
        entity_id = self.sdk.add_knowledge(agent_id, "VizEntity", "A visual entity", type="object")
        
        # Add a relationship
        self.sdk.relate(agent_id, episode_id, entity_id, "OBSERVED")
        
        # Export Mermaid
        mermaid_str = self.sdk.visualize_graph(agent_id)
        
        # Verify Mermaid content
        self.assertIn("graph TD", mermaid_str)
        self.assertIn("Viz episode", mermaid_str)
        self.assertIn("VizEntity (object)", mermaid_str)
        self.assertIn("OBSERVED", mermaid_str)
        
        # Test saving to file
        output_file = "test_graph.mmd"
        self.sdk.visualize_graph(agent_id, output_file=output_file)
        self.assertTrue(os.path.exists(output_file))
        os.remove(output_file)

if __name__ == "__main__":
    unittest.main()
