<protocol_framework name="protocols_evaluation">

<meta>
  <id>"protocols_evaluation"</id>
  <description>"Agent evaluation metrics and self-assessment protocols."</description>
  <globs>[]</globs>
  <alwaysApply>false</alwaysApply>
  <tags>["type:protocol", "evaluation", "quality", "metrics"]</tags>
  <priority>"LOW"</priority>
  <version>"1.0.0"</version>
</meta>

<axiom_core>

### EVALUATION PROTOCOL [THE JUDGE]

<scope>Defines scoring dimensions, self-evaluation checklists, and output report format for agent quality assessment.</scope>

#### 1. Evaluation Dimensions & Scoring

| Dimension    | Definition                      | Measurement               | Weight |
| :----------- | :------------------------------ | :------------------------ | :----- |
| Accuracy     | Output correctness vs expected  | % correct assertions      | 30%    |
| Completeness | All requirements addressed      | % requirements satisfied  | 25%    |
| Efficiency   | Resource usage vs baseline      | Tokens used / optimal     | 20%    |
| Safety       | No policy violations            | Binary (pass/fail)        | 15%    |
| Latency      | Response time within limits     | Actual vs threshold       | 10%    |

`final_score = accuracy*0.30 + completeness*0.25 + efficiency*0.20 + safety*0.15 + latency*0.10`

| Score     | Grade | Action              |
| :-------- | :---- | :------------------ |
| 0.95–1.00 | A+    | Approve             |
| 0.90–0.94 | A     | Approve             |
| 0.80–0.89 | B     | Approve with notes  |
| 0.70–0.79 | C     | Review recommended  |
| 0.50–0.69 | D     | Refinement required |
| 0.00–0.49 | F     | Reject              |

#### 2. Self-Evaluation Checklist

**Pre-Response:** Routing JSON first (Law 1) | Language matches user (Law 18) | No emojis (Law 22) | No placeholders (Law 11) | Thinking tags for complex tasks (Law 10).
**Post-Response:** Target agent executed (Law 9) | Artifacts in correct location (Law 5).

#### 3. Evaluation Report Format

```markdown
# EVALUATION REPORT
## Task Summary
- **Task:** code_review | **Agent:** VALIDATOR | **Duration:** 1250 | **Tokens:** 1500/500/2000
## Dimension Scores
| Dimension | Score | Weight | Weighted |
## Grade: [Letter] | Issues: [...] | Recommendations: [...]
```

</axiom_core>
<authority_matrix>

### INTEGRATION & BENCHMARK AUTHORITY

<scope>Defines REFLECTOR routing rules and external benchmark alignment for evaluation governance.</scope>

#### 4. Reflector Integration

Route to REFLECTOR when: quality score <0.80 | security-sensitive output | architecture decisions | multi-file changes | user requests review.

`Output Self-Evaluate Score <0.80 REFLECTOR | Score ≥0.80 Approve`

#### 5. Benchmark Alignment

**GAIA:** Reasoning, multi-modality, web browsing, tool use.
**HAL:** Coding, web navigation, science, customer service.

</authority_matrix>
<compliance_testing>

### FEEDBACK LOOP

<scope>Continuous improvement cycle to track quality scores and identify recurring failure patterns.</scope>

#### 6. Feedback Loop

`Execute  Evaluate  Log  Analyze  Improve  (repeat)`
Track: Avg quality score/agent | common failure patterns | improvement rate after reflection | user satisfaction.

</compliance_testing>

<cache_control />

</protocol_framework>
