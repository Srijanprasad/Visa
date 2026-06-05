# AI Agent Instructions for Visa

## Purpose
This file helps AI coding agents understand the structure, conventions, and priorities for the `Visa` repo.

## Project overview
- `app.py` is the Streamlit application entrypoint and UI layer.
- `backend/` contains RAG ingestion and inference logic.
- `visa_rules/` implements visa-specific eligibility and policy handling.
- `visa_services/` provides supporting services such as financial validation, sponsor checks, TB checks, retrieval, and LLM orchestration.
- `vector_db/`, `uk_visa_db/`, and `visa_db/` are data/storage directories for the RAG indexes and policy databases.

## What to know first
- The app is a Python/Streamlit project using Python 3.8+.
- Dependencies are declared in `requirements.txt`.
- Environment configuration is loaded from `.env` and `.env.example`.
- Two retrieval stacks exist in the repo:
  - `backend/rag_agent.py` uses LangChain + Chroma + HuggingFace embeddings.
  - `backend/rag_system.py` uses SentenceTransformer + FAISS + Ollama.
- The system is designed for UK visa eligibility screening across multiple routes:
  - Student Visa
  - Skilled Worker Visa
  - Graduate Visa
  - Health & Care Visa
  - Visitor Visa

## Important conventions
- Preserve the professional black-and-white theme. Avoid reintroducing emojis, bright accent colors, or casual language in UI text.
- Keep business logic inside `visa_rules/` and `visa_services/` whenever possible; `app.py` should remain primarily UI and orchestration.
- Do not hardcode secret keys or service endpoints. Use `.env`/environment variables instead.
- Prefer lightweight edits over wholesale rewrites for RAG flow changes; there are existing retrieval and index-loading patterns.
- There is no formal tests/`tests/` directory in this repo, so new code should include manual verification guidance or minimal coverage if adding test support.

## Recommended files to inspect
- `README.md` and `DEPLOYMENT_GUIDE.md` for setup and operational expectations.
- `app.py` for the UI flow and page configuration.
- `backend/ingest.py` for data ingestion patterns.
- `backend/rag_agent.py` for the current agent architecture.
- `backend/rag_system.py` for FAISS-based retrieval and Ollama integration.
- `visa_rules/*.py` for visa route rules.
- `visa_services/*.py` for supporting domain services.

## Common developer goals
- Keep the eligibility assessment logic grounded in policy documents and rule metadata.
- Avoid introducing new external LLM providers without updating `README.md` and environment docs.
- Use the existing RAG indexes when possible rather than adding duplicate retrieval pipelines.
- Maintain the current deployment expectations: Streamlit app with local Ollama/LLM or Pinecone-backed retrieval.

## Known risks / pitfalls
- The repo expects local LLM services (`OLLAMA_URL` or `LLM_BASE_URL`) and may fail if these services are not available.
- There are multiple vector storage locations. Do not assume a single source of truth without verifying the code path.
- Large binary artifacts live under `vector_db/` and `uk_visa_db/`; avoid modifying or committing them unless required.

## Useful links
- [README](README.md)
- [DEPLOYMENT_GUIDE](DEPLOYMENT_GUIDE.md)
- [.env.example](.env.example)
