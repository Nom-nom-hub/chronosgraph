# ChronosGraph v1.0 🛡️

**ChronosGraph** is a high-performance, professional-grade agentic memory system that combines **Episodic Memory** (time-series events) with a **Knowledge Graph** (semantic entities and relationships). It is designed to make AI agents more robust, observable, and collaborative.

## Key Features

- **Hybrid Memory Architecture**: Seamlessly integrates SQLite-based relational storage with vectorized semantic search.
- **Advanced NL Query Language**: Ask your memory questions in natural language.
- **Multi-Agent Collaboration**: Secure knowledge sharing with granular visibility controls (`Private`, `Shared`, `Public`).
- **Intelligent Pruning & Summarization**: Prevents context window overflow through LLM-powered memory condensation.
- **Graph Visualization**: Export and view your agent's knowledge graph using Mermaid.js.
- **Production Ready**: Built-in migrations, structured logging, and comprehensive input validation.

## Quick Start

### Installation

```bash
pip install -r requirements.txt
```

### Basic Usage

```python
from chronosgraph.chronosgraph_sdk import ChronosGraphSDK

# Initialize SDK
sdk = ChronosGraphSDK("memory.db")

# Register your agent
agent_id = sdk.initialize_agent("ResearchAgent")

# Store a memory
sdk.check_in(agent_id, {
    "content": "ChronosGraph v1.0 has been released!",
    "type": "news"
})

# Recall context for a task
context = sdk.get_context(agent_id, "What happened recently?")
print(context)

# Ask a natural language question
answer = sdk.ask(agent_id, "When was the new version released?")
```

## Documentation

- **SDK API**: See `chronosgraph_sdk.py` for full method documentation.
- **Tutorial**: Run `python tutorial.py` for a complete walkthrough.
- **Roadmap**: See `ROADMAP.md` for the project's evolution and future plans.

## Security

ChronosGraph implements strict input validation and parameterized queries to protect against common vulnerabilities. For security concerns, please refer to `SECURITY.md`.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.
