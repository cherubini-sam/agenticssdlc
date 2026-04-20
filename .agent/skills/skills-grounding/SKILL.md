---
name: skills-grounding
description: "Fact verification and deep web research with provider-agnostic search and citation protocol."
---

## 1. Grounding Protocol

1. **Query Analysis** — Identify the claims to verify; extract fresh, specific search terms.
2. **Search Execution** — Generate 2–3 targeted queries. Prioritize official docs and GitHub (>1K stars).
3. **Result Processing** — Cross-reference top 2–3 results; note any disagreements between sources.

## 2. Provider Configuration

```json
{
  "grounding_enabled": true,
  "grounding_provider": "${GROUNDING_PROVIDER:-google}",
  "providers": {
    "google": { "dynamic_retrieval_threshold": 0.5 },
    "tavily": { "search_depth": "advanced" },
    "bing": { "market": "en-US" },
    "serpapi": { "engine": "google" }
  },
  "include_citations": true,
  "max_citations": 5
}
```

## 3. Research Loop (Deep Research)

Do NOT rely on a single search query.

1. **Deconstruct** — Break complex query into 3 focused sub-questions.
2. **Execute** — Run 3 parallel searches; read top 2 results per query.
3. **Synthesize** — Combine findings; flag contradictions.
4. **Refine** — If answer is shallow, re-query with more specific terms.

## 4. Citation Protocol

- Format: `[Title](URL)`
- NEVER cite a URL you haven't visited via `read_url_content`.
- Remove any 404 URLs before outputting.
- On 403/404: retry with alternative queries until valid content is retrieved.

## 5. Source Reliability Hierarchy

| Priority | Source Type             | Reliability       |
| :------- | :---------------------- | :---------------- |
| 1        | Official docs           | Highest           |
| 2        | GitHub (stars >1K)      | High              |
| 3        | Technical blogs (corps) | Medium-High       |
| 4        | Stack Overflow          | Medium            |
| 5        | Reddit / Forums         | Low (errors only) |
