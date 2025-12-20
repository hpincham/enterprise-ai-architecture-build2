# ADR-002: Centralized AI Gateway Pattern

## Status
Accepted

## Date
2025-XX-XX

## Context

As enterprise teams begin adopting AI capabilities, a common early pattern is to embed direct calls to AI services (e.g., Azure OpenAI) inside individual applications.

This approach creates several systemic risks:

- AI access credentials are distributed across multiple applications
- Identity enforcement is inconsistent or absent
- Cost visibility is fragmented
- Logging and auditability vary by implementation
- Governance changes require updates across many systems

To support secure, scalable, and governable AI adoption, a centralized architectural pattern is required.

---

## Decision

We will introduce a **centralized AI Gateway** that acts as the sole ingress point between enterprise applications/users and Azure OpenAI services.

All AI requests will flow through this gateway, which is responsible for:

- Validating enterprise identity (Microsoft Entra ID)
- Enforcing access and usage guardrails
- Managing authentication to Azure OpenAI using managed identity
- Providing consistent logging and observability
- Establishing a stable control plane for future AI capabilities

Applications will **not** call Azure OpenAI directly.

---

## Architecture Pattern

The AI Gateway sits logically between:

- **Enterprise users and applications**
- **Azure OpenAI and supporting AI services**

The gateway exposes a small, well-defined API surface and encapsulates AI-specific concerns, allowing downstream applications to remain simpler and more secure.

This pattern aligns with established enterprise practices such as:
- API gateways
- Shared service layers
- Centralized identity and policy enforcement

---

## Rationale

This decision was driven by the following considerations:

### Security
- Centralized identity validation using Entra ID
- Elimination of API keys or secrets in application code
- Reduced attack surface

### Governance
- Single point to apply usage policies, rate limits, and prompt constraints
- Consistent enforcement of AI safety and compliance controls

### Cost Management
- Centralized visibility into token usage and model consumption
- Ability to introduce quotas, budgets, and throttling mechanisms

### Operability
- Standardized logging, metrics, and error handling
- Clear ownership and support boundaries
- Easier troubleshooting and incident response

### Evolvability
- Future capabilities (RAG, policy engines, agent orchestration) can be added without modifying client applications
- Supports incremental maturity rather than one-time redesigns

---

## Consequences

### Positive
- Predictable and governable AI adoption
- Reduced duplication of AI integration logic
- Strong alignment with enterprise architecture standards
- Clear separation of concerns

### Trade-offs
- Introduces an additional hop in request flow
- Requires initial platform investment
- Becomes a critical shared service that must be designed for reliability

These trade-offs are acceptable given the long-term operational and governance benefits.

---

## Alternatives Considered

### Direct Application-to-AI Integration
**Rejected.**

While simpler initially, this approach leads to:
- Credential sprawl
- Inconsistent controls
- Poor cost visibility
- High long-term maintenance burden

### Client-Side AI Access
**Rejected.**

Allowing browsers or thick clients to call AI services directly:
- Increases security risk
- Complicates identity enforcement
- Makes governance and auditing difficult

---

## Related Decisions
- ADR-001: AI Access Patterns
- ADR-003: Authentication and Authorization Strategy
- ADR-004: Guardrails and Usage Controls

---

## Notes

This ADR establishes the **foundational control plane** for enterprise AI usage.

Subsequent builds will expand on this pattern to introduce:
- Retrieval-Augmented Generation (RAG)
- Policy-based prompt management
- Multi-tenant routing and segmentation
