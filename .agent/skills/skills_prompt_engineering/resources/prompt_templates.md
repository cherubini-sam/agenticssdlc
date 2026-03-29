# Prompt Templates

## Code Review Prompts

### Basic Code Review

```
Review this code for quality and best practices:

<code>
{code}
</code>

Focus on:
- Code clarity and readability
- Potential bugs or edge cases
- Performance considerations
- Security vulnerabilities

Provide specific, actionable feedback.
```

### Security-Focused Review

```
Perform a security audit of this code:

<code>
{code}
</code>

Check for:
- SQL injection vulnerabilities
- XSS attacks
- Authentication/authorization issues
- Sensitive data exposure
- Input validation gaps

Rate severity: CRITICAL, HIGH, MEDIUM, LOW
```

## Refactoring Prompts

### Extract Functions

```
Refactor this code by extracting reusable functions:

<code>
{code}
</code>

Guidelines:
- Functions should be <20 lines
- Single responsibility principle
- Descriptive names
- Add type hints (Python) or TypeScript types
```

### Improve Readability

```
Refactor for maximum readability:

<code>
{code}
</code>

Apply:
- Meaningful variable names
- Extract magic numbers to constants
- Add comments for complex logic
- Simplify nested conditions
```

## Documentation Prompts

### Generate Docstrings

```
Add comprehensive docstrings to this code:

<code>
{code}
</code>

Format: Google style docstrings
Include:
- Brief description
- Args with types
- Returns with type
- Raises (if applicable)
- Example usage
```

### API Documentation

```
Generate API documentation for this endpoint:

<code>
{code}
</code>

Include:
- Endpoint URL and method
- Request parameters
- Request body schema
- Response schema
- Example request/response
- Error codes
```

## Test Generation Prompts

### Unit Tests

```
Generate unit tests for this function:

<code>
{code}
</code>

Requirements:
- Test framework: {framework}
- Cover edge cases
- Test error handling
- Aim for >90% coverage
- Include setup/teardown if needed
```

### Integration Tests

```
Create integration tests for this module:

<code>
{code}
</code>

Test:
- Happy path scenarios
- Error conditions
- External dependencies (mocked)
- Data validation
```

## Debugging Prompts

### Root Cause Analysis

```
Analyze this error and identify the root cause:

<error>
{error_message}
</error>

<stack_trace>
{stack_trace}
</stack_trace>

<code>
{relevant_code}
</code>

Provide:
1. Root cause explanation
2. Why it occurred
3. Specific fix
4. Prevention strategy
```

### Performance Debugging

```
Identify performance bottlenecks in this code:

<code>
{code}
</code>

Analyze:
- Time complexity
- Space complexity
- Unnecessary operations
- Optimization opportunities

Suggest specific improvements with expected impact.
```

## Code Generation Prompts

### From Specification

```
Implement this specification:

<spec>
{specification}
</spec>

Requirements:
- Language: {language}
- Follow {style_guide} style guide
- Include error handling
- Add type hints/annotations
- Write self-documenting code
```

### Boilerplate Generation

```
Generate boilerplate code for:

Type: {type}  # e.g., REST API, CLI tool, data processor
Language: {language}
Framework: {framework}

Include:
- Project structure
- Configuration files
- Entry point
- Basic error handling
- Logging setup
```

## Optimization Prompts

### Algorithm Optimization

```
Optimize this algorithm for better performance:

<code>
{code}
</code>

Current complexity: {current_complexity}
Target: Reduce time/space complexity

Constraints:
- Maintain correctness
- Preserve functionality
- Explain trade-offs
```

### Database Query Optimization

```
Optimize this database query:

<query>
{query}
</query>

<schema>
{schema}
</schema>

Improve:
- Execution time
- Index usage
- Join efficiency
- Query plan

Explain the optimizations.
```

## Conversion Prompts

### Language Translation

```
Convert this code from {source_lang} to {target_lang}:

<code>
{code}
</code>

Maintain:
- Functionality
- Idiomatic style for target language
- Error handling
- Comments/documentation
```

### Framework Migration

```
Migrate this code from {old_framework} to {new_framework}:

<code>
{code}
</code>

Ensure:
- Feature parity
- Best practices for new framework
- Updated dependencies
- Migration notes
```

## Prompt Template Variables

Common variables to use in prompts:

- `{code}` - Code to analyze/modify
- `{language}` - Programming language
- `{framework}` - Framework name
- `{error_message}` - Error text
- `{stack_trace}` - Stack trace
- `{specification}` - Requirements/spec
- `{style_guide}` - Style guide name
- `{complexity}` - Complexity notation
- `{schema}` - Database schema
- `{query}` - SQL query
