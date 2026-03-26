"""
Courtroom demo using the generic Orchestrator class.
Shows how the same architecture can be used for different contexts.
"""

import asyncio
import logging
from daie import Agent, AgentConfig, Orchestrator, set_llm

async def main():
    print("\n" + "="*50)
    print("   AI COURTROOM INTERACTIVE DEMO (Ollama)")
    print("="*50)
    
    # Ask for streaming preference
    stream_input = input("\nEnable real-time streaming (reasoning & answers)? [Y/n]: ").lower()
    use_streaming = stream_input != 'n'
    
    # Configure LLM to use Ollama
    set_llm(ollama_llm="llama3.2:1b", stream=use_streaming)
    
    if use_streaming:
        print("\n[*] Streaming is ENABLED")
    else:
        print("\n[*] Streaming is DISABLED")
        
    print("Type 'exit' or 'quit' to end the session.\n")

    # Initialize agents
    print("[*] Initializing courtroom environment...")
    
    judge = Agent(config=AgentConfig(
        name="Judge_Justice",
        system_prompt="You are a fair and wise judge. Your goal is to reach a verdict based on arguments from lawyers."
    ))
    
    prosecutor = Agent(config=AgentConfig(
        name="Prosecutor_Agent",
        system_prompt="You are a determined prosecutor. Your goal is to prove the defendant is guilty beyond reasonable doubt."
    ))
    
    defense = Agent(config=AgentConfig(
        name="Defense_Attorney",
        system_prompt="You are a sharp defense attorney. Your goal is to protect the defendant's rights and prove their innocence."
    ))

    # Create the Orchestrator (Court context)
    court = Orchestrator(
        main_agent=judge,
        sub_agents=[prosecutor, defense],
        context_name="Courtroom",
        main_role="Judge",
        sub_role="Lawyer"
    )

    # Start the courtroom
    await court.start()
    print("[+] Court is in session! Judge: Judge_Justice, Lawyers: Prosecutor_Agent, Defense_Attorney\n")

    while True:
        try:
            user_input = input("\033[94mYou (Court Clerk):\033[0m ").strip()
            if not user_input:
                continue
            if user_input.lower() in ['exit', 'quit']:
                break

            print("\n\033[92mJudge_Justice is presiding over the case...\033[0m")
            
            # Execute the task
            result = await court.execute_task(user_input)
            
            # Extract answer if it still looks like JSON
            final_display = result
            if isinstance(result, str) and result.strip().startswith("{"):
                try:
                    import json
                    parsed = json.loads(result)
                    final_display = parsed.get("answer", result)
                except:
                    pass

            print(f"\n\033[93mFinal Verdict/Guidance from Judge:\033[0m")
            print(f"{final_display}\n")
            
            print("-" * 30 + "\n")

        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"\nError in court loop: {e}")

    print("\n[*] Closing courtroom session...")
    await court.stop()
    print("[+] Session closed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
