"""
Example 04: RAG-Powered Chat Agent
===================================
This example shows how to create an agent that uses Retrieval-Augmented
Generation (RAG) to answer questions based on your own documents (PDF, TXT).

The agent uses a built-in TF-IDF engine (numpy-based) to retrieve relevant
context from the specified directory and inject it into the conversation.
"""

import asyncio
import os
from daie import Agent, AgentConfig, set_llm
from daie.agents import AgentRole

# 1. Configure the LLM
set_llm(ollama_llm="llama3.2:1b", stream=True)

# 2. Path to your documents folder
DOCUMENTS_PATH = os.path.join(os.path.dirname(__file__), "my_documents")


async def main():
    # Ensure the documents directory exists
    os.makedirs(DOCUMENTS_PATH, exist_ok=True)

    # Create a sample document for testing
    sample_file = os.path.join(DOCUMENTS_PATH, "sample.txt")
    if not os.path.exists(sample_file):
        with open(sample_file, "w") as f:
            f.write(
                "DAIE (Decentralized AI Ecosystem) is an open-source Python library "
                "for building multi-agent AI systems. It supports tools like Selenium "
                "for web browsing, file management, API calls, and agent-to-agent "
                "communication over P2P networks. Agents can have unique personas "
                "with custom gender, personality, and behavioral traits.\n\n"
                "Key features:\n"
                "- ReAct-style tool-use loop for autonomous task execution\n"
                "- P2P networking with secure file transfers\n"
                "- Memory management (working, semantic, episodic)\n"
                "- Audio input/output and camera vision capabilities\n"
                "- RAG support for document-based knowledge retrieval\n"
            )
        print(f"📄 Created sample document at: {sample_file}\n")

    # 3. Configure the RAG-enabled agent
    config = AgentConfig(
        name="DocBot",
        role=AgentRole.GENERAL_PURPOSE,
        system_prompt=(
            "You are a knowledgeable assistant. Use the provided document context "
            "to answer questions accurately. If the context doesn't contain the "
            "answer, say so honestly."
        ),
        personality="precise, helpful, and thorough",
        temperature=0.3,       # Lower temperature for factual answers
        max_tokens=1024,
        # --- RAG configuration ---
        rag_document_path=DOCUMENTS_PATH,
        enable_rag=True,
        rag_strict_context=True,  # Only answer from documents, refuse outside queries
    )

    # 4. Create and start the agent
    agent = Agent(config=config)
    await agent.start()

    print("=== RAG Chat (Document-Powered) ===")
    print(f"📂 Documents loaded from: {DOCUMENTS_PATH}")
    print("Type 'exit' to quit.\n")

    while True:
        try:
            user_input = input("You: ")
            if user_input.lower() in ("exit", "quit"):
                break
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            break

        # 5. Send message — the agent should automatically retrieve
        #    relevant document chunks and include them in the prompt
        response = await agent.send_message(user_input)

        if response.startswith("Error:"):
            print(response)

        print("\n")

    await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
