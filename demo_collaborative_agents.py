import os
from chronosgraph_sdk import ChronosGraphSDK

def run_collaborative_demo():
    db_name = "collab_demo.db"
    if os.path.exists(db_name):
        os.remove(db_name)
        
    print("🚀 Initializing ChronosGraph Collaborative Demo...")
    sdk = ChronosGraphSDK(db_name)
    
    # 1. Initialize two agents in the same shared group
    group_id = "project_alpha"
    researcher_id = sdk.initialize_agent("ResearcherBot", "Gathers information.", shared_group=group_id)
    writer_id = sdk.initialize_agent("WriterBot", "Writes reports based on research.", shared_group=group_id)
    
    print(f"✅ ResearcherBot and WriterBot joined group: {group_id}")
    
    # 2. ResearcherBot records an observation
    print("\n🕵️ ResearcherBot is working...")
    sdk.check_in(researcher_id, {
        "content": "The quarterly revenue for Q1 2026 is $4.5 billion, a 12% increase year-over-year."
    })
    print("✅ ResearcherBot saved a discovery.")
    
    # 3. WriterBot tries to recall information it never personally saw
    print("\n✍️ WriterBot is starting a report...")
    task = "What were the Q1 2026 financial results?"
    print(f"WriterBot Query: '{task}'")
    
    context = sdk.get_context(writer_id, task)
    
    print("\n🧠 WriterBot's Retrieved Context:")
    print(context)
    
    print("\n✨ Conclusion: WriterBot successfully 'remembered' what ResearcherBot discovered "
          "because they share a collective consciousness via ChronosGraph!")

if __name__ == "__main__":
    run_collaborative_demo()
