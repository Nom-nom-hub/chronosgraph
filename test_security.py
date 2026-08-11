import unittest
import os
from .chronosgraph_engine import ChronosGraphEngine

class TestSecurity(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_security.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.engine = ChronosGraphEngine(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_invalid_agent_id(self):
        """Test that invalid agent IDs are rejected."""
        with self.assertRaises(ValueError):
            self.engine.get_agent("not-a-uuid")

    def test_invalid_agent_name(self):
        """Test that names with suspicious characters are rejected."""
        with self.assertRaises(ValueError):
            self.engine.register_agent("Agent; DROP TABLE agents;")

    def test_long_name(self):
        """Test that excessively long names are rejected."""
        with self.assertRaises(ValueError):
            self.engine.register_agent("A" * 256)

if __name__ == "__main__":
    unittest.main()
