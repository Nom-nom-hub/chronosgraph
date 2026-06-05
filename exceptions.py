class ChronosGraphError(Exception):
    """Base exception for ChronosGraph errors."""
    pass

class AgentNotFoundError(ChronosGraphError):
    """Raised when an agent with the given ID is not found."""
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        super().__init__(f"Agent with ID '{agent_id}' not found.")

class EpisodeNotFoundError(ChronosGraphError):
    """Raised when an episode with the given ID is not found."""
    def __init__(self, episode_id: str):
        self.episode_id = episode_id
        super().__init__(f"Episode with ID '{episode_id}' not found.")

class EntityNotFoundError(ChronosGraphError):
    """Raised when an entity with the given ID is not found."""
    def __init__(self, entity_id: str):
        self.entity_id = entity_id
        super().__init__(f"Entity with ID '{entity_id}' not found.")

class RelationshipNotFoundError(ChronosGraphError):
    """Raised when a relationship with the given ID is not found."""
    def __init__(self, relationship_id: str):
        self.relationship_id = relationship_id
        super().__init__(f"Relationship with ID '{relationship_id}' not found.")

class InvalidEpisodeDataError(ChronosGraphError):
    """Raised when episode data is missing required fields or is invalid."""
    def __init__(self, message: str = "Invalid episode data provided."):
        super().__init__(message)

class EmbeddingGenerationError(ChronosGraphError):
    """Raised when there is an error generating embeddings."""
    def __init__(self, original_error: Exception):
        self.original_error = original_error
        super().__init__(f"Error generating embedding: {original_error}")

class DatabaseError(ChronosGraphError):
    """Raised for database-related errors."""
    def __init__(self, original_error: Exception):
        self.original_error = original_error
        super().__init__(f"Database operation failed: {original_error}")

class FactExtractionError(ChronosGraphError):
    """Raised when there is an error extracting facts from text."""
    def __init__(self, message: str):
        super().__init__(message)
