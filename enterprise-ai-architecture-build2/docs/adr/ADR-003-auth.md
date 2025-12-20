# ADR-003: Authentication & Authorization for Enterprise AI Gateway

## Status
Accepted

## Date
2025-XX-XX

## Context

The Enterprise AI Gateway is a shared service that mediates access between enterprise users/applications and Azure OpenAI. Because it becomes a central control point, its authentication and authorization model must be:

- Enterprise-standard (compatible with corporate identity practices)
- Consistent across consumers (apps, users, services)
- Auditable and supportable
- Designed to eliminate secret sprawl
- Compatible with future policy enforcement and governance

The organization uses Microsoft Entra ID as the enterprise identity provider. The gateway will be hosted in Azure and will call Azure OpenAI.

---

## Decision

We will implement a two-tier authentication model:

1. **Caller → Gateway (User/App authentication)**
   - The gateway will require a valid **Entra ID access token** (OAuth 2.0 / OpenID Connect).
   - Tokens are validated server-side by the gateway:
     - signature (JWKS)
     - issuer
     - audience
     - expiration

2. **Gateway → Azure OpenAI (Service-to-service authentication)**
   - The gateway will authenticate to Azure OpenAI using **Managed Identity** (system-assigned or user-assigned).
   - No API keys or embedded secrets will be used for Azure OpenAI access.

Authorization will be enforced at the gateway using:

- Role/claim-driven access decisions (initially minimal)
- A well-defined path to expand into RBAC/ABAC and policy-based controls as maturity increases

---

## Rationale

### Enterprise Compatibility
- Entra ID tokens align with standard enterprise authentication patterns.
- This approach supports both human users and application clients.

### Reduced Secret Sprawl
- Managed Identity eliminates static API keys and reduces the need for secret distribution and rotation.

### Auditability and Governance
- Central token validation produces consistent, traceable access decisions.
- Supports later introduction of:
  - group-based access
  - per-user/per-app quotas
  - policy enforcement per tenant or business unit

### Operational Simplicity
- The gateway becomes the single enforcement point for identity and access.
- Troubleshooting is simplified by correlating:
  - token claims (non-sensitive)
  - request IDs
  - usage telemetry

---

## Authorization Model (Build 2)

Build 2 intentionally starts with a minimal authorization model:

- Only authenticated callers may access the `/chat` endpoint.
- Requests include a stable identity key (e.g., `oid` or `sub`) to support:
  - per-user rate limiting
  - usage attribution
- Sensitive identity data (email/UPN) will not be logged by default.

**Note:** Authorization decisions will be expanded in later builds based on enterprise governance needs. This ADR defines the baseline and extension points.

---

## Implementation Notes

### Token Validation Requirements
The gateway validates incoming JWT access tokens using:
- Entra JWKS endpoint for signing keys
- Allowed issuer list (tenant v2 endpoint)
- Audience (API Application ID URI or client ID)
- Expiration and basic integrity checks

### Identity Claim Selection
To uniquely identify the caller without logging personal data:
- Prefer `oid` (object ID) when available
- Fall back to `sub`
- Derive a **stable hash** for logging and rate-limiting keys

### Service-to-Service Authentication
The gateway uses Managed Identity to obtain an access token for:
- `https://cognitiveservices.azure.com/.default`

This token is used to call Azure OpenAI endpoints.

---

## Consequences

### Positive
- Centralized enterprise authentication and consistent enforcement
- Reduced security risk via elimination of API keys
- Clean audit trail and operational visibility
- Clear extension points for RBAC/ABAC and policy controls

### Trade-offs
- Requires Entra app registration and token configuration
- Token validation and JWKS caching introduce some implementation complexity
- Authorization logic must be deliberately designed to avoid over-permissive access

These trade-offs are acceptable given the risk reduction and governance benefits.

---

## Alternatives Considered

### API Key Authentication to Azure OpenAI
**Rejected.**
- Encourages secret sprawl and rotation burden
- Increases risk of key leakage
- Harder to audit and attribute usage

### Client-Side Direct Authentication to Azure OpenAI
**Rejected.**
- Weakens governance and control
- Complicates observability and consistent policy enforcement
- Increases attack surface

### Per-Application Credentials (one key per app)
**Rejected (for baseline).**
- Still increases secret management overhead
- Does not provide centralized enforcement as effectively as Managed Identity

---

## Related Decisions
- ADR-001: AI Access Patterns
- ADR-002: Centralized AI Gateway Pattern
- ADR-004: Guardrails and Usage Controls (rate limits, quotas, token caps)

---

## Notes / Future Enhancements

Potential future enhancements include:
- Group-based authorization using Entra groups (with careful handling of token size limits)
- “On-behalf-of” flow when acting as a user across downstream services
- Attribute-based access control (ABAC) via policy engine integration
- Per-tenant / per-business-unit segregation and routing
