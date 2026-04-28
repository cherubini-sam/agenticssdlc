---
id: skills_test_authoring
description: "Test design — pyramid balance, authoring discipline, coverage, determinism, contract and mutation testing."
type: skill
---

## Scope

A test suite is an executable specification: it earns its keep by failing reliably when behaviour breaks and passing reliably when behaviour holds.

## Test Pyramid

| Layer | Purpose | Speed | Share |
| :--- | :--- | :--- | :--- |
| Unit | One module, dependencies stubbed | Under 50 ms | About 70% |
| Integration | Multiple real components wired together | Under 2 s | About 20% |
| End-to-end | Full system from entry point to persistence | Under 30 s | About 10% |

Inverted pyramids — mostly end-to-end — produce slow, flaky, expensive suites.

## Authoring Discipline

Test name states expected behaviour. Arrange minimal state; act once; assert one outcome. No order dependence, shared state, real network, or wall-clock time.

## Coverage Targets

| Metric | Target |
| :--- | :--- |
| Line coverage on changed code | At least 85% |
| Branch coverage on changed code | At least 75% |
| Mutation score on critical modules | At least 60% |
| New behavioural lines without a test | Zero |

Coverage is a guard-rail — a test exercising code without asserting outcomes is worse than no test.

## Determinism

Inject the clock and seeded randomness — never call wall-clock or global random directly. Wait on explicit conditions, never sleep. Failure messages name expected and actual. A failing test reproduces on a clean checkout.

## Contract Testing

Consumer publishes interactions; provider verifies in the build. Failure blocks merge. Schema contracts enforced by registry.

## Mutation Testing

Synthetic faults injected; a test must fail for each. Surviving mutants signal a gap. Run on critical modules per commit; full suite nightly.

## Source

Cohn, Succeeding with Agile (Ch. 16), 2009; Beck, TDD, 2002; Meszaros, xUnit Test Patterns, 2007; Pact Foundation; Stryker / PIT mutation tooling.
