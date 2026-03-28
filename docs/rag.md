# RAG (Retrieval-Augmented Generation)

DAIE provides a built-in RAG engine that allows agents to maintain independent knowledge bases. Each agent can have its own unique set of documents, and the agent will automatically retrieve relevant context before answering queries.

## Features

- **Per-Agent Knowledge Bases** — Each agent can have its own `rag_document_path`
- **TF-IDF Retrieval** — Uses TF-IDF indexing with cosine similarity (no external ML dependencies)
- **Automatic Context Augmentation** — Retrieved context is automatically injected into prompts
- **Strict Context Mode** — Optionally restrict answers to document content only
- **Multiple Document Formats** — Supports `.txt`, `.pdf`, `.md` files

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          USER / APPLICATION                                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              AGENT                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         RAG ENGINE                                  │    │
│  │  • Document loading                                                 │    │
│  │  • TF-IDF indexing                                                  │    │
│  │  • Context retrieval                                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      DOCUMENT LOADER                                │    │
│  │  • .txt files                                                       │    │
│  │  • .pdf files                                                       │    │
│  │  • .md files                                                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         CHUNKER                                     │    │
│  │  • Split documents into chunks                                      │    │
│  │  • Configurable chunk size                                          │    │
│  │  • Overlapping chunks for context continuity                        │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                      TF-IDF INDEXER                                 │    │
│  │  • Build vocabulary                                                 │    │
│  │  • Compute term frequency                                           │    │
│  │  • Compute inverse document frequency                               │    │
│  │  • Create TF-IDF matrix                                             │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         RETRIEVER                                   │    │
│  │  • Convert query to TF-IDF vector                                   │    │
│  │  • Compute cosine similarity                                        │    │
│  │  • Return top-k relevant chunks                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                    │                                        │
│                                    ▼                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    CONTEXT BUILDER                                  │    │
│  │  • Format retrieved chunks                                          │    │
│  │  • Inject into agent prompt                                         │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              LLM MANAGER                                    │
│  • Ollama  • OpenAI  • Anthropic  • Google  • Azure  • OpenRouter           │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Quick Start

```python
from daie import Agent, AgentConfig, set_llm

set_llm(ollama_llm="llama3.2:latest")

# Create agent with RAG enabled
config = AgentConfig(
    name="Expert",
    rag_document_path="data/expert_knowledge/",  # Local folder with documents
    enable_rag=True,
)
agent = Agent(config=config)
await agent.start()

# Agent will automatically retrieve relevant context before answering
result = await agent.execute_task("What is DAIE?")
```

---

## Configuration

### AgentConfig RAG Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `rag_document_path` | `str \| None` | `None` | Path to directory containing documents |
| `enable_rag` | `bool` | `False` | Enable RAG functionality |
| `rag_strict_context` | `bool` | `False` | Only answer from documents |

### Strict Context Mode

When `rag_strict_context=True`, the agent will ONLY answer from the loaded documents and refuse to respond to anything outside the document context:

```python
config = AgentConfig(
    name="StrictExpert",
    rag_document_path="data/knowledge/",
    enable_rag=True,
    rag_strict_context=True,  # Only answer from documents
)
```

---

## RAGEngine

The `RAGEngine` class handles document loading, chunking, indexing, and retrieval:

```python
from daie.rag import RAGEngine

engine = RAGEngine(
    document_path="data/knowledge/",
    chunk_size=500,        # Max characters per chunk
    chunk_overlap=50,      # Overlapping characters between chunks
)

# Load documents and build index
num_chunks = engine.load()
print(f"Loaded {num_chunks} chunks")

# Retrieve relevant chunks
results = engine.retrieve("What is DAIE?", top_k=3)
for chunk, score in results:
    print(f"Score: {score:.3f}")
    print(f"Source: {chunk.source}")
    print(f"Text: {chunk.text[:100]}...")
```

### RAGEngine Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `document_path` | `str` | — | Path to documents directory |
| `chunk_size` | `int` | `500` | Max characters per chunk |
| `chunk_overlap` | `int` | `50` | Overlapping characters between chunks |

### RAGEngine Methods

| Method | Description |
|--------|-------------|
| `load()` | Load documents, chunk them, and build TF-IDF index. Returns number of chunks. |
| `retrieve(query, top_k=3)` | Retrieve most relevant chunks for a query. Returns list of (Chunk, score) tuples. |
| `build_context(query, top_k=3)` | Build a context string from retrieved chunks. |

### RAGEngine Properties

| Property | Description |
|----------|-------------|
| `is_loaded` | Whether the engine has loaded documents |
| `num_chunks` | Number of chunks in the index |

---

## How It Works

### 1. Document Loading

Documents are loaded from the specified directory:

```python
from daie.rag.document_loader import load_directory

documents = load_directory("data/knowledge/")
# Returns list of Document objects with .content and .source
```

Supported formats:
- `.txt` — Plain text files
- `.pdf` — PDF files (requires PyPDF2)
- `.md` — Markdown files

### 2. Chunking

Documents are split into chunks:

- Each chunk has a maximum of `chunk_size` characters
- Chunks overlap by `chunk_overlap` characters for context continuity
- Each chunk tracks its source file and index

### 3. TF-IDF Indexing

A TF-IDF (Term Frequency-Inverse Document Frequency) index is built:

- **Term Frequency**: How often a term appears in a chunk
- **Inverse Document Frequency**: How rare a term is across all chunks
- **TF-IDF Score**: Product of TF and IDF — highlights important, specific terms

### 4. Retrieval

When a query is received:

1. The query is converted to a TF-IDF vector
2. Cosine similarity is computed between the query and all chunks
3. Top-k most similar chunks are returned
4. Chunks with similarity > 0.05 are included

### 5. Context Augmentation

Retrieved context is automatically injected into the agent's prompt:

```
Additional Information:
[Retrieved chunk 1 text]
[Retrieved chunk 2 text]
[Retrieved chunk 3 text]

Instruction: Only use the information provided above to answer. If the information is not there, say you don't know.

User: What is DAIE?
```

---

## Multiple Knowledge Bases

Each agent can have its own unique knowledge base:

```python
# Agent 1: Technical expert
tech_expert = Agent(config=AgentConfig(
    name="TechExpert",
    rag_document_path="data/technical_docs/",
    enable_rag=True,
))

# Agent 2: Business analyst
business_analyst = Agent(config=AgentConfig(
    name="BusinessAnalyst",
    rag_document_path="data/business_docs/",
    enable_rag=True,
))

# Each agent retrieves from its own knowledge base
tech_result = await tech_expert.execute_task("How does the system work?")
business_result = await business_analyst.execute_task("What are the business benefits?")
```

---

## Document Loader

The `DocumentLoader` handles loading different file formats:

```python
from daie.rag.document_loader import Document, load_directory

# Load all documents from a directory
documents = load_directory("data/knowledge/")

for doc in documents:
    print(f"Source: {doc.source}")
    print(f"Content: {doc.content[:100]}...")
```

### Document Class

```python
@dataclass
class Document:
    content: str    # Document text content
    source: str     # Source file path
```

---

## Chunk Class

The `Chunk` class represents a piece of text extracted from a document:

```python
@dataclass
class Chunk:
    text: str           # The text content
    source: str         # Source file path
    chunk_index: int    # Index within the source document
```

---

## Performance Considerations

- **Chunk Size**: Larger chunks provide more context but reduce precision. Default: 500 characters.
- **Chunk Overlap**: Overlap ensures context continuity. Default: 50 characters.
- **Top-K**: More results provide broader context but increase prompt size. Default: 3.
- **Similarity Threshold**: Chunks with similarity < 0.05 are filtered out.

---

## Next Steps

- [Agents](agents.md) — Agent configuration and the ReAct loop
- [Tools](tools.md) — Pre-built tools and creating custom tools
- [LLM Configuration](llm.md) — Multi-provider LLM setup
- [Orchestrator](orchestrator.md) — Multi-agent coordination
