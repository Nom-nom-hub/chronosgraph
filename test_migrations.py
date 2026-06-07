import os
import sqlite3
import unittest
from .migrations import MigrationManager
from .exceptions import DatabaseError

class TestMigrations(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_migrations.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_migration_table_creation(self):
        """Test that the migrations table is created correctly."""
        manager = MigrationManager(self.db_path)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='migrations'")
            self.assertIsNotNone(cursor.fetchone())

    def test_apply_migrations(self):
        """Test applying all migrations up to v3."""
        manager = MigrationManager(self.db_path)
        manager.apply_migrations()
        
        self.assertEqual(manager.get_current_version(), 3)
        
        # Verify tables from v1 exist
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            for table in ["agents", "episodes", "entities", "relationships", "permissions"]:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'")
                self.assertIsNotNone(cursor.fetchone(), f"Table {table} should exist after migrations")
            
            # Verify indexes from v2 exist
            for index in ["idx_episodes_agent_timestamp", "idx_entities_agent_name", "idx_relationships_agent_source", "idx_relationships_agent_target"]:
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='index' AND name='{index}'")
                self.assertIsNotNone(cursor.fetchone(), f"Index {index} should exist after v2 migration")
            
            # Verify columns from v3 exist
            cursor.execute("PRAGMA table_info(entities)")
            columns = [row[1] for row in cursor.fetchall()]
            self.assertIn("visibility", columns)
            self.assertIn("owner_agent_id", columns)

    def test_idempotent_migrations(self):
        """Test that applying migrations multiple times doesn't cause errors."""
        manager = MigrationManager(self.db_path)
        manager.apply_migrations()
        version_after_first = manager.get_current_version()
        
        manager.apply_migrations()
        version_after_second = manager.get_current_version()
        
        self.assertEqual(version_after_first, version_after_second)
        self.assertEqual(version_after_first, 3)

if __name__ == "__main__":
    unittest.main()
