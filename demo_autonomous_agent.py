import time
import sqlite3
from chronosgraph_sdk import ChronosGraphSDK

def run_autonomous_demo():
    print("🚀 Initializing ChronosGraph Autonomous Demo...")
    sdk = ChronosGraphSDK("autonomous_agent.db")
    
    agent_id = sdk.initialize_agent("AutoMind", "An agent with autonomous fact extraction.")
    print(f"✅ Agent 'AutoMind' ready.")
    
    # Simulating a complex observation
    observation = (
        "I am meeting with Elon Musk at the SpaceX headquarters in Boca Chica. "
        "We are discussing the Starship launch schedule and the importance of multi-planetary life."
    )
    
    print(f"\n📝 Recording Observation: \"{observation}\"")
    print("🧠 ChronosGraph is now autonomously extracting facts and building the graph...")
    
    episode_id = sdk.check_in(agent_id, {
        "type": "observation",
        "content": observation
    })
    
    print(f"✅ Episode recorded: {episode_id}")
    
    # Now let's inspect what ChronosGraph did autonomously
    print("\n🔍 Inspecting the Autonomous Knowledge Graph:")
    
    with sqlite3.connect("autonomous_agent.db") as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Check extracted entities
        print("\n--- Extracted Entities ---")
        cursor.execute("SELECT name, type, description FROM entities WHERE agent_id = ?", (agent_id,))
        entities = cursor.fetchall()
        for ent in entities:
            print(f"🔹 [{ent['type'].upper()}] {ent['name']}: {ent['description']}")
            
        # Check extracted relationships
        print("\n--- Extracted Relationships ---")
        cursor.execute("SELECT source_id, target_id, type FROM relationships WHERE agent_id = ?", (agent_id,))
        rels = cursor.fetchall()
        for rel in rels:
            # Resolve names for display
            cursor.execute("SELECT name FROM entities WHERE entity_id = ?", (rel['source_id'],))
            s_row = cursor.fetchone()
            s_name = s_row['name'] if s_row else "Episode"
            
            cursor.execute("SELECT name FROM entities WHERE entity_id = ?", (rel['target_id'],))
            t_name = cursor.fetchone()['name']
            
            print(f"🔗 {s_name} --({rel['type']})--> {t_name}")

    print("\n✨ ChronosGraph autonomously built this graph from a single sentence!")
    print("The agent now 'knows' these entities and their connections for future recall.")

if __name__ == "__main__":
    run_autonomous_demo()
