# ID2223-Project  
## Qwen-8B Research Agent with Zotero-Driven RAG

This repository implements a research assistant agent built on **Qwen-8B**, designed for **paper-centric reasoning** over a continuously updating academic library managed in **Zotero**.

---

## System Overview

The system integrates four layers:

- **Zotero CSV** — the paper source of truth  
- **Feature Groups (Hopsworks)** — structured research database  
- **Vector embeddings (RAG)** — semantic search over paper content  
- **LLM Agent (Qwen-8B)** — tool-aware reasoning and decision making  

---

## Part I — Agent

Qwen-8B operates as a **decision-making agent**, not a plain chatbot.

For every user question, it reasons between three possible actions:

### 1. Direct Answer
Used when the question is **conceptual** or does **not require stored papers**.

### 2. RAG Retrieval
Used when the answer **depends on paper content** and must be retrieved from the vector database.

### 3. Tool Call (MCP)
Used when the question **requires interacting with structured data**, such as:
- checking which papers exist
- detecting newly added papers
- querying metadata

This design makes the model:

- **Data-aware**
- **Tool-aware**
- **Context-aware**

rather than a blind text generator.

##  Part II — Feature Group Design

Two Feature Groups form the backbone of the system.

---

### 1 Paper Metadata Feature Group

This Feature Group stores **one record per paper**.

It represents the **bibliographic layer** of the library, answering:

- What papers exist  
- Who wrote them  
- When and where they were published  

This Feature Group is used when the agent needs:

- Paper lists  
- Filtering by author, year, or topic  
- Citation-style information  

---

### 2 Paper Chunk Embedding Feature Group

This Feature Group stores **semantic representations of paper content**.

It represents the **knowledge layer** of the library, capturing:

- What papers actually say  
- How ideas relate across papers  

It is used for:

- Semantic search  
- RAG retrieval  
- Context injection into Qwen-8B  

---

### 3 How the Agent Chooses

The agent decides which Feature Group to use based on the intent of the question.

| Question Type | Data Layer |
|--------------|------------|
| “Which papers discuss X?” | Metadata Feature Group |
| “Explain how method Y works” | Embedding Feature Group |
| “Show recent papers” | Metadata Feature Group |
| “Summarize what papers say about Z” | Both Feature Groups |

This design makes the system **structurally grounded**, not just vector-based.
