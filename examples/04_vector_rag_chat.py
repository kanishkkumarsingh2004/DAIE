"""
Vector RAG Chat Example

This example demonstrates how to use the VectorRAGEngine for semantic search
with document retrieval. The agent can answer questions based on loaded documents
using vector embeddings for more accurate semantic matching.

Note: As of the latest update, agents with enable_rag=True now use VectorRAGEngine
by default instead of the simple TF-IDF based RAGEngine.

Usage:
    python examples/04_vector_rag_chat.py
"""

import asyncio

from daie import Agent, AgentConfig, set_llm
from daie.chat import ChatLoopConfig
from daie.rag import VectorRAGEngine

# Set up LLM (using Ollama with llama3.2:1b for local inference)
set_llm(ollama_llm="llama3.2:1b", stream=True)


async def main():
    # Initialize vector RAG engine with documents
    # Point this to a directory containing your documents
    rag_engine = VectorRAGEngine(
        document_path="examples/data",
        chunk_size=500,
        chunk_overlap=50,
        embedding_model="all-MiniLM-L6-v2",  # Fast and efficient model
    )

    # Load and index documents
    print("Loading and indexing documents...")
    num_chunks = rag_engine.load()
    print(f"Indexed {num_chunks} chunks from documents\n")

    # Create agent with RAG enabled
    config = AgentConfig(
        name="NOVA",
        gender="female",
        system_prompt="You are a helpful AI assistant with access to a knowledge base. Use the provided context to answer questions accurately. If the context doesn't contain relevant information, say so.",
        personality="knowledgeable, helpful, precise",
        behavior="- Answer questions based on the provided context - Be accurate and cite sources when possible - Keep responses concise",
        enable_rag=True,
        rag_strict_context=True,  # Only use information from documents
    )

    agent = Agent(config=config)
    agent.rag_engine = rag_engine

    # Create and run chat loop
    chat_loop = ChatLoopConfig(
        agent=agent,
        welcome_message="=== Vector RAG Chat ===\nAsk questions about the loaded documents. Type 'exit' to quit.\n",
        show_agent_name=True,
    )

    await chat_loop.run_async()


if __name__ == "__main__":
    asyncio.run(main())
