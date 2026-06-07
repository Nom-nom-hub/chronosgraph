import sqlite3
from .logger import logger
from .exceptions import DatabaseError

class MigrationManager:
    """
    Handles database schema versioning and migrations for ChronosGraph.
    """
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._ensure_migration_table()

    def _ensure_migration_table(self):
        """Creates the migrations table if it doesn't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS migrations (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        version INTEGER NOT NULL UNIQUE,
                        applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
        except sqlite3.Error as e:
            logger.error(f"Failed to ensure migrations table: {e}", extra={"error_type": "DatabaseError"})
            raise DatabaseError(e) from e

    def get_current_version(self) -> int:
        """Returns the current database schema version."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT MAX(version) FROM migrations")
                row = cursor.fetchone()
                return row[0] if row and row[0] is not None else 0
        except sqlite3.Error as e:
            logger.error(f"Failed to get current schema version: {e}", extra={"error_type": "DatabaseError"})
            raise DatabaseError(e) from e

    def apply_migrations(self):
        """Applies all pending migrations in order."""
        current_version = self.get_current_version()
        logger.info(f"Current database version: {current_version}")

        migrations = [
            (1, self._migration_v1, "Initial schema creation"),
            (2, self._migration_v2, "Strategic indexing for performance"),
            (3, self._migration_v3, "Multi-agent sharing and visibility controls"),
        ]

        for version, migration_func, description in migrations:
            if version > current_version:
                logger.info(f"Applying migration v{version}: {description}")
                try:
                    migration_func()
                    self._record_migration(version)
                    logger.info(f"Successfully applied migration v{version}")
                except Exception as e:
                    logger.error(f"Failed to apply migration v{version}: {e}", extra={"version": version, "error_type": "MigrationError"})
                    raise DatabaseError(f"Migration v{version} failed: {e}") from e

    def _record_migration(self, version: int):
        """Records a successful migration in the database."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO migrations (version) VALUES (?)", (version,))
            conn.commit()

    def _migration_v1(self):
        """Initial schema creation (v1)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Create Agents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE,
                    description TEXT,
                    shared_group TEXT
                )
            """)
            # Create Episodes table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS episodes (
                    episode_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    type TEXT NOT NULL,
                    content TEXT NOT NULL,
                    embedding BLOB,
                    tool_name TEXT,
                    tool_input TEXT,
                    tool_output TEXT,
                    success BOOLEAN,
                    parent_episode_id TEXT,
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id),
                    FOREIGN KEY (parent_episode_id) REFERENCES episodes(episode_id)
                )
            """)
            # Create Entities table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS entities (
                    entity_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    name TEXT NOT NULL,
                    type TEXT NOT NULL,
                    description TEXT,
                    embedding BLOB,
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)
            # Create Relationships table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS relationships (
                    relationship_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    type TEXT NOT NULL,
                    strength REAL,
                    timestamp TEXT NOT NULL,
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)
            conn.commit()

    def _migration_v2(self):
        """Strategic indexing for performance (v2)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Episodes indexing
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_episodes_agent_timestamp ON episodes (agent_id, timestamp DESC)")
            
            # Entities indexing
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_entities_agent_name ON entities (agent_id, name)")
            
            # Relationships indexing
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_relationships_agent_source ON relationships (agent_id, source_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_relationships_agent_target ON relationships (agent_id, target_id)")
            
            conn.commit()

    def _migration_v3(self):
        """Multi-agent sharing and visibility controls (v3)."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # Add visibility column to entities
            # 0: Private (Agent only), 1: Shared (Group only), 2: Public (All agents)
            try:
                cursor.execute("ALTER TABLE entities ADD COLUMN visibility INTEGER DEFAULT 0")
            except sqlite3.OperationalError:
                pass # Column might already exist
            
            # Add owner_agent_id to entities to track original creator in shared contexts
            try:
                cursor.execute("ALTER TABLE entities ADD COLUMN owner_agent_id TEXT")
            except sqlite3.OperationalError:
                pass
            
            # Add permissions table for granular control
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS permissions (
                    permission_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    resource_type TEXT NOT NULL, -- 'entity', 'episode', 'group'
                    resource_id TEXT NOT NULL,
                    can_read BOOLEAN DEFAULT 1,
                    can_write BOOLEAN DEFAULT 0,
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)
            
            conn.commit()
