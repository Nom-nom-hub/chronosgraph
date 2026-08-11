import os
import unittest
from unittest.mock import MagicMock
from .chronosgraph_sdk import ChronosGraphSDK

class TestSummarization(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_summarization.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        
        # Mock OpenAI client
        self.mock_openai = MagicMock()
        self.sdk = ChronosGraphSDK(self.db_path, openai_client=self.mock_openai)
        
        # Setup mock response for embeddings
        mock_embedding_data = MagicMock()
        mock_embedding_data.embedding = [0.1] * 1536
        self.mock_openai.embeddings.create.return_value.data = [mock_embedding_data]
        
        # Setup mock response for summarization
        mock_summary_response = MagicMock()
        mock_summary_response.choices[0].message.content = "This is a summary of past events."
        self.mock_openai.chat.completions.create.return_value = mock_summary_response
        
        # Setup mock response for fact extraction (needed for auto_extract=True)
        mock_fact_response = MagicMock()
        mock_fact_response.choices[0].message.content = '{"entities": [], "relationships": []}'
        # Note: We need to handle multiple calls to chat.completions.create
        self.mock_openai.chat.completions.create.side_effect = [mock_summary_response, mock_fact_response]

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_pruning_logic(self):
        """Test that get_context respects the max_episodes limit."""
        agent_id = self.sdk.initialize_agent("PruneAgent")
        
        # Add 10 episodes
        for i in range(10):
            self.sdk.check_in(agent_id, {"content": f"Episode {i}", "type": "observation"}, auto_extract=False)
            
        # Get context with limit 3
        context = self.sdk.get_context(agent_id, "query", max_episodes=3)
        
        # Count episodes in context (lines starting with "- ")
        episode_count = len([line for line in context.split('\n') if line.startswith("- ")])
        self.assertEqual(episode_count, 3)

    def test_summarization_workflow(self):
        """Test the full summarization and archiving workflow."""
        agent_id = self.sdk.initialize_agent("SummaryAgent")
        
        # Add 15 episodes
        for i in range(15):
            self.sdk.check_in(agent_id, {"content": f"Event {i}", "type": "event"}, auto_extract=False)
            
        # Summarize episodes older than 5
        summary_id = self.sdk.summarize_memory(agent_id, older_than_n_episodes=5)
        
        self.assertTrue(summary_id != "")
        
        # Verify that 10 episodes were archived (15 total - 5 recent = 10 old)
        episodes = self.sdk.engine.get_episodes(agent_id, limit=100, include_archived=False)
        # 5 recent episodes + 1 summary episode = 6 active episodes
        self.assertEqual(len(episodes), 6)
        
        # Verify the summary content is present
        self.assertTrue(any("SUMMARY of previous events" in ep['content'] for ep in episodes))

if __name__ == "__main__":
    unittest.main()
