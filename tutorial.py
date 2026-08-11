"""
ChronosGraph v1.0 - Professional Tutorial
This script demonstrates the core capabilities of ChronosGraph for AI agents.
"""

import os
from unittest.mock import MagicMock
from chronosgraph.chronosgraph_sdk import ChronosGraphSDK

def main():
    # 1. Initialization
    # In a real scenario, you'd provide your own OpenAI client or use the default.
    # Here we use a mock to ensure the tutorial runs without API keys.
    mock_openai = MagicMock()
    mock_embedding_data = MagicMock()
    mock_embedding_data.embedding = [0.1] * 1536
    mock_openai.embeddings.create.return_value.data = [mock_embedding_data]
    
    # Mock LLM for fact extraction and summarization
    mock_chat_response = MagicMock()
    mock_chat_response.choices[0].message.content = '{"entities": [{"name": "ChronosGraph", "type": "software"}], "relationships": []}'
    mock_openai.chat.completions.create.return_value = mock_chat_response

    sdk = ChronosGraphSDK("tutorial.db", openai_client=mock_openai)
    print("✅ ChronosGraph SDK Initialized.")

    # 2. Agent Registration
    agent_id = sdk.initialize_agent("AlphaAgent", "A research agent.", shared_group="ResearchTeam")
    print(f"✅ Agent Registered: {agent_id}")

    # 3. Checking In (Episodic Memory)
    episode_id = sdk.check_in(agent_id, {
        "content": "Today I started learning about ChronosGraph for agentic memory.",
        "type": "observation"
    })
    print(f"✅ Episode Stored: {episode_id}")

    # 4. Semantic Recall
    print("\n--- Semantic Recall ---")
    results = sdk.recall(agent_id, "What did I learn today?")
    for res in results:
        print(f"Found: {res['content']} (Score: {res['similarity']:.2f})")

    # 5. Natural Language Querying (New in v1.0!)
    print("\n--- Natural Language Query ---")
    # Mocking the query plan for the tutorial
    sdk.query_engine._parse_query = MagicMock(return_value={
        "semantic_search": True,
        "graph_traversal": False,
        "semantic_query": "learning about ChronosGraph"
    })
    query_results = sdk.ask(agent_id, "Tell me about my learning progress.")
    print(f"Query Results: {query_results.get('semantic_results', [])[0]['content']}")

    # 6. Graph Visualization
    print("\n--- Graph Visualization ---")
    mermaid = sdk.visualize_graph(agent_id, "tutorial_graph.mmd")
    print("✅ Mermaid graph generated and saved to tutorial_graph.mmd")

    # Clean up
    if os.path.exists("tutorial.db"):
        os.remove("tutorial.db")
    if os.path.exists("tutorial_graph.mmd"):
        os.remove("tutorial_graph.mmd")

if __name__ == "__main__":
    main()
