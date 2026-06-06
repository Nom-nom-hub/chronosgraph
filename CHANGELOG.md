# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
