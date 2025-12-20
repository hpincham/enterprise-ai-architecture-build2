# Enterprise AI Gateway – Build 2
A reference architecture for secure, governable, and cost-controlled enterprise AI using Azure OpenAI, Entra ID, managed identities, network controls, observability, and explicit cost guardrails.

This repository contains **Build 2** of my Enterprise AI Architecture portfolio:  
a production-oriented **AI Gateway / Control Plane** implemented with **FastAPI** and **Azure OpenAI**.

The goal of this build is to demonstrate how AI capabilities can be exposed to an enterprise in a way that is:

- Secure by default
- Governable and auditable
- Cost-aware
- Operable at scale
- Aligned with existing enterprise identity, network, and delivery patterns

This is not a demo chatbot. It is a **foundational system component**.

---

## Architecture Context

This gateway sits between enterprise users/applications and Azure OpenAI.

**Responsibilities include:**
- Centralized ingress for AI requests
- Identity validation using Microsoft Entra ID
- Controlled access to Azure OpenAI via managed identity
- Enforcement of basic guardrails (rate limits, token limits, prompt size)
- Structured, privacy-aware logging for observability
- Clear seams for future expansion (RAG, policy engines, multi-tenant routing)

This repository corresponds to **Build 2** in the broader architecture portfolio:

- **Build 1**: Reference Architecture & ADRs (published on clarusigna.com)
- **Build 2**: AI Gateway / Control Plane (this repo)
- **Build 3+**: RAG, policy enforcement, and advanced orchestration

---

## High-Level Flow

1. A client application calls the gateway
2. The gateway validates the caller’s Entra ID access token
3. Requests are evaluated against guardrails (rate, size, limits)
4. The gateway calls Azure OpenAI using **managed identity**
5. Responses are returned without logging sensitive content
6. Telemetry is emitted for latency, usage, and operational health

---

## Technology Choices

| Area | Choice | Rationale |
|-----|------|-----------|
| API Framework | FastAPI (Python) | Modern, expressive, widely adopted for AI services |
| Identity | Microsoft Entra ID | Enterprise-standard authentication & authorization |
| AI Platform | Azure OpenAI | Enterprise controls, networking, and compliance |
| Auth to AI | Managed Identity | Eliminates secret management |
| Deployment | Containerized App Service | Predictable, scalable runtime |
| Observability | App Insights / Log Analytics | Centralized operations |
| Automation | PowerShell | Repeatable infrastructure and ops workflows |

---

## Repository Structure
enterprise-ai-architecture-build2/
├── README.md
├── Dockerfile
├── requirements.txt
├── .env.example
├── docs/
│ ├── architecture.md
│ └── adr/
│ ├── ADR-002-gateway.md
│ ├── ADR-003-auth.md
│ └── ADR-004-guardrails.md
├── src/
│ ├── main.py
│ ├── auth.py
│ ├── openai_client.py
│ ├── guardrails.py
│ └── logging_config.py
└── scripts/
├── deploy-build2.ps1
├── smoketest-build2.ps1
└── logs-build2.ps1


---

## What This Build Intentionally Does *Not* Include (Yet)

- Retrieval-Augmented Generation (RAG)
- Vector databases
- Prompt orchestration frameworks
- Agentic workflows

Those are **Build 3+ concerns**.

This build focuses on getting the **control plane right first** — a common enterprise failure point.

---

## Running Locally (Developer Convenience)

> Local execution is supported for development and testing.  
> Production deployments rely on Azure Managed Identity.

1. Create a Python virtual environment
2. Install dependencies from `requirements.txt`
3. Copy `.env.example` to `.env` and populate values
4. Run with `uvicorn src.main:app --reload`

---

## Deployment

The service is designed to run as a containerized workload on Azure App Service.

Infrastructure provisioning, configuration, and validation are automated using PowerShell scripts in `/scripts`.

Deployment steps are intentionally explicit to mirror enterprise delivery practices.

---

## Why This Exists

Most organizations adopt AI by:
- embedding keys in apps
- bypassing identity controls
- losing cost visibility
- creating operational blind spots

This gateway demonstrates a **safer and more sustainable pattern**.

---

## Author

**Howard Pincham**  
Enterprise Systems Architect  
Focused on applying enterprise architecture discipline to AI-enabled systems

Portfolio and reference artifacts available at:  
https://clarusigna.com/


