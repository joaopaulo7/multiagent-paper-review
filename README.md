# Multiagent Paper Review System

A research system for automated scientific paper review using multi-agent architectures with Large Language Models (LLMs). The system processes academic papers and generates structured multi-perspective reviews through coordinated specialized agents.

## Architecture

The system consists of three main components orchestrated via Docker Compose:

### 1. Papers Server (MCP Server)

A FastMCP-based Model Context Protocol server that provides paper search and retrieval capabilities.

- **papersMCP.py**: MCP server implementation exposing two tools:
  - `search_articles(query)`: Semantic search using FAISS vector store, returns top-3 relevant paper chunks with relevance scores
  - `get_article_content(id)`: Retrieves a configurable window (default 20KB) of text centered on the matched chunk position, enabling retrieval of longer context while avoiding loading entire large documents

- **CreateVectorStore.ipynb**: Jupyter notebook for batch processing incoming PDF papers:
  - Loads PDFs using PyMuPDF4LLM
  - Cleans and preprocesses text (removes tables, links, references, multi-line breaks)
  - Chunks documents with 10% overlap using RecursiveCharacterTextSplitter
  - Stores in FAISS vector database with metadata (title, area, doc_id, chunk position)
  - Saves processed text as markdown in `vector_db/documents/`

Papers are organized in `papers-server/papers/` by research area subdirectories (CS, biology, nutrition).

### 2. Paper Export Client (Multi-Agent Reviewer)

A LangGraph-based multiagent system generating structured paper reviews from three distinct perspectives.

- **ReviewerAgents.ipynb**: Main review orchestration notebook implementing a StateGraph with four node types:
  - `nice_reviewer`: Generates favorable reviews emphasizing positive aspects
  - `strict_reviewer`: Critical review focusing on research gaps and weaknesses
  - `neutral_reviewer`: Balanced perspective avoiding strong opinions
  - `editor`: Synthesizes final review from all three perspectives

The output schema (`Review` model) includes:
- `area`: Main research area
- `problem`: Problem statement addressed
- `step_by_step`: Methodological approach
- `conclusion`: Process conclusion
- `overall_review`: Comprehensive markdown review (in Portuguese)

Each reviewer agent has access to the MCP server tools for cross-referencing other papers in the database.

### 3. Llama.cpp (configurable)

CUDA-enabled Docker container serving GGUF-format LLM models via OpenAI-compatible API:

- **Chat model**: NVIDIA-Nemotron-3-Nano-4B-Q4_K_M.gguf (4B parameters)
- **Embedding model**: embeddinggemma-300m-qat-Q4_0.gguf

### Shared Utilities

**common/utils.py**: Core utilities for both server and client:
- LLM instantiation via `lm-config.yaml` (supports OpenAI-compatible, Google GenAI, Ollama providers)
- PDF loading via PyMuPDF4LLM
- Text cleaning functions (markdown tables, links, references, multi-line breaks)
- Document chunking with configurable size and overlap

## Configuration

**lm-config.yaml**: Defines LLM provider settings. Can be altered to run cloud model:
```yaml
main_language_model:
  provider: openai
  model: NVIDIA-Nemotron-3-Nano-4B-GGUF
  base_url: http://llamacpp:8082/v1
  
main_embedding_model:
  provider: openai
  model: embeddinggemma-300m-qat-GGUF
  base_url: http://llamacpp:8082/v1
```

## Deployment

```bash
docker compose up --build
```

The client Jupyter notebook is accessible at `http://localhost:8888`.