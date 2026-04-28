---
id: skills_release_engineering
description: "Delivery discipline — CI, deployment strategy, rollback safety, DORA metrics."
type: skill
---

## Scope

Release engineering turns committed code into production behaviour predictably and reversibly — deterministic CI, risk-matched deployment, reliable rollback, DORA metrics.

## Continuous Integration

| Check | Direction |
| :--- | :--- |
| Trunk-based development | Short-lived branches; merge daily |
| Determinism | Build reproducible from the same commit on any agent |
| Required checks | Lint, type, unit, integration, security scan green before merge |
| Artefact identity | Build once; deploy the same artefact to every environment |
| Pipeline duration | Under 15 minutes from commit to deployable artefact |

## Deployment Strategies

| Strategy | When | Rollback |
| :--- | :--- | :--- |
| Rolling | Stateless, backwards-compatible change | Re-deploy previous artefact |
| Blue/green | Schema change or major behaviour | Flip traffic to idle colour |
| Canary | Risk at scale | Stop promotion; route to stable fleet |
| Feature flag | Behaviour decoupled from deploy | Flip the flag; no redeploy |
| Shadow | New code needs production load | Disable shadow consumer |

Every strategy declares explicit success and abort criteria before promotion.

## Rollback

Target the previous known-good artefact by hash or tag. Under 15 min for elite delivery. Database changes expand → contract so the previous artefact still runs. Forward-fix only when rollback is impossible.

## DORA Metrics (elite targets)

| Metric | Target |
| :--- | :--- |
| Deployment frequency | On demand (multiple per day) |
| Lead time for changes | Under one hour |
| Change failure rate | Under 15% |
| Mean time to restore | Under one hour |

All four improve together; trading failure rate for frequency is a regression.

## Source

Forsgren, Humble & Kim, Accelerate, 2018; DORA State of DevOps (annual); Humble & Farley, Continuous Delivery, 2010.
