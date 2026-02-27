**AI Capacity Planning System (Agentic AI with LangGraph)**

An AI-driven capacity planning system that intelligently selects the best machine–operator combination to meet production targets within deadlines using Agentic AI, LangGraph, and LLM-based decision-making.

This project simulates a real-world manufacturing planning problem with learning from historical outcomes.

***Key Features***

Multi-agent workflow using LangGraph

Machine feasibility analysis based on availability, uptime, and risk

Operator–machine matching using efficiency scores

LLM-powered decision agent (Groq LLaMA 3.1)

Memory-based learning from past successes and failures

Fully runnable in Jupyter Notebook (.ipynb)

Easily extensible to FastAPI / Streamlit

**System Architecture**

Part Analysis Agent
        ↓
Machine Feasibility Agent
        ↓
Operator Matching Agent
        ↓
Memory Retrieval Agent
        ↓
Learning Agent
        ↓
LLM Selection Agent (Groq)
        ↓
Memory Update Agent
