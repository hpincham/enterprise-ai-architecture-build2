# ADR-004: Guardrails, Usage Controls, and Observability for Enterprise AI Gateway

## Status
Accepted

## Date
2025-XX-XX

## Context

Enterprise AI systems introduce unique operational and risk challenges that do not exist in typical API integrations:

- Cost can scale rapidly with token usage, concurrency, and prompt size
- Misuse (intentional or accidental) can cause data leakage or policy violations
- Model outputs may be unsafe, inaccurate, or contextually inappropriate
- Debugging can pressure teams to log prompts/responses, increasing privacy risk
- Rate limits and throttling are common and must be handled gracefully

Because the Enterprise AI Gateway is the central access point for Azure OpenAI, it must implement baseline guardrails to ensure:

- Predictable cost behavior
- Safe and compliant usage
- Operational supportability and auditability
- Clear seams for future policy enforcement

---

## Decision

We will implement a layered guardrail strategy across three planes:

1. **Application-level guardrails (in the gateway)**
   - Maximum prompt size (character or token approximations)
   - Maximum `max_tokens` per request (hard clamp)
   - Per-user and/or per-client rate limiting
   - Request validation and safe defaults (temperature, system prompts, etc.)
   - Structured logging of metadata (not content) for operations

2. **Platform-level controls (Azure)**
   - Budget alerts at the subscription/resource group level
   - Quotas and rate limits as available for Azure OpenAI deployments
   - Resource tagging for cost allocation and governance

3. **Operational observability controls**
   - Centralized telemetry collection via Application Insights / Log Analytics
   - Dashboards for latency, error rates, request volume, and token usage
   - Alerts for high error rates, throttling, and unusual usage patterns

The gateway will **not** log full prompt or response content by default.

---

## Rationale

### Cost Predictability
- Token usage is directly tied to cost; guardrails prevent runaway spend.
- Hard limits reduce risk from accidental loops, oversized prompts, and excessive completions.

### Risk & Compliance
- Guardrails provide a first line of protection against misuse.
- Minimizing content logging reduces the risk of capturing sensitive data in telemetry systems.

### Operational Supportability
- Structured metadata logs enable troubleshooting without collecting sensitive content.
- Standard dashboards and alerts reduce mean time to detect (MTTD) and resolve (MTTR).

### Enterprise Consistency
- This mirrors established API patterns: validation, throttling, observability, and cost allocation.

---

## Guardrail Baseline (Build 2)

The following controls are mandatory in Build 2:

### Input Controls
- Prompt size limit (e.g., 4,000 characters)
- Request schema validation (required fields, type constraints)
- Optional allow-list of model deployments (one deployment to start)

### Output Controls
- Hard clamp for `max_tokens` (e.g., <= 800)
- Safe defaults for generation parameters (e.g., temperature <= 0.3)
- Return errors without exposing internals or sensitive details

### Rate Limiting
- Per-caller rate limits (e.g., N requests/minute)
- Stable caller key derived from `oid` / `sub` (hashed for logging)

### Logging (Privacy-Aware)
Log:
- request id (correlation)
- hashed caller id
- endpoint path
- status code
- latency
- model deployment name
- token usage totals (when available)

Do NOT log by default:
- prompt content
- response content
- user emails/UPN
- attachments or source documents

### Error Handling
- Graceful handling of throttling and timeouts
- Clear client-facing errors (429, 503, 500) without leaking internals
- Retry policy handled by clients or later gateway enhancements (explicitly documented)

---

## Observability Requirements

We will implement:
- Application Insights / Log Analytics integration
- A minimal dashboard showing:
  - request volume
  - success/error rate
  - p95 latency
  - token usage per day (or per period)
- Alerts for:
  - sustained elevated error rate
  - sustained throttling events
  - abnormal request volume

---

## Cost Controls (Azure)

We will implement:
- Subscription or resource group budget alert (email/action group)
- Resource tagging (application, owner, environment)
- Azure OpenAI quotas/limits when available/allowed by tenant policies

---

## Consequences

### Positive
- Reduced cost surprises and better accountability
- Safer system behavior and reduced misuse risk
- Better operational posture and faster troubleshooting
- A foundation for policy engines and mature governance

### Trade-offs
- Guardrails may block legitimate edge cases (by design)
- Some debugging becomes harder without content logs
- Rate limiting in-memory will not scale across multiple instances unless upgraded (e.g., Redis)

These trade-offs are acceptable; the baseline favors enterprise safety and predictability.

---

## Alternatives Considered

### No Guardrails (trust the client)
**Rejected.**
- Increases cost risk and governance gaps
- Encourages inconsistent implementations across teams

### Log Full Prompts/Responses for Debugging
**Rejected (default).**
- High privacy and compliance risk
- Increases sensitivity of telemetry platforms

A controlled “break-glass” diagnostic mode may be introduced later with explicit approvals.

### Rely Only on Azure Quotas
**Rejected (as sole mechanism).**
- Quotas help, but do not replace application-level policy enforcement and observability.

---

## Related Decisions
- ADR-001: AI Access Patterns
- ADR-002: Centralized AI Gateway Pattern
- ADR-003: Authentication & Authorization for Enterprise AI Gateway

---

## Notes / Future Enhancements

Planned future improvements include:
- Redis-backed distributed rate limiting for scale-out deployments
- Content safety integration and policy enforcement (Azure AI Content Safety or equivalent)
- Prompt template registry and versioning
- Per-tenant segmentation and routing
- Automated cost anomaly detection
