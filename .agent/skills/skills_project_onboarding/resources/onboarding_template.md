# Project Reconnaissance: [Project Name]

## Architecture

- **Type:** [Monolith/Microservices/Library/Monorepo/Plugin Architecture]
- **Stack:** [Language/Framework/Version]
- **Package Manager:** [pip/npm/yarn/cargo/etc]
- **Build Tool:** [webpack/vite/make/etc]

## Key Landmarks

### Entry Points

- **Main:** `[path/to/main.py or index.ts]`
- **API:** `[path/to/api/routes.py]`
- **CLI:** `[path/to/cli.py]`

### Configuration Files

- **Environment:** `[.env.example, config/]`
- **Dependencies:** `[requirements.txt, package.json]`
- **Build:** `[webpack.config.js, Makefile]`

### Core Modules

- `[src/core/]` - Core business logic
- `[src/api/]` - API endpoints
- `[src/models/]` - Data models
- `[src/utils/]` - Utilities

## Dependencies

### Production

- **Count:** [X] packages
- **Notable:**
  - `[framework-name]` v[X.X.X] - [Purpose]
  - `[library-name]` v[X.X.X] - [Purpose]

### Development

- **Count:** [X] packages
- **Notable:**
  - `[testing-framework]` - Testing
  - `[linter]` - Code quality

## Health Check

- **Tests:** PASS/FAIL ([XX]% coverage)
  - Framework: [pytest/jest/etc]
  - Location: `tests/`
- **Documentation:** PASS/FAIL
  - README: PASS/FAIL
  - Contributing Guide: PASS/FAIL
  - API Docs: PASS/FAIL
- **CI/CD:** PASS/FAIL
  - Platform: [GitHub Actions/GitLab CI/etc]
  - Config: `[.github/workflows/]`
- **Linting:** PASS/FAIL
  - Tools: [eslint, prettier, black, etc]
- **Environment Setup:** PASS/FAIL
  - Docker: PASS/FAIL
  - Env Template: PASS/FAIL

## Project Statistics

- **Total Files:** [X]
- **Total Lines:** [X]
- **Languages:**
  - [Language]: [XX]%
  - [Language]: [XX]%

## Integration Points

### External APIs

- [API Name] - [Purpose]
- [API Name] - [Purpose]

### Databases

- [Database Type] - [Connection details location]

### Services

- [Service Name] - [Purpose]

## Quick Start

### Prerequisites

```bash
[List required tools/versions]
```

### Installation

```bash
# Clone repository
git clone [repo-url]

# Install dependencies
[package-manager install command]

# Setup environment
cp .env.example .env
# Edit .env with your configuration
```

### Running Locally

```bash
# Development server
[command to start dev server]

# Run tests
[command to run tests]

# Build for production
[command to build]
```

## Development Workflow

1. **Create Feature Branch:** `git checkout -b feature/your-feature`
2. **Make Changes:** Edit code and add tests
3. **Run Tests:** `[test command]`
4. **Lint Code:** `[lint command]`
5. **Commit:** `git commit -m "feat: your feature"`
6. **Push:** `git push origin feature/your-feature`
7. **Create PR:** Open pull request for review

## Common Commands

```bash
# Run development server
[dev command]

# Run tests
[test command]

# Run linter
[lint command]

# Build production
[build command]

# Database migrations (if applicable)
[migration command]
```

## Troubleshooting

### Common Issues

**Issue:** [Common problem]
**Solution:** [How to fix]

**Issue:** [Common problem]
**Solution:** [How to fix]

## Additional Resources

- **Documentation:** [Link to docs]
- **API Reference:** [Link to API docs]
- **Contributing Guide:** [Link to CONTRIBUTING.md]
- **Issue Tracker:** [Link to issues]
