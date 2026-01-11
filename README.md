# ID2223-Project Qwen-8B Research Agent with Zotero-Driven RAG
## This repository implements a research assistant agent built on Qwen-8B, designed for paper-centric reasoning over a continuously updating academic library managed in Zotero.
The system integrates:
* Zotero CSV as the paper source of truth
* Feature Groups (Hopsworks) as the structured research database
* Vector embeddings (RAG) for semantic search
* LLM Agent (Qwen-8B) for tool-aware reasoning

### Part I：Agent
Qwen-8B operates as a decision-making agent, not a plain chatbot.

For every user question, it reasons between three actions:

Action	Purpose
Direct Answer	The question is conceptual or does not require stored papers
RAG Retrieval	The question depends on paper content
Tool Call (MCP)	The question requires interacting with stored data

This makes the model data-aware, tool-aware, and context-aware.
