import asyncio
import logging
import sys
from daie import Agent, AgentConfig, AgentRole, Orchestrator, set_llm

# Configure logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='classroom.log',
    filemode='w'
)

# Also log to console but more concisely
console = logging.StreamHandler()
console.setLevel(logging.WARNING)
logging.getLogger('').addHandler(console)

async def main():
    print("\n" + "="*50)
    print("   AI CLASSROOM INTERACTIVE DEMO (Ollama)")
    print("="*50)
    
    # 0. Ask for streaming
    stream_input = input("Enable real-time streaming (reasoning & answers)? [Y/n]: ").lower()
    use_streaming = stream_input != 'n'
    
    # Configure LLM to use Ollama
    set_llm(ollama_llm="llama3.2:1b", stream=use_streaming)

    print(f"\n[*] Streaming is {'ENABLED' if use_streaming else 'DISABLED'}")
    print("Type 'exit' or 'quit' to end the session.\n")

    # 1. Create Teacher Agent
    teacher = Agent(
        config=AgentConfig(
            name="Professor_AI",
            role=AgentRole.COORDINATOR,
            goal="Coordinate students to solve complex problems professionally",
            system_prompt="You are an expert professor. You break down complex queries into logical sub-tasks for your students."
        )
    )

    # 2. Create Student Agents
    math_student = Agent(
        config=AgentConfig(
            name="Math_Student",
            role=AgentRole.SPECIALIZED,
            goal="Handle numerical, logical, and computational parts of a task",
            system_prompt="You are a brilliant math student. provide precise calculations and logic."
        )
    )

    research_student = Agent(
        config=AgentConfig(
            name="Research_Student",
            role=AgentRole.SPECIALIZED,
            goal="Provide factual information, research data, and creative writing",
            system_prompt="You are a diligent research student. Provide detailed explanations and well-structured content."
        )
    )

    # 3. Create Orchestrator
    classroom = Orchestrator(
        main_agent=teacher,
        sub_agents=[math_student, research_student],
        context_name="Classroom",
        main_role="Teacher",
        sub_role="Student"
    )

    # 4. Start Orchestrator
    print("[*] Initializing classroom environment...")
    await classroom.start()
    print("[+] Classroom is ready! Teacher: Professor_AI, Students: Math_Student, Research_Student\n")

    # 5. Chat Loop
    while True:
        try:
            user_input = input("\033[94mYou:\033[0m ")
            if user_input.lower() in ["exit", "quit", "bye"]:
                print("\n[*] Dismissing class. Goodbye!")
                break
            
            if not user_input.strip():
                continue

            print("\n\033[92mProfessor_AI is orchestrating the class...\033[0m")
            
            # Execute the task
            result = await classroom.execute_task(user_input)
            
            # Extract answer if it still looks like JSON (precaution for smaller models)
            final_display = result
            if isinstance(result, str) and result.strip().startswith("{"):
                try:
                    import json
                    parsed = json.loads(result)
                    final_display = parsed.get("answer", result)
                except:
                    pass

            print(f"\n\033[93mFinal Answer from Professor_AI:\033[0m")
            print(f"{final_display}\n")
            
            print("-" * 30 + "\n")

        except KeyboardInterrupt:
            print("\n\n[*] Interrupted by user. Closing classroom...")
            break
        except Exception as e:
            print(f"\n\033[91mError:\033[0m {e}")
            logging.error(f"Error in chat loop: {e}", exc_info=True)

    # 6. Stop Classroom
    await classroom.stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
