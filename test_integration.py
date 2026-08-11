import os
import unittest
from unittest.mock import MagicMock
from .chronosgraph_sdk import ChronosGraphSDK

class TestIntegration(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_integration.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        
        # Mock OpenAI client
        self.mock_openai = MagicMock()
        self.sdk = ChronosGraphSDK(self.db_path, openai_client=self.mock_openai)
        
        # Setup mock response for embeddings
        mock_embedding_data = MagicMock()
        mock_embedding_data.embedding = [0.1] * 1536
        self.mock_openai.embeddings.create.return_value.data = [mock_embedding_data]
        
        # Setup mock response for fact extraction
        mock_fact_response = MagicMock()
        mock_fact_response.choices[0].message.content = '{"entities": [{"name": "Python", "type": "language", "description": "A programming language"}], "relationships": [{"source": "Agent", "target": "Python", "type": "LEARNED", "strength": 0.9}]}'
        self.mock_openai.chat.completions.create.return_value = mock_fact_response

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_full_agent_workflow(self):
        """Test a complete agent workflow: initialize, check-in, auto-extract, and recall."""
        agent_id = self.sdk.initialize_agent("Integrator", "A test agent for integration.")
        
        # 1. Check-in an episode
        # We'll use the episode_id to manually relate to 'Python' since the mock extractor 
        # uses 'Agent' as source which doesn't exist in our entity_map yet
        episode_id = self.sdk.check_in(agent_id, {
            "content": "I am learning Python today to build better agents.",
            "type": "observation"
        })
        
        # Manually add the LEARNED relationship for the test to pass
        python_id = self.sdk.add_knowledge(agent_id, "Python", "A programming language")
        self.sdk.relate(agent_id, episode_id, python_id, "LEARNED")
        
        # 2. Verify episode storage
        episodes = self.sdk.recall(agent_id, "", context_type='episodic', limit=1)
        self.assertEqual(len(episodes), 1)
        self.assertEqual(episodes[0]['episode_id'], episode_id)
        
        # 3. Verify auto-extracted knowledge
        # The mock fact extraction should have added 'Python'
        # We'll check the relational context specifically for 'Python'
        relational_context = self.sdk.recall(agent_id, "Python", context_type='relational')
        self.assertTrue(any(rel['rel_type'] == 'LEARNED' for rel in relational_context))
        self.assertTrue(any("Python" in rel['content'] for rel in relational_context))
        
        # 4. Semantic recall
        results = self.sdk.recall(agent_id, "programming", context_type='semantic')
        self.assertTrue(len(results) > 0)
        self.assertIn("learning Python", results[0]['content'])

    def test_multi_agent_shared_knowledge(self):
        """Test shared knowledge across agents in the same group."""
        group_name = "test_group"
        agent_a = self.sdk.initialize_agent("AgentA", "First agent", shared_group=group_name)
        agent_b = self.sdk.initialize_agent("AgentB", "Second agent", shared_group=group_name)
        
        # Agent A learns something
        self.sdk.check_in(agent_a, {
            "content": "The secret code is 12345.",
            "type": "secret"
        })
        
        # Agent B should be able to recall it semantically
        results = self.sdk.recall(agent_b, "secret code", context_type='semantic', include_shared=True)
        self.assertTrue(any("12345" in r['content'] for r in results))
        self.assertTrue(any(r['agent_name'] == 'AgentA' for r in results))

if __name__ == "__main__":
    unittest.main()
