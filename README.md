# ChronosGraph: A Hybrid Memory Database for AI Agents

## Overview

ChronosGraph is an innovative memory database designed specifically for AI agents, offering a hybrid approach to long-term memory management. It combines the strengths of episodic memory, semantic recall, and relational knowledge graphs to provide agents with a comprehensive and deeply contextual understanding of their experiences and environment. Unlike traditional vector databases that primarily focus on semantic similarity, ChronosGraph enables agents to capture the 'why' and 'how' of their actions, fostering more intelligent, adaptable, and self-improving AI systems.

## Key Features

*   **Hybrid Memory Architecture**: Integrates episodic memory (detailed event logs), semantic memory (vector embeddings for similarity search), and relational memory (knowledge graph for contextual understanding).
*   **Episodic Learning**: Stores full agent trajectories, allowing agents to learn from past successes and failures, adapt strategies, and avoid repeating mistakes.
*   **Relational Reasoning**: Builds a rich internal model of the environment by capturing explicit relationships between experiences and entities, enabling deeper causal reasoning and informed decision-making.
*   **Plug-and-Play Universal API**: Provides a simplified and intuitive API for seamless integration with various AI agent frameworks (e.g., LangChain, LangGraph, custom agents).
*   **Scalability**: Designed with a modular architecture that supports future upgrades to more robust relational, vector, and graph databases as project needs evolve.

## Getting Started

### Installation

To get started with ChronosGraph, clone the repository and install the necessary dependencies:

```bash
git clone https://github.com/Nom-nom-hub/chronosgraph.git
cd chronosgraph
pip install -r requirements.txt # Assuming a requirements.txt will be added later
```

### Quick Start

Here's a quick example of how to use ChronosGraph SDK to initialize an agent, record an episode, and recall information:

```python
from chronosgraph_sdk import ChronosGraphSDK

# Initialize the SDK (this will create a chronosgraph.db SQLite file)
sdk = ChronosGraphSDK("my_agent_memory.db")

# Register a new agent
agent_id = sdk.initialize_agent("MyAgent", "A test agent for demonstration.")
print(f"Agent registered with ID: {agent_id}")

# Record an episode (e.g., an observation)
episode_id = sdk.check_in(agent_id, {
    "type": "observation",
    "content": "I observed a strange anomaly in sector 7."
})
print(f"Recorded episode with ID: {episode_id}")

# Recall relevant information based on a query
query = "What did I see in sector 7?"
context = sdk.recall(agent_id, query, context_type="semantic")
print(f"\nRecalled context for \"{query}\":\n{context}")
```

## Contributing

We welcome contributions to ChronosGraph! Please see our `CONTRIBUTING.md` (to be added) for guidelines on how to submit issues, features, and pull requests.

## License

This project is licensed under the MIT License - see the `LICENSE` file for details.
