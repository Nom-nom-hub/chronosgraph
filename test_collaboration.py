import os
import unittest
from unittest.mock import MagicMock
from .chronosgraph_sdk import ChronosGraphSDK

class TestCollaboration(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_collaboration.db"
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

    def test_visibility_levels(self):
        """Test that entities respect visibility levels across agents."""
        agent_a = self.sdk.initialize_agent("AgentA")
        agent_b = self.sdk.initialize_agent("AgentB")
        
        # Agent A adds a private entity
        self.sdk.add_knowledge(agent_a, "PrivateInfo", "Secret A", visibility=0)
        
        # Agent A adds a shared entity
        self.sdk.add_knowledge(agent_a, "SharedInfo", "Common Knowledge", visibility=1)
        
        # Agent B tries to get context for PrivateInfo (should fail)
        from .exceptions import EntityNotFoundError
        with self.assertRaises(EntityNotFoundError):
            self.sdk.engine.get_graph_context(agent_b, "PrivateInfo")
            
        # Agent B tries to get context for SharedInfo (should succeed because visibility >= 1)
        context = self.sdk.engine.get_graph_context(agent_b, "SharedInfo")
        # Note: Even if it succeeds, there might be no relationships yet, but it shouldn't raise EntityNotFoundError
        self.assertEqual(len(context), 0)

    def test_shared_group_recall(self):
        """Test recall within a shared group."""
        group = "collab_group"
        agent_a = self.sdk.initialize_agent("AgentA", shared_group=group)
        agent_b = self.sdk.initialize_agent("AgentB", shared_group=group)
        
        # Agent A records an episode
        self.sdk.check_in(agent_a, {"content": "Project X is launching tomorrow.", "type": "news"}, auto_extract=False)
        
        # Agent B recalls
        results = self.sdk.recall(agent_b, "Project X", context_type='semantic', include_shared=True)
        self.assertTrue(any("Project X" in r['content'] for r in results))
        self.assertTrue(any(r['agent_name'] == 'AgentA' for r in results))

if __name__ == "__main__":
    unittest.main()
