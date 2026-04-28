---
id: skills_security_review
description: "Application security — secrets, injection, authn/authz, supply chain, AI/LLM threats."
type: skill
---

## Scope

Security review walks five surfaces: secrets, injection, authn/authz, supply chain, and LLM threats when a model is in the request path.

## Findings

**Secrets** — Credential or token hardcoded in source, fixture, or config: CRITICAL. Secret in log or error: HIGH.

**Injection** — Unparameterised user input in a query: CRITICAL. User input in an external command without escaping: CRITICAL. Template rendered without contextual escaping: HIGH. Untrusted input deserialised via unsafe loader: HIGH.

**Authn/Authz** — Endpoint reachable without authentication: CRITICAL. Authorisation from client-supplied claims only: CRITICAL. Missing privilege check on a mutating operation: HIGH.

**Supply chain** — Dependency with known critical CVE: CRITICAL. SBOM absent or provenance unverified: HIGH. Artefacts not signed: HIGH.

**LLM** — Prompt injection via input or retrieved content: CRITICAL. Model output unsanitised to shell, DB, or browser: CRITICAL. Destructive tools without human confirmation: HIGH. Sensitive data in model context: HIGH.

## Severity Rules

CRITICAL stops the change. HIGH fixed in-change or documented with a compensating control. MEDIUM fixed or accepted with rationale.

## Required Mitigations

Secrets from a managed store. Parameterised queries; explicit argument lists. Server-side authorisation. Locked, CVE-scanned dependencies. SBOM plus signed provenance. LLM I/O untrusted; least-privilege tools; human confirmation for destructive actions.

## Source

OWASP SAMM v2.0; NIST SP 800-218 v1.1, 2022; OWASP Top 10; OWASP ASVS v4.0.3; OWASP Top 10 for LLM Applications, 2024; OpenSSF SLSA v1.0; CycloneDX/SPDX; CISA Secure-by-Design, 2023.
