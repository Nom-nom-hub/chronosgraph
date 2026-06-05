import sqlite3
from chronosgraph_sdk import ChronosGraphSDK

import os

def run_relational_demo():
    db_name = "relational_demo.db"
    if os.path.exists(db_name):
        os.remove(db_name)
        
    print("🚀 Initializing ChronosGraph Relational Demo...")
    sdk = ChronosGraphSDK(db_name)
    agent_id = sdk.initialize_agent("LogicBot", "An agent exploring relational recall.")
    
    # 1. Build a small graph
    print("\n📦 Building a Knowledge Graph...")
    # Episode 1: Meeting
    ep1 = sdk.check_in(agent_id, {
        "type": "observation",
        "content": "Met with Sarah from the Engineering team. She mentioned the 'Project Phoenix' timeline."
    })
    # Episode 2: Another mention
    ep2 = sdk.check_in(agent_id, {
        "type": "observation",
        "content": "Reviewed the Phoenix budget with the Finance department."
    })
    
    # Let's manually add some connections that semantic search might miss
    sarah_id = sdk.add_knowledge(agent_id, "Sarah", "Lead Engineer", "person")
    phoenix_id = sdk.add_knowledge(agent_id, "Project Phoenix", "Next-gen engine development", "project")
    
    sdk.relate(agent_id, ep1, sarah_id, "INVOLVES")
    sdk.relate(agent_id, sarah_id, phoenix_id, "LEADS")
    sdk.relate(agent_id, ep2, phoenix_id, "DISCUSSES")

    print("\n🔍 --- Scenario 1: Semantic Recall ---")
    print("Task: 'Who is leading the new engine project?'")
    # Semantic search might find 'Project Phoenix' but not necessarily 'Sarah' if she isn't in the text
    results = sdk.recall(agent_id, "Project Phoenix", context_type='semantic', limit=2)
    for r in results:
        print(f"🔹 Found Episode: {r['content']}")

    print("\n🔍 --- Scenario 2: Relational Recall ---")
    print("Querying the graph for: 'Project Phoenix'")
    # Relational recall traverses the graph to find Sarah
    relational = sdk.recall(agent_id, "Project Phoenix", context_type='relational')
    for r in relational:
        print(f"🔗 Found {r['result_type'].upper()}: {r['content']} (via {r['rel_type']})")

    print("\n✨ Conclusion: Relational recall found 'Sarah' and 'Finance' connections "
          "that simple semantic search might have ranked lower or missed entirely!")

if __name__ == "__main__":
    run_relational_demo()
