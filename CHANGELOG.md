# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-08-11

### Added
- **v1.0.0 Production Release**: Reached the first major stable milestone for ChronosGraph.
- **Advanced NL Query Language**: Integrated a GPT-4o powered `QueryEngine` for natural language interaction with agent memory.
- **Security Hardening**: Implemented strict input validation, UUID verification, and name sanitization across the engine and SDK.
- **CI/CD Pipeline**: Added GitHub Actions workflow for automated testing on every push and pull request.
- **Comprehensive Documentation**: Updated README, added a professional tutorial, and finalized the SDK API documentation.
- **Vector Store Abstraction**: Introduced a pluggable `VectorStore` interface, decoupling the memory engine from specific implementations.
- **Local Vector Store**: Refactored the existing SQLite and NumPy-based similarity search into a dedicated `LocalVectorStore` class.
- **Scalability Architecture**: Added a scaffold for `PineconeVectorStore` for future high-performance integrations.

## [0.10.0] - 2026-08-11

### Added
- **Vector Store Abstraction**: Introduced a pluggable `VectorStore` interface in `vector_store.py`, decoupling the memory engine from specific vector database implementations.
- **Local Vector Store**: Refactored the existing SQLite and NumPy-based similarity search into a dedicated `LocalVectorStore` class.
- **Scalability Architecture**: Added a scaffold for `PineconeVectorStore`, providing a clear path for integrating high-performance external vector databases.
- **Engine Refactoring**: Updated `ChronosGraphEngine` to depend on the `VectorStore` abstraction, allowing users to swap memory backends during initialization.
- **Vector Store Testing**: Added `test_vector_store.py` to verify the delegation of semantic search and correct initialization of the vector store architecture.

## [0.9.0] - 2026-08-11

### Added
- **Graph Visualization Utility**: Implemented `export_mermaid_graph` in `ChronosGraphEngine` and `visualize_graph` in the SDK. This allows developers to export the agent's knowledge graph as a Mermaid.js diagram for debugging and analysis.
- **Interactive HTML Viewer**: Created a standalone HTML visualization tool that uses Mermaid.js to render agent memory graphs with zoom and pan capabilities, aiding in deep debugging.
- **Bi-directional Node Mapping**: Enhanced the visualization logic to include both entities and recent episodes, showing how experiences link to the knowledge graph.
- **Visualization Testing**: Added `test_visualization.py` to ensure correct Mermaid string generation and file export functionality.

## [0.8.0] - 2026-08-11

### Added
- **Intelligent Context Pruning**: Updated `get_context` in `ChronosGraphSDK` to include a `max_episodes` limit, preventing context window overflow by prioritizing relevant memories.
- **Memory Summarization**: Introduced `MemorySummarizer` and `summarize_memory` in the SDK to condense older episodes into concise summaries using LLMs.
- **Episode Archiving**: Added `archive_episodes` to `ChronosGraphEngine` and a new migration (v4) to support marking episodes as archived, keeping the active memory lean.
- **Summarization Testing**: Added `test_summarization.py` to verify the pruning, summarization, and archiving workflows.

## [0.7.0] - 2026-06-07

### Added
- **Multi-Agent Collaboration**: Introduced granular visibility controls (Private, Shared, Public) for entities, allowing agents to share knowledge securely.
- **Schema Migration (v3)**: Added `visibility` and `owner_agent_id` columns to the `entities` table and created a `permissions` table for future granular access control.
- **Enhanced Graph Context**: Updated `get_graph_context` to respect visibility levels, enabling agents to discover shared knowledge while protecting private information.
- **Collaboration Testing**: Added `test_collaboration.py` to verify knowledge sharing and visibility logic across multiple agents.

## [0.6.0] - 2026-06-07

### Added
- **Comprehensive Test Suite**: Added `test_integration.py` for end-to-end agent workflow verification and `test_edge_cases.py` for large volume and malformed data handling.
- **Bi-directional Graph Traversal**: Updated `get_graph_context` in `ChronosGraphEngine` to support bi-directional relationship lookups, improving the richness of retrieved context.
- **Integration Stability**: Verified the full system stability by running a consolidated suite of 30+ tests across multiple domains.

## [0.5.0] - 2026-06-06

### Added
- **Performance Optimization**: Implemented strategic SQL indexing in `migrations.py` (v2) for `episodes`, `entities`, and `relationships` tables to accelerate relational lookups.
- **Vectorized Similarity Search**: Optimized `semantic_search` in `ChronosGraphEngine` using vectorized NumPy operations, significantly improving search speed for large datasets.
- **Updated Migration Tests**: Refined `test_migrations.py` to verify the application of v2 migrations and index creation.

## [0.4.0] - 2026-06-06

### Added
- **Entity Deduplication**: Implemented `find_entity_by_name` in `ChronosGraphEngine` and integrated it into `ChronosGraphSDK.add_knowledge` to prevent redundant entity creation.
- **Refined Fact Extraction**: Updated the LLM prompt in `FactExtractor` to improve extraction accuracy, relationship precision, and provide explicit deduplication instructions to the model.
- **Deduplication Testing**: Added `test_deduplication.py` to ensure the new deduplication logic works as expected.

## [0.3.0] - 2026-06-05

### Added
- **Database Migration System**: Introduced `MigrationManager` in `migrations.py` to handle schema versioning and safe updates.
- **Automated Schema Initialization**: Integrated migrations into `ChronosGraphEngine` to ensure the database is always up-to-date upon initialization.
- **Migration Testing**: Added `test_migrations.py` to verify the idempotency and correctness of the migration engine.

## [0.2.0] - 2026-06-05

### Added
- **Structured Logging**: Implemented a JSON-based logging system in `logger.py` for better observability.
- **Custom Exceptions**: Added a comprehensive set of custom exceptions in `exceptions.py` to handle specific error cases (e.g., `AgentNotFoundError`, `DatabaseError`).
- **Robust Error Handling**: Integrated error catching and logging across `ChronosGraphEngine`, `ChronosGraphSDK`, and `FactExtractor`.
- **Enhanced Testing**: Added unit tests to verify error handling and logging functionality in `test_chronosgraph.py`.

## [0.1.0] - 2026-06-05

### Added
*   Initial release of ChronosGraph.
*   Core hybrid memory architecture with episodic, semantic, and relational capabilities.
*   Universal API for agent interaction (`check_in`, `recall`, `query_graph`).
*   SQLite-based persistence for episodes, entities, and relationships.
*   Basic fact extraction using LLMs.
*   Initial documentation (`README.md`).
