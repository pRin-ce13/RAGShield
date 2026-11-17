# RAGShield: Project Overview

## 1. Problem Statement

Retrieval-Augmented Generation (RAG) is the leading design pattern for grounding Large Language Models (LLMs) in enterprise private data. In a typical RAG system:
1. User submits a query.
2. The system searches a vector store for semantically similar text chunks from internal documents.
3. The retrieved chunks are injected into the prompt context sent to the LLM.
4. The LLM produces an answer citing the retrieved facts.

### The Security Dilemma
While powerful, RAG introduces critical security risks:
- **Indirect Prompt Injection:** A malicious actor implants adversarial instructions in an indexed document (e.g. an uploaded PDF or web page). When another user's query retrieves that document, the LLM executes the attacker's embedded commands.
- **Access Control & Tenant Isolation Bypass:** A low-privileged user tricks the retrieval pipeline or LLM into fetching and summarizing documents from restricted departments (e.g., executive salaries or confidential M&A memos).
- **Synthetic Secret / PII Disclosure:** Attackers extract API keys, passwords, or synthetic personal records present in the knowledge base through iterative probing.
- **Retrieval Manipulation & Poisoning:** Attackers craft text designed to maximize cosine similarity and out-rank legitimate documents, misleading the LLM.

Currently, security teams test these systems either through manual ad-hoc prompting (slow, incomplete, unrepeatable) or generic web application scanners that fail to comprehend LLM/RAG semantics.

---

## 2. The Solution: RAGShield

**RAGShield** is an automated, repeatable security testing platform specifically built for RAG applications. It acts like a specialized security vulnerability scanner (similar to what Burp Suite or OWASP ZAP is for web apps) tailored specifically for RAG and LLM systems.

### Core Capabilities
1. **Configurable Target Adapters:** Connects to any RAG system exposing an HTTP endpoint.
2. **Standardized Test Suites:** Contains parameterized test cases covering direct injection, indirect injection, secret leakage, and access control boundaries.
3. **Multi-Method Evaluation Engine:** Employs deterministic exact matching, regex/pattern assertions, access control rules, and optional LLM-as-judge checks.
4. **Evidence-Based Reporting:** Captures full request/response trails, severity ratings, confidence levels, and OWASP LLM Top 10 mappings.
5. **Remediation Playbooks:** Suggests actionable guardrails (e.g., input sanitization, chunk filtering, retrieval access control, output guardrails).

---

## 3. Guiding Engineering Principles

- **No Premature Complexity:** We build each component step-by-step as needed.
- **Safety by Default:** Testing targets must be explicitly authorized. Scans enforce conservative rate limits, SSRF blocking, and timeouts.
- **Synthetic Data Exclusively:** All tests, knowledge bases, and dummy credentials use synthetic, harmless mock data.
