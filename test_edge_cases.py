import os
import unittest
import sqlite3
from unittest.mock import MagicMock
from .chronosgraph_sdk import ChronosGraphSDK
from .exceptions import AgentNotFoundError, InvalidEpisodeDataError

class TestEdgeCases(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_edge_cases.db"
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

    def test_invalid_agent_operations(self):
        """Test operations on non-existent agents."""
        with self.assertRaises(AgentNotFoundError):
            self.sdk.check_in("non-existent-id", {"content": "hello"})
        
        with self.assertRaises(AgentNotFoundError):
            self.sdk.recall("non-existent-id", "query")

    def test_malformed_episode_data(self):
        """Test check-in with malformed data."""
        agent_id = self.sdk.initialize_agent("EdgeAgent")
        with self.assertRaises(InvalidEpisodeDataError):
            self.sdk.check_in(agent_id, {"wrong_key": "no content here"})

    def test_large_volume_episodes(self):
        """Test handling of a large number of episodes."""
        agent_id = self.sdk.initialize_agent("VolumeAgent")
        # Add 100 episodes
        for i in range(100):
            self.sdk.check_in(agent_id, {"content": f"Episode content {i}"}, auto_extract=False)
        
        episodes = self.sdk.recall(agent_id, "", context_type='episodic', limit=100)
        self.assertEqual(len(episodes), 100)
        # Verify order (most recent first)
        self.assertEqual(episodes[0]['content'], "Episode content 99")

    def test_very_long_content(self):
        """Test handling of extremely long content strings."""
        agent_id = self.sdk.initialize_agent("LongAgent")
        long_content = "A" * 100000 # 100KB string
        episode_id = self.sdk.check_in(agent_id, {"content": long_content}, auto_extract=False)
        
        results = self.sdk.recall(agent_id, "", context_type='episodic', limit=1)
        self.assertEqual(results[0]['content'], long_content)

if __name__ == "__main__":
    unittest.main()
