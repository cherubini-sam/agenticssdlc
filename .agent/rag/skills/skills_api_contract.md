---
id: skills_api_contract
description: "Interface design — resource shape, idempotency, error semantics, versioning."
type: skill
---

## Scope

An API contract is the negotiated interface between a producer and its consumers. A well-formed contract behaves predictably under retry, fails in machine-readable ways, and survives consumer change without coordinated redeploys.

## Resource & Operation Shape

| Property | Direction |
| :--- | :--- |
| Resource naming | Plural nouns for collections; stable opaque identifiers for items |
| Operation semantics | One verb per operation — create, read, update, delete, list, search, action |
| Action verbs | Sub-resource pattern; never overload an existing verb |
| Field naming | One casing convention per contract |

## Idempotency

| Operation | Required Property |
| :--- | :--- |
| Read | Safe and idempotent |
| Create | Accepts a client-supplied idempotency key; duplicate keys return the original result |
| Update (full replace) | Same body produces same end state |
| Update (partial) | Documented merge semantics (RFC 7396 or RFC 6902) |
| Delete | No-op on a missing resource |
| Long-running | Returns an operation handle; status polled separately |

## Error Semantics

Single consistent error schema across endpoints. RFC 9457 Problem Details: `type`, `title`, `status`, `detail`, `instance`. Stable machine-readable `code` independent of the HTTP status. Per-field structured validation errors. No secrets, tokens, internal paths, or stack frames in error bodies.

## Versioning

| Change | Compatibility | Allowed Where |
| :--- | :--- | :--- |
| Add optional field, add endpoint | Backwards-compatible | Same version |
| Tighten validation, remove or rename field, change type, change default | Breaking | New version only |

URL-path or media-type versioning, declared once and applied uniformly. Mixed strategies confuse consumers and tooling.

## Source

IETF RFC 9457 (2023); RFC 7396 (2014); RFC 6902 (2013).
