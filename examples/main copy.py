import asyncio
import os
from daie import Agent, AgentConfig, set_llm, Orchestrator
from daie.agents import AgentRole


DOCUMENTS_PATH = os.path.join(os.path.dirname(__file__), "data")

config1 = AgentConfig(
        name="NOVA",
        role=AgentRole.GENERAL_PURPOSE,
        system_prompt=(
            "You are a knowledgeable assistant. Use the provided document context "
            "to answer questions accurately. If the context doesn't contain the "
            "answer, say so honestly."
        ),
        personality="precise, helpful, and thorough",
        gender="female",
        behavior="always cites the source document chunk in your answer",
        temperature=0.3,       # Lower temperature for factual answers
        max_tokens=1024,
        # --- RAG configuration ---
        rag_document_path=DOCUMENTS_PATH,
        enable_rag=True,
    )

config2 = AgentConfig(
        name="Professor_AI",
            role=AgentRole.COORDINATOR,
            goal="Coordinate students to solve complex problems professionally",
            system_prompt="You are an expert professor. You break down complex queries into logical sub-tasks for your students.",
            # --- RAG configuration ---
            rag_document_path=DOCUMENTS_PATH,
            enable_rag=True,
        )

NOVA = Agent(config=config1)
Professor = Agent(config=config2)

async def main():
    # 1. Configure the LLM
    set_llm(ollama_llm="llama3.2:1b", stream=True)

    # 2. Ensure the documents directory exists
    os.makedirs(DOCUMENTS_PATH, exist_ok=True)
    sample_file = os.path.join(DOCUMENTS_PATH, "sample.txt")
    if not os.path.exists(sample_file):
        with open(sample_file, "w") as f:
            f.write(
                "DAIE (Decentralized AI Ecosystem) is an open-source Python library "
                "for building multi-agent AI systems.\n"
                "Key features:\n"
                "- Unified Orchestrator model for agent coordination\n"
                "- RAG support for document-based knowledge\n"
            )
        print(f"📄 Created sample document at: {sample_file}\n")

    research_lab = Orchestrator(
        main_agent=Professor,
        sub_agents=[NOVA,],
        context_name="research_lab",
        main_role="Professor",
        sub_role="research assistant"
    )

    await research_lab.start()

    while True:
        try:
            user_input = input("\033[94mYou (Court Clerk):\033[0m ").strip()
            if not user_input:
                continue
            if user_input.lower() in ['exit', 'quit']:
                break

            print("\n\033[92mJudge_Justice is presiding over the case...\033[0m")
            
            # Execute the task
            result = await research_lab.execute_task(user_input)
            
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
    await research_lab.stop()
    print("[+] Session closed.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass

