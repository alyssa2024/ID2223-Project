## 📚 Introduction

This project implements a **paper reading agent** that enables **semantic search and question answering over academic papers** using **Retrieval-Augmented Generation (RAG)** and **in-context learning**.

The agent operates on a personal literature collection exported from **Zotero** and provides the following capabilities:

- ingests academic papers and their metadata from a Zotero-exported CSV file  
- creates and stores **vector embeddings** for paper content to support semantic retrieval  
- maintains a **continuously updatable knowledge base**, automatically incorporating newly added papers  
- retrieves relevant papers or text chunks in response to user queries  
- leverages a large language model to generate **grounded, context-aware answers** based on retrieved documents  

The system allows users to interact with their research papers as a searchable and queryable knowledge base, supporting efficient literature exploration, comprehension, and cross-paper reasoning.

## 🔄 Pipelines Description

The project is organized around three logical pipelines, each implemented and validated through a corresponding Jupyter notebook.  
The notebooks and pipelines are treated as **parallel representations of the same system components**, where notebooks are used for development and validation, while pipelines define the end-to-end processing logic.

### 🏗️ Feature Backfill Pipeline

The Feature Backfill pipeline is responsible for the **initial construction of the paper knowledge base**.

This pipeline:
- loads a Zotero-exported CSV file containing paper metadata and local PDF file paths  
- parses bibliographic metadata and extracts text from PDF documents  
- processes metadata and document content separately  
- generates vector embeddings for paper text  
- stores metadata features and embeddings in Hopsworks Feature Store  

This pipeline is executed once to bootstrap the system with the full historical literature collection.

---

### 🔄 Feature Pipeline (Incremental Update)

The Feature Pipeline implements **incremental knowledge base updates**.

Its main purpose is to:
- detect newly added papers in an updated Zotero CSV export  
- avoid reprocessing existing documents  
- generate embeddings only for unseen papers or text chunks  
- append new metadata and vectors to the existing feature groups  

This design enables efficient and scalable updates as the literature collection grows over time.

---

### 🤖 Inference Pipeline

The Inference Pipeline implements the **paper reading agent** and provides the interface through which users interact with the system.

It consists of two tightly coupled components:

#### Agent Instantiation

This component is responsible for constructing the paper reading agent, including:
- initializing the vector retrieval layer connected to Hopsworks Feature Store  
- embedding user queries into the same vector space as the paper corpus  
- retrieving relevant papers or text chunks via semantic similarity search  
- assembling retrieved context into prompts  
- applying Retrieval-Augmented Generation and in-context learning using a large language model  

The instantiated agent encapsulates the complete reasoning and retrieval logic required for grounded question answering over the literature collection.

#### User Interface and Interaction

This component handles deployment and user interaction with the agent:
- provides a frontend interface for submitting natural language queries  
- forwards user inputs to the instantiated agent  
- displays generated answers returned by the LLM  
- supports interactive exploration of the paper knowledge base  

Together, these components enable end-to-end interaction, from user query submission to retrieval-aware answer generation, forming the final access point of the system.

## 🧠 Agent Execution Model

The paper reading agent follows a **stateful, retrieval-driven execution model** that tightly couples its internal architecture with a structured inference workflow.  
From query submission to answer delivery, the agent orchestrates intent routing, multi-stage retrieval, reasoning, and citation-aware response generation.

---

### 1. Query Intake and Intent Routing

The execution begins when a user submits a natural language query through the user interface.  
The query is first processed by an **Intent Router**, which classifies the input into one of two categories:

- **Direct interaction queries** (e.g., greetings or self-referential questions), which are answered directly by the language model without retrieval.
- **Information-seeking queries**, which activate the retrieval-augmented agent workflow.

For direct interactions, the agent constructs a minimal prompt, invokes the LLM once, and immediately returns the response to the UI.

---

### 2. Agent State Initialization

For information-seeking queries, the agent initializes an internal **Agent State** that persists throughout inference.  
This state tracks:
- current retrieval results
- the type of the most recent retrieval (`metadata` or `chunks`)
- intermediate paper identifiers

The state enables multi-stage retrieval while keeping intermediate steps internal to the agent.

---

### 3. Metadata Retrieval for Search Scoping

At the start of the retrieval process, the agent detects that no retrieval results are available and performs a **metadata-level semantic search**.

This retrieval stage:
- searches over paper titles and abstracts
- retrieves a small set of relevant papers
- extracts only paper identifiers and high-level metadata

Metadata retrieval is used exclusively to **constrain the search space** and is never exposed to the language model as reasoning context.

---

### 4. Forced Transition to Chunk Retrieval

Immediately after metadata retrieval, the agent performs a **forced transition** to full-text retrieval:

- paper identifiers obtained from metadata search are used to constrain chunk-level retrieval
- detailed text chunks are retrieved from the vector store
- retrieval results in the agent state are overwritten with chunk-level data
- the agent explicitly skips LLM invocation at this stage and restarts the inference loop

As a result, the language model remains unaware of the metadata-only retrieval step.

---

### 5. Context Construction from Full-Text Chunks

Once chunk-level retrieval results are available, the agent proceeds to construct the reasoning context.

This step:
- enriches retrieved chunks with corresponding paper titles
- assembles a structured context using only full-text chunks
- guarantees that metadata-only content is excluded from the prompt

The **Context Builder** enforces a strict separation between retrieval for scoping and retrieval for reasoning.

---

### 6. Prompt Synthesis and LLM Reasoning

The agent synthesizes the final prompt by combining:
- the original user query
- the chunk-based context
- task-specific reasoning instructions

The prompt is passed to the **LLM Reasoning Module**, which produces a structured decision, such as:
- generating a final answer
- requesting additional retrieval
- abstaining due to insufficient evidence

Only chunk-level evidence is visible to the language model during reasoning.

---

### 7. Decision Handling and Iterative Control

If the LLM requests further retrieval, the agent executes the corresponding retrieval action and continues the inference loop using the existing agent state.

If the LLM produces an answer, the agent terminates the loop and proceeds to response formatting.

---

### 8. Citation Aggregation and UI Response

For answer generation, the agent:
- groups retrieved chunks by paper identifier
- assigns stable citation indices
- formats references at the paper level

The final output consists of a natural language answer and structured citations, which are returned to the user interface and displayed as the final response.
