import time

from chronosgraph_sdk import ChronosGraphSDK


def run_demo():
    print("Initializing ChronosGraph SDK...")
    sdk = ChronosGraphSDK("demo_agent.db")
    
    print("\n--- Registering Agent ---")
    agent_id = sdk.initialize_agent("ExplorerBot", "An agent exploring a virtual world.")
    print(f"Agent 'ExplorerBot' registered with ID: {agent_id}")
    
    print("\n--- Simulating Agent Experience (Episodes) ---")
    
    # Episode 1: Observation
    print("Agent observes the environment...")
    ep1_id = sdk.check_in(agent_id, {
        "type": "observation",
        "content": "I am in a dark forest. I see a glowing mushroom to the north."
    })
    print(f"Recorded Episode 1 (Observation): {ep1_id}")
    time.sleep(0.5)
    
    # Episode 2: Thought
    print("Agent thinks about the observation...")
    ep2_id = sdk.check_in(agent_id, {
        "type": "thought",
        "content": "Glowing mushrooms might be poisonous or magical. I should be careful.",
        "parent_episode_id": ep1_id
    })
    print(f"Recorded Episode 2 (Thought): {ep2_id}")
    time.sleep(0.5)
    
    # Episode 3: Action
    print("Agent takes an action...")
    ep3_id = sdk.check_in(agent_id, {
        "type": "action",
        "content": "I approach the glowing mushroom cautiously.",
        "parent_episode_id": ep2_id
    })
    print(f"Recorded Episode 3 (Action): {ep3_id}")
    time.sleep(0.5)
    
    print("\n--- Adding Explicit Knowledge (Entities) ---")
    print("Agent learns a new fact...")
    ent_id = sdk.add_knowledge(
        agent_id,
        "Lumina Cap",
        "A rare, glowing mushroom found in dark forests. It is safe to touch but tastes terrible.",
        "flora"
    )
    print(f"Added Entity 'Lumina Cap': {ent_id}")
    
    print("\n--- Establishing Relationships (Graph) ---")
    print("Agent connects the observation to the new knowledge...")
    rel_id = sdk.relate(agent_id, ep1_id, ent_id, "IDENTIFIED_AS")
    print(f"Created Relationship (IDENTIFIED_AS) between Episode 1 and Entity 'Lumina Cap': {rel_id}")
    
    print("\n--- Recalling Context for a New Task ---")
    new_task = "I am hungry. Should I eat the glowing mushroom?"
    print(f"Agent Task: '{new_task}'")
    
    print("Agent queries ChronosGraph for context...")
    context = sdk.get_context(agent_id, new_task)
    
    print("\n--- Retrieved Context ---")
    print(context)
    
    print("\n--- Conclusion ---")
    print(
        "The agent can now use this context to make an informed decision "
        "(e.g., 'It tastes terrible, so I shouldn't eat it')."
    )
    print("Demo completed.")

if __name__ == "__main__":
    run_demo()
