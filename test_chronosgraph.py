import os
import sqlite3
import unittest
from unittest.mock import MagicMock

import numpy as np

from .chronosgraph_engine import ChronosGraphEngine
from .chronosgraph_sdk import ChronosGraphSDK
from .exceptions import (
    AgentNotFoundError,
    DatabaseError,
    EpisodeNotFoundError,
    EntityNotFoundError,
    RelationshipNotFoundError,
    InvalidEpisodeDataError,
    EmbeddingGenerationError,
    FactExtractionError
)


class TestChronosGraph(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_chronosgraph.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.engine = ChronosGraphEngine(self.db_path)
        
        # Mock OpenAI client
        self.mock_openai = MagicMock()
        self.sdk = ChronosGraphSDK(self.db_path, openai_client=self.mock_openai)
        
        # Setup mock response for embeddings
        mock_embedding_data = MagicMock()
        mock_embedding_data.embedding = [0.1] * 1536
        self.mock_openai.embeddings.create.return_value.data = [mock_embedding_data]
        
        # Setup mock response for fact extraction
        mock_chat_response = MagicMock()
        mock_chat_response.choices[0].message.content = '{"entities": [{"name": "TestEntity", "type": "concept", "description": "test"}], "relationships": []}'
        self.mock_openai.chat.completions.create.return_value = mock_chat_response

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_01_register_agent(self):
        agent_id = self.engine.register_agent("TestAgent1", "A test agent.")
        self.assertIsNotNone(agent_id)
        self.assertTrue(isinstance(agent_id, str))

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM agents WHERE agent_id = ?", (agent_id,))
            agent = cursor.fetchone()
            self.assertIsNotNone(agent)
            self.assertEqual(agent[1], "TestAgent1") # name

    def test_02_add_episode(self):
        agent_id = self.engine.register_agent("TestAgent2")
        episode_data = {
            "type": "thought",
            "content": "This is a test thought.",
            "embedding": [0.1, 0.2, 0.3]
        }
        episode_id = self.engine.add_episode(agent_id, episode_data)
        self.assertIsNotNone(episode_id)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM episodes WHERE episode_id = ?", (episode_id,))
            episode = cursor.fetchone()
            self.assertIsNotNone(episode)
            self.assertEqual(episode["agent_id"], agent_id)
            self.assertEqual(episode["content"], "This is a test thought.")
            retrieved_embedding = np.frombuffer(episode["embedding"], dtype=np.float32).tolist()
            self.assertTrue(np.allclose(retrieved_embedding, [0.1, 0.2, 0.3]))

    def test_03_add_entity(self):
        agent_id = self.engine.register_agent("TestAgent3")
        entity_data = {
            "name": "TestEntity",
            "type": "concept",
            "description": "A concept for testing.",
            "embedding": [0.4, 0.5, 0.6]
        }
        entity_id = self.engine.add_entity(agent_id, entity_data)
        self.assertIsNotNone(entity_id)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM entities WHERE entity_id = ?", (entity_id,))
            entity = cursor.fetchone()
            self.assertIsNotNone(entity)
            self.assertEqual(entity["name"], "TestEntity")
            retrieved_embedding = np.frombuffer(entity["embedding"], dtype=np.float32).tolist()
            self.assertTrue(np.allclose(retrieved_embedding, [0.4, 0.5, 0.6]))

    def test_04_add_relationship(self):
        agent_id = self.engine.register_agent("TestAgent4")
        episode_id = self.engine.add_episode(agent_id, {"type": "action", "content": "action1"})
        entity_id = self.engine.add_entity(agent_id, {"name": "entity1", "type": "concept"})
        
        rel_data = {
            "source_id": episode_id,
            "target_id": entity_id,
            "type": "MENTIONS",
            "strength": 0.9
        }
        relationship_id = self.engine.add_relationship(agent_id, rel_data)
        self.assertIsNotNone(relationship_id)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM relationships WHERE relationship_id = ?", (relationship_id,))
            relationship = cursor.fetchone()
            self.assertIsNotNone(relationship)
            self.assertEqual(relationship["source_id"], episode_id)
            self.assertEqual(relationship["target_id"], entity_id)
            self.assertEqual(relationship["type"], "MENTIONS")
            self.assertEqual(relationship["strength"], 0.9)

    def test_05_get_episodes(self):
        agent_id = self.engine.register_agent("TestAgent5")
        self.engine.add_episode(agent_id, {"type": "thought", "content": "thought1"})
        self.engine.add_episode(agent_id, {"type": "thought", "content": "thought2"})
        episodes = self.engine.get_episodes(agent_id, limit=1)
        self.assertEqual(len(episodes), 1)
        self.assertEqual(episodes[0]["content"], "thought2") # Should be the latest

    def test_06_semantic_search(self):
        agent_id = self.engine.register_agent("TestAgent6")
        self.engine.add_episode(agent_id, {"type": "thought", "content": "apple", "embedding": [1.0, 0.0, 0.0]})
        self.engine.add_episode(agent_id, {"type": "thought", "content": "banana", "embedding": [0.0, 1.0, 0.0]})
        self.engine.add_episode(agent_id, {"type": "thought", "content": "orange", "embedding": [0.9, 0.1, 0.0]})

        # Search for something similar to apple
        results = self.engine.semantic_search(agent_id, [1.0, 0.0, 0.0], limit=1)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["content"], "apple")
        self.assertAlmostEqual(results[0]["similarity"], 1.0)

        results = self.engine.semantic_search(agent_id, [0.9, 0.1, 0.0], limit=2)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["content"], "orange")
        self.assertEqual(results[1]["content"], "apple")

    def test_07_sdk_check_in(self):
        agent_id = self.sdk.initialize_agent("SDKAgent1")
        episode_id = self.sdk.check_in(agent_id, {"type": "action", "content": "SDK action."})
        self.assertIsNotNone(episode_id)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM episodes WHERE episode_id = ?", (episode_id,))
            episode = cursor.fetchone()
            self.assertIsNotNone(episode)
            self.assertEqual(episode["content"], "SDK action.")
            self.assertIsNotNone(episode["embedding"]) # Should have been generated

    def test_08_sdk_recall_semantic(self):
        agent_id = self.sdk.initialize_agent("SDKAgent2")
        # Manually set distinct embeddings for testing semantic recall
        self.engine.add_episode(agent_id, {
            "type": "thought", "content": "I like apples.", "embedding": [1.0, 0.1, 0.1]
        })
        self.engine.add_episode(agent_id, {
            "type": "thought", "content": "I prefer bananas.", "embedding": [0.1, 1.0, 0.1]
        })
        self.engine.add_episode(agent_id, {
            "type": "thought", "content": "Oranges are citrus.", "embedding": [0.1, 0.1, 1.0]
        })

        # Query embedding for "fruits like apples" should be closer to the "apples" embedding
        query_embedding_for_apples = [0.9, 0.0, 0.0] # Simulating a query for apples
        
        # Temporarily override the SDK's _generate_embedding for this test to use our custom query embedding
        original_generate_embedding = self.sdk._generate_embedding
        self.sdk._generate_embedding = lambda text: query_embedding_for_apples # This will be used for the query

        results = self.sdk.recall(agent_id, "fruits like apples", context_type="semantic", limit=1)
        self.assertEqual(len(results), 1)
        self.assertIn("apples", results[0]["content"].lower())

        # Restore original _generate_embedding
        self.sdk._generate_embedding = original_generate_embedding

    def test_09_sdk_get_context(self):
        agent_id = self.sdk.initialize_agent("SDKAgent3")
        self.sdk.check_in(agent_id, {"type": "thought", "content": "First thought for context."})
        self.sdk.check_in(agent_id, {"type": "action", "content": "Second action for context."})

        context = self.sdk.get_context(agent_id, "What did I do recently?")
        self.assertIn("Relevant past experiences (including shared knowledge):", context)
        self.assertIn("First thought for context.", context)
        self.assertIn("Second action for context.", context)

    def test_10_sdk_add_knowledge_and_relate(self):
        agent_id = self.sdk.initialize_agent("SDKAgent4")
        episode_id = self.sdk.check_in(agent_id, {"type": "observation", "content": "Observed a red apple."})
        entity_id = self.sdk.add_knowledge(agent_id, "Apple", "A common fruit.", "fruit")
        self.sdk.relate(agent_id, episode_id, entity_id, "MENTIONS")

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM relationships WHERE source_id = ? AND target_id = ?", (episode_id, entity_id))
            rel = cursor.fetchone()
            self.assertIsNotNone(rel)
            self.assertEqual(rel["type"], "MENTIONS")

    def test_11_error_handling_agent_not_found(self):
        with self.assertRaises(AgentNotFoundError):
            self.engine.get_agent("non_existent_id")

    def test_12_error_handling_invalid_episode_data(self):
        agent_id = self.engine.register_agent("ErrorAgent1")
        with self.assertRaises(InvalidEpisodeDataError):
            self.engine.add_episode(agent_id, {"wrong_key": "data"})

    def test_13_error_handling_embedding_generation_failure(self):
        # Mock embedding generation failure
        self.mock_openai.embeddings.create.side_effect = Exception("OpenAI Error")
        agent_id = self.sdk.initialize_agent("ErrorAgent2")
        with self.assertRaises(EmbeddingGenerationError):
            self.sdk.check_in(agent_id, {"content": "some content"})

    def test_14_error_handling_fact_extraction_failure(self):
        # Mock fact extraction failure
        self.mock_openai.chat.completions.create.side_effect = Exception("LLM Error")
        agent_id = self.sdk.initialize_agent("ErrorAgent3")
        with self.assertRaises(FactExtractionError):
            self.sdk.check_in(agent_id, {"content": "some content"}, auto_extract=True)

if __name__ == "__main__":
    unittest.main(argv=["first-arg-is-ignored"], exit=False)
