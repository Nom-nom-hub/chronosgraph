# ChronosGraph: An Episodic and Relational Memory Layer for AI Agents

## 1. Introduction

ChronosGraph is envisioned as a universal, plug-and-play memory layer designed to overcome the limitations of current AI agent memory systems. Unlike traditional databases that merely store raw data, ChronosGraph focuses on capturing the **trajectories** of AI agents—their actions, observations, thoughts, tool usage, and outcomes (success or failure). This rich, contextualized storage enables agents to learn from their past experiences, reason more effectively, and exhibit more intelligent behavior over time. The goal is to create a system that is 100% useful and perceived as essential by developers building sophisticated AI agents.

## 2. Architectural Overview: A Hybrid Approach

ChronosGraph adopts a hybrid architectural approach, combining the strengths of relational databases, vector databases, and graph databases. This allows for flexible storage and retrieval of different types of agent memory:

*   **Relational Storage (SQLite)**: For structured metadata, agent configurations, and explicit episodic data (e.g., timestamps, agent IDs, episode types).
*   **Vector Storage**: For semantic understanding and retrieval of observations, thoughts, and actions. Embeddings of these elements will enable similarity-based search and contextual recall.
*   **Graph Storage**: To represent the complex relationships between episodes, entities, and agents. This allows for reasoning over interconnected experiences, identifying causal links, and understanding dependencies.

This hybrid model ensures that ChronosGraph can support both precise, factual recall and nuanced, context-aware retrieval, addressing the shortcomings of single-paradigm memory systems [1] [2].

## 3. Data Model

The core data model revolves around `Episodes`, `Entities`, and `Relationships`.

### 3.1. Episode

An `Episode` represents a discrete unit of an agent's experience or interaction. Each episode captures a snapshot of the agent's state and its interaction with the environment.

| Field Name      | Type     | Description                                                                 | Example                                                              |
| :-------------- | :------- | :-------------------------------------------------------------------------- | :------------------------------------------------------------------- |
| `episode_id`    | UUID     | Unique identifier for the episode.                                          | `a1b2c3d4-e5f6-7890-1234-567890abcdef`                               |
| `agent_id`      | UUID     | Identifier of the agent that experienced this episode.                      | `agent_alpha`                                                        |
| `timestamp`     | DATETIME | UTC timestamp of when the episode occurred.                                 | `2026-06-03T10:30:00Z`                                               |
| `type`          | ENUM     | Type of episode (e.g., `action`, `observation`, `thought`, `tool_use`).     | `action`                                                             |
| `content`       | TEXT     | The main textual content of the episode (e.g., agent's thought, observation). | `User requested to find current weather in London.`                  |
| `embedding`     | BLOB     | Vector embedding of the `content` for semantic search.                      | `[0.123, 0.456, ..., 0.789]`                                         |
| `tool_name`     | TEXT     | (Optional) Name of the tool used in this episode.                           | `weather_api`                                                        |
| `tool_input`    | TEXT     | (Optional) Input provided to the tool.                                      | `{"location": "London"}`                                         |
| `tool_output`   | TEXT     | (Optional) Output received from the tool.                                   | `{"temperature": "15C", "conditions": "cloudy"}`               |
| `success`       | BOOLEAN  | (Optional) Indicates if the episode (e.g., tool use) was successful.        | `True`                                                               |
| `parent_episode_id` | UUID     | (Optional) Link to a preceding episode in a sequence.                       | `f1e2d3c4-b5a6-0987-6543-210fedcba987`                               |

### 3.2. Entity

An `Entity` represents a significant concept, object, or actor identified within one or more episodes. Entities provide a way to connect disparate experiences.

| Field Name      | Type     | Description                                                                 | Example                                                              |
| :-------------- | :------- | :-------------------------------------------------------------------------- | :------------------------------------------------------------------- |
| `entity_id`     | UUID     | Unique identifier for the entity.                                           | `entity_london_weather`                                              |
| `agent_id`      | UUID     | Identifier of the agent that identified or interacted with this entity.     | `agent_alpha`                                                        |
| `name`          | TEXT     | Human-readable name of the entity.                                          | `London Weather`                                                     |
| `type`          | ENUM     | Category of the entity (e.g., `location`, `person`, `concept`, `tool`).     | `location`                                                           |
| `description`   | TEXT     | A brief description or summary of the entity.                               | `Current weather conditions and forecast for London.`                |
| `embedding`     | BLOB     | Vector embedding of the `name` and `description`.                           | `[0.987, 0.654, ..., 0.321]`                                         |

### 3.3. Relationship

A `Relationship` defines a directed connection between two entities or an entity and an episode, forming the graph structure. This allows for contextual retrieval and complex reasoning.

| Field Name      | Type     | Description                                                                 | Example                                                              |
| :-------------- | :------- | :-------------------------------------------------------------------------- | :------------------------------------------------------------------- |
| `relationship_id` | UUID     | Unique identifier for the relationship.                                     | `rel_12345`                                                          |
| `agent_id`      | UUID     | Identifier of the agent that established this relationship.                 | `agent_alpha`                                                        |
| `source_id`     | UUID     | UUID of the source (Episode or Entity).                                     | `a1b2c3d4-e5f6-7890-1234-567890abcdef` (episode)                     |
| `target_id`     | UUID     | UUID of the target (Episode or Entity).                                     | `entity_london_weather`                                              |
| `type`          | ENUM     | Type of relationship (e.g., `CAUSED_BY`, `MENTIONS`, `USED_TOOL`, `HAS_OUTCOME`). | `MENTIONS`                                                           |
| `strength`      | FLOAT    | (Optional) A numerical value indicating the strength or confidence of the relationship. | `0.85`                                                               |
| `timestamp`     | DATETIME | UTC timestamp of when the relationship was established or observed.         | `2026-06-03T10:30:05Z`                                               |

## 4. Schema Design (SQLite)

For Part 1, we will use SQLite for its simplicity, serverless nature, and ease of integration. It can effectively handle the relational aspects and store embeddings as BLOBs. Graph relationships will be managed through explicit tables.

```sql
-- Table for Episodes
CREATE TABLE IF NOT EXISTS episodes (
    episode_id TEXT PRIMARY KEY, -- UUID as TEXT
    agent_id TEXT NOT NULL,
    timestamp TEXT NOT NULL, -- ISO 8601 format
    type TEXT NOT NULL, -- ENUM: 'action', 'observation', 'thought', 'tool_use'
    content TEXT NOT NULL,
    embedding BLOB, -- Stored as a serialized vector (e.g., numpy array bytes)
    tool_name TEXT,
    tool_input TEXT,
    tool_output TEXT,
    success BOOLEAN,
    parent_episode_id TEXT,
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id),
    FOREIGN KEY (parent_episode_id) REFERENCES episodes(episode_id)
);

-- Table for Entities
CREATE TABLE IF NOT EXISTS entities (
    entity_id TEXT PRIMARY KEY, -- UUID as TEXT
    agent_id TEXT NOT NULL,
    name TEXT NOT NULL,
    type TEXT NOT NULL, -- ENUM: 'location', 'person', 'concept', 'tool', etc.
    description TEXT,
    embedding BLOB, -- Stored as a serialized vector
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
);

-- Table for Relationships
CREATE TABLE IF NOT EXISTS relationships (
    relationship_id TEXT PRIMARY KEY, -- UUID as TEXT
    agent_id TEXT NOT NULL,
    source_id TEXT NOT NULL, -- Can be episode_id or entity_id
    target_id TEXT NOT NULL, -- Can be episode_id or entity_id
    type TEXT NOT NULL, -- ENUM: 'CAUSED_BY', 'MENTIONS', 'USED_TOOL', 'HAS_OUTCOME', etc.
    strength REAL,
    timestamp TEXT NOT NULL, -- ISO 8601 format
    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
    -- No direct foreign key constraints for source_id/target_id due to mixed types (episode/entity)
    -- Application logic will ensure referential integrity
);

-- Table for Agents (to manage multiple agents using ChronosGraph)
CREATE TABLE IF NOT EXISTS agents (
    agent_id TEXT PRIMARY KEY, -- UUID as TEXT
    name TEXT NOT NULL UNIQUE,
    description TEXT
);
```

## 5. Universal API Specification

The API will be designed for simplicity and ease of integration, allowing agents to interact with ChronosGraph via a few core functions.

### 5.1. `chronosgraph.check_in(agent_id: str, episode_data: dict) -> str`

*   **Description**: Stores a new episode of an agent's experience into ChronosGraph. This function will automatically generate embeddings for `content` and `description` fields, and infer potential entities and relationships.
*   **Parameters**:
    *   `agent_id` (str): The unique identifier of the agent performing the check-in.
    *   `episode_data` (dict): A dictionary containing episode details, conforming to the `Episode` data model (e.g., `type`, `content`, `tool_name`, `tool_input`, `tool_output`, `success`, `parent_episode_id`).
*   **Returns**: `str` - The `episode_id` of the newly created episode.

### 5.2. `chronosgraph.recall(agent_id: str, query: str, context_type: str = 'semantic', limit: int = 5) -> list[dict]`

*   **Description**: Retrieves relevant past experiences or knowledge for an agent based on a query. Supports different types of recall.
*   **Parameters**:
    *   `agent_id` (str): The unique identifier of the agent requesting recall.
    *   `query` (str): The natural language query or context for retrieval.
    *   `context_type` (str, optional): The type of recall desired. Defaults to `'semantic'`.
        *   `'semantic'`: Retrieves episodes/entities semantically similar to the query (using vector search).
        *   `'episodic'`: Retrieves specific past episodes (e.g., by `episode_id` or `parent_episode_id`).
        *   `'relational'`: Retrieves entities/episodes connected via graph relationships to the query context.
    *   `limit` (int, optional): Maximum number of results to return. Defaults to 5.
*   **Returns**: `list[dict]` - A list of dictionaries, each representing a recalled episode or entity, including its type and relevant data.

### 5.3. `chronosgraph.query_graph(agent_id: str, graph_query: str) -> list[dict]`

*   **Description**: Allows for more complex querying of the relational graph, enabling agents to ask questions about connections, dependencies, and causal links between experiences and entities.
*   **Parameters**:
    *   `agent_id` (str): The unique identifier of the agent querying the graph.
    *   `graph_query` (str): A query string (e.g., a simplified graph query language or natural language query to be interpreted) to traverse the relationships.
*   **Returns**: `list[dict]` - A list of dictionaries representing the results of the graph query (e.g., paths, connected entities, or aggregated information).

## 6. Justification and Unique Benefits

ChronosGraph's hybrid design and focus on episodic and relational memory directly address key limitations in existing AI agent memory systems [3] [4]:

*   **Beyond Vector Search**: While vector databases are excellent for semantic similarity, they often lack the ability to capture the *why* and *how* of an agent's actions or the explicit relationships between different pieces of information. ChronosGraph augments semantic recall with structured episodic data and a relational graph, allowing for deeper contextual understanding and causal reasoning [5].
*   **Episodic Learning**: By storing full agent trajectories, ChronosGraph enables agents to learn from successes and failures, adapt strategies, and avoid repeating mistakes. This is crucial for developing truly autonomous and adaptive agents.
*   **Relational Reasoning**: The graph component allows agents to build a rich internal model of their environment and their interactions within it. They can identify patterns, infer new knowledge from relationships, and make more informed decisions.
*   **Plug-and-Play Universal API**: The simplified API ensures that ChronosGraph can be easily integrated into any agent framework (e.g., LangChain, LangGraph, custom agents) with minimal effort, making it a truly universal memory solution.
*   **Scalability (Future-Proof)**: While starting with SQLite for simplicity, the architectural design is modular, allowing for future upgrades to more robust relational databases (e.g., PostgreSQL), dedicated vector databases (e.g., Pinecone, Weaviate), and graph databases (e.g., Neo4j) as scalability requirements grow.

This design ensures ChronosGraph is not just a data store, but a foundational component for building more intelligent, adaptable, and self-improving AI agents.

## References

[1] [AI Agent Memory Systems in 2026: Mem0, Zep, Hindsight, Memvid and everything in between compared](https://blog.devgenius.io/ai-agent-memory-systems-in-2026-mem0-zep-hindsight-memvid-and-everything-in-between-compared-96e35b818da8)
[2] [The State of AI Agent Memory in 2026: What the Research Actually Shows](https://pub.towardsai.net/the-state-of-ai-agent-memory-in-2026-what-the-research-actually-shows-0b77063c2c2b)
[3] [Are vector databases fundamentally insufficient for long-term memory?](https://www.reddit.com/r/LocalLLaMA/comments/1r3w2jp/are_vector_databases_fundamentally_insufficient/)
[4] [Long-term Memory for AI Agents](https://ai.gopubby.com/long-term-memory-for-agentic-ai-systems-4ae9b37c6c0f)
[5] [Episodic Memory for AI Agents: How It Works](https://atlan.com/know/episodic-memory-ai-agents/)
