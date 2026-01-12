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

