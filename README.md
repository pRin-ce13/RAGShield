# RAGShield

> **Automated Security Testing and Vulnerability Assessment Platform for RAG Applications**

[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![Status](https://img.shields.io/badge/status-Phase%203%20(Attack%20Library%20Complete)-green.svg)]()
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()

---

## 📌 Overview

**RAGShield** is an automated security evaluation platform designed to test the safety, resilience, and data boundaries of Retrieval-Augmented Generation (RAG) applications.

As enterprises adopt LLMs connected to proprietary knowledge bases, RAG architectures introduce new security vectors. RAGShield acts as a controlled testing harness that probes RAG systems for vulnerabilities such as prompt injection, unauthorized cross-tenant data retrieval, synthetic secret disclosure, and retrieval manipulation.

---

## 🎯 Key Objectives

1. **Target Agnostic Testing**: Connect to RAG targets via modular, configurable HTTP adapters.
2. **Deterministic & Semantic Evaluators**: Combine deterministic pattern checks and access-policy assertions with optional LLM-assisted evaluation.
3. **Reproducible Security Evidence**: Capture input payloads, observed outputs, execution metadata, and confidence scores without storing sensitive target data.
4. **Actionable Remediation**: Produce vulnerability reports mapped to OWASP LLM Top 10 categories with clear remediation guidance.
5. **Responsible Testing**: Built-in scan rate limits, network boundary validation (SSRF defense), synthetic document isolation, and audit logging.

---

## 🏗️ Architecture Roadmap

RAGShield is developed modularly across structured phases:

```text
RAGShield/
├── frontend/        # React + TypeScript security dashboard (Phase 8)
├── backend/         # FastAPI REST service & scan management (Phase 7)
├── engine/          # Security testing engine, attacks, & evaluators (Phases 2-6)
├── demo-rag/        # Local demonstration RAG target (Phase 1)
├── datasets/        # Synthetic documents & test cases (Phase 3)
└── docs/            # Architecture guides, living tech stack, & phase reports
```

---

## 🚦 Current Status: Phase 3 (Attack Library Complete)

- [x] Phase 0: Project Discovery & Setup (Git, `.gitignore`, `.venv`, initial docs).
- [x] Phase 1: RAG Fundamentals & Demonstration Target (`demo-rag/` with ChromaDB, chunking, grounded generation).
- [x] Phase 2: Target Adapter & Integration (`engine/targets/` HTTP adapter, SSRF defense, FastAPI REST demo).
- [x] Phase 3: Test-Case Model & Attack Library (`engine/attacks/` Pydantic schema, OWASP mapping, 11 parameterized test cases).
- [ ] Phase 4: Scan Orchestration & Execution (Concurrent scan runner, rate limits, progress tracking).

---

## 🛠️ Local Setup Guide

### 1. Prerequisites
- **Python 3.12+**
- **Git**

### 2. Clone and Setup Environment

```powershell
# Clone the repository
git clone <your-repo-url>
cd RAGShield

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment (Windows PowerShell)
.\.venv\Scripts\Activate.ps1

# Create your local environment configuration
copy .env.example .env
```

---

## 📚 Documentation Index

- [Project Context & Roadmap](docs/PROJECT_CONTEXT.md)
- [Project Overview](docs/PROJECT_OVERVIEW.md)
- [System Architecture](docs/ARCHITECTURE.md)
- [Tech Stack & Library Decisions](docs/TECH_STACK_AND_LIBRARIES.md)
- [Development Log](docs/DEVELOPMENT_LOG.md)
- [Interview Preparation Guide](docs/INTERVIEW_PREPARATION.md)
- [Phase Reports Directory](docs/phase-reports/)

---

## ⚖️ Responsible Use & Disclaimer

RAGShield is strictly designed for **authorized security testing and educational research**. Security assessments must only be conducted against systems you own or have explicit, written authorization to evaluate. All testing datasets use synthetic documents and dummy secrets.
