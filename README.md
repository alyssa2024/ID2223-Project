## 📚 Introduction

This project implements an intelligent **Paper Reading Agent** that transcends linear chatbots by employing an **autonomous agentic loop**, leveraging **Hopsworks Feature Store** to manage vector embeddings derived from **Zotero** libraries. Unlike static `Query → Retrieve → Answer` pipelines, the agent actively **evaluates evidence sufficiency**: it orchestrates a **two-stage retrieval strategy** (metadata scoping followed by full-text drill-down with **reranking**) and iteratively decides whether to refine the search or proceed to reasoning based on the quality of the dynamic context. This retrieved evidence forms the basis of **In-Context Learning (ICL)**—supplemented by few-shot demonstrations to guide reasoning—enabling the LLM to generate grounded responses with **strict, evidence-backed citations**..

The system allows users to interact with their research papers as a searchable and queryable knowledge base, supporting efficient literature exploration, comprehension, and cross-paper reasoning.

## 🏗️ System Architecture

<img src="agent_articheture.png" width="800"/>

## 🔄 Pipelines Description

The project is structured around three core pipelines, designed to handle data ingestion, incremental updates, and agentic inference. These pipelines are implemented as modular components, ensuring separation of concerns between data engineering (MLOps) and application logic.

###  1. Feature Backfill Pipeline (Bootstrap)

The Feature Backfill pipeline is responsible for the **initial construction of the knowledge base**.
It performs the following steps:
- **Data Ingestion**: Loads paper metadata and extracts full text from PDFs based on the Zotero export.
- **Feature Engineering**: Processes data in two parallel streams—**metadata** (Titles/Abstracts) is embedded directly, while **full text** is first split into chunks before embedding.
- **Storage**: Uploads both raw data and vector embeddings to **Hopsworks Feature Store**, organizing them into distinct Feature Groups for metadata and chunks.

This pipeline is executed once to bootstrap the system with the complete literature collection.

---

###  2. Feature Pipeline (Incremental Update)

The Feature Pipeline enables **continuous learning** by handling incremental updates.
It focuses on:
- **Change Detection**: Identifies new or modified entries in the Zotero CSV compared to the existing Feature Store.
- **Update Logic**: Applies the **same feature engineering process** (chunking and embedding) as the backfill pipeline to the new data.
- **Synchronization**: Upserts the processed features into the existing Hopsworks Feature Groups.

This design enables efficient and scalable updates as the literature collection grows over time.

---

###  3. Inference Pipeline (Agent & UI)

The Inference Pipeline operationalizes the **Paper Reading Agent** and provides the interactive layer for the user.

- **Agent Instantiation**: Constructs the runtime agent by initializing the Hopsworks vector retrieval layer and assembling the reasoning modules (Intent Router, Context Builder) to support RAG and In-Context Learning.
- **User Interface (UI)**: Deploys a **chatbot-style interface** where the model generates answers with strict **paper-level citations**. Users can interact with these citations via **collapsible icons**, which expand to reveal the specific full-text chunks used as evidence.

Together, these components transform the static data in Hopsworks into a dynamic, queryable research assistant.

## 🧠 RAG Agent Execution Model

The system operates as a specialized **Retrieval-Augmented Generation (RAG) Agent**, designed to bridge the gap between static **Zotero** libraries and dynamic, evidence-based reasoning. Unlike standard RAG implementations, this agent employs a **"Coarse-to-Fine" Agentic Loop**, orchestrated via the **Model Context Protocol (MCP)**, to optimize the quality of the retrieved context before generation.

The execution flow consists of four distinct phases:

### 1. Intent Routing (RAG Trigger)

Every user interaction is first evaluated by the **Intent Router** to determine if external knowledge is required:
- **Direct Interaction**: General chitchat is handled immediately, bypassing the RAG pipeline.
- **RAG Activation**: Research-oriented queries trigger the **Agentic Loop**, initializing the state for multi-stage retrieval against the **Hopsworks Feature Store**.

### 2. Phase I: Semantic Scoping (Metadata Embedding)

Upon entering the loop, the agent executes the first stage of the RAG pipeline via **MCP**:
- **Vector Search**: Performs a semantic search using **metadata embeddings** (generated from titles and abstracts of Zotero papers).
- **Candidate Filtering**: Identifies the top-k most relevant papers to establish a focused search boundary.
- **Silent Filtering**: These candidates serve solely as a scope constraint and are not passed to the LLM, preventing hallucination based on shallow abstracts.

### 3. Phase II: Deep Retrieval & Reranking

Immediately after scoping, the system executes a **Forced Deep Dive** to acquire high-granularity evidence:
- **Chunk Retrieval**: The agent triggers a second MCP tool call to search for **full-text chunk embeddings**, constrained strictly within the candidate `paper_ids` identified in Phase I.
- **Reranking**: Retrieved chunks undergo a **Reranking process** to re-score and re-order them based on their precise relevance to the specific query query, ensuring the most critical information bubbles to the top.
- **Context Injection**: The agent state is updated with these optimized, high-relevance chunks, and the loop performs a `continue` to refresh the context window.

### 4. Phase III: Grounded Generation (ICL + Prompt)

In the final phase, the agent acts as the **Generator**:
- **Dynamic Context Assembly**: The **Context Builder** constructs a prompt using the reranked full-text chunks.
- **In-Context Learning (ICL)**: The prompt is fortified with **few-shot examples** to guide the LLM’s reasoning style and citation format.
- **Evidence-Based Answer**: The LLM synthesizes an answer using *only* the provided context, appending strict **Paper-Level Citations** (e.g., `[1]`) that link back to the source documents.

This architecture ensures a high-fidelity RAG process: **Macro-level search (Metadata) $\to$ Micro-level retrieval (Chunks) $\to$ Quality Optimization (Rerank) $\to$ Grounded Synthesis.**
