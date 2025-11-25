@./CLAUDE_CODE_SYSTEM_REQUIREMENTS.md
@./KB_FILE_STRUCTURE.md

# [PROJECT_NAME] - AI Assistant Guide

## Project Overview

**[PROJECT_NAME]** is [brief 1-2 sentence description of what this project does and its purpose].

**Key Information:**
- **Project Type:** [Web App / API / Data Pipeline / CLI Tool / Library / Mobile App / etc.]
- **Primary Language:** [Python / JavaScript / TypeScript / Go / Rust / etc.]
- **Framework:** [NextJS / FastAPI / Django / React / Express / etc.]
- **Deployment:** [AWS / GCP / Azure / Docker / Kubernetes / etc.]

### What This Project Does

[2-3 sentences explaining the main functionality and value proposition]

### Target Users

[Who will use this project? What problems does it solve for them?]

---

## Directory Structure

```
[project-name]/
├── [directory-name]/          # [Purpose and contents]
├── [directory-name]/          # [Purpose and contents]
├── [directory-name]/          # [Purpose and contents]
└── [README.md]                # [Project documentation]
```

### Key Directories

**[Directory Name 1]:** [Purpose]
- [What's in this directory]
- [Key files or subdirectories]

**[Directory Name 2]:** [Purpose]
- [What's in this directory]
- [Key files or subdirectories]

**[Directory Name 3]:** [Purpose]
- [What's in this directory]
- [Key files or subdirectories]

---

## Getting Started

### Prerequisites

- [Requirement 1] (version X.X or later)
- [Requirement 2] (version X.X or later)
- [Requirement 3]
- [Account/Service needed]

### Installation

```bash
# Clone the repository
git clone [repository-url]
cd [project-name]

# Install dependencies
[package-manager] install

# Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# Run setup scripts (if any)
[setup command]
```

### Running Locally

```bash
# Development mode
[dev command]

# Production mode
[prod command]

# Run tests
[test command]
```

---

## Development Workflow

### Standard Development Cycle

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make changes**
   - Follow coding standards in CLAUDE_CODE_SYSTEM_REQUIREMENTS.md
   - Write tests for new functionality
   - Update documentation

3. **Test locally**
   ```bash
   [test command]
   ```

4. **Commit changes**
   ```bash
   git add .
   git commit -m "Clear, descriptive commit message"
   ```

5. **Push and create PR**
   ```bash
   git push origin feature/your-feature-name
   # Create pull request on GitHub/GitLab
   ```

### Key Commands

```bash
# Development
[command]                    # [Description]
[command]                    # [Description]

# Testing
[command]                    # [Description]
[command]                    # [Description]

# Building
[command]                    # [Description]

# Deployment
[command]                    # [Description]
```

---

## Project Architecture

### High-Level Architecture

[Describe the main components and how they interact. Consider including:]
- System components
- Data flow
- External dependencies
- Integration points

### Technology Stack

**Backend:**
- [Technology 1]: [Purpose]
- [Technology 2]: [Purpose]

**Frontend:** (if applicable)
- [Technology 1]: [Purpose]
- [Technology 2]: [Purpose]

**Infrastructure:**
- [Service 1]: [Purpose]
- [Service 2]: [Purpose]

**Tools & Libraries:**
- [Tool 1]: [Purpose]
- [Tool 2]: [Purpose]

---

## Common Issues & Troubleshooting

### Issue 1: [Common Problem]

**Symptoms:** [How to recognize this problem]

**Cause:** [Why this happens]

**Solution:**
```bash
# Steps to fix
[command or action]
```

### Issue 2: [Common Problem]

**Symptoms:** [How to recognize this problem]

**Cause:** [Why this happens]

**Solution:**
```bash
# Steps to fix
[command or action]
```

### Issue 3: [Common Problem]

**Symptoms:** [How to recognize this problem]

**Cause:** [Why this happens]

**Solution:**
```bash
# Steps to fix
[command or action]
```

---

## Testing Strategy

### Test Structure

[Describe how tests are organized:]
- Unit tests location
- Integration tests location
- E2E tests location
- Test data/fixtures location

### Running Tests

```bash
# Run all tests
[test-all command]

# Run unit tests only
[unit-test command]

# Run integration tests
[integration-test command]

# Run specific test file
[test-specific command]

# Run with coverage
[coverage command]
```

### Testing Best Practices

1. [Practice 1]
2. [Practice 2]
3. [Practice 3]

---

## Deployment

### Deployment Environments

**Development:** [URL or description]
**Staging:** [URL or description]
**Production:** [URL or description]

### Deployment Process

```bash
# Deploy to [environment]
[deploy command]

# Verify deployment
[verify command]

# Rollback if needed
[rollback command]
```

### Environment Variables

Required environment variables:
- `[VAR_NAME]`: [Description and where to get value]
- `[VAR_NAME]`: [Description and where to get value]
- `[VAR_NAME]`: [Description and where to get value]

---

## Code Standards

See `CLAUDE_CODE_SYSTEM_REQUIREMENTS.md` for detailed technical requirements.

### Quick Reference

- **Language Version:** [Version]
- **Package Manager:** [npm / pip / cargo / go mod / etc.]
- **Code Style:** [Link to style guide or linter config]
- **Testing:** [Required coverage threshold]
- **Documentation:** [When and what to document]

---

## Contributing

### Code Review Process

1. Create feature branch
2. Make changes with tests
3. Submit pull request
4. Address review comments
5. Merge after approval

### Commit Message Format

```
[type]: [short description]

[optional longer description]

[optional footer with issue references]
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

---

## Additional Resources

### Documentation
- [Link to main documentation]
- [Link to API docs]
- [Link to architecture diagrams]

### External Resources
- [Technology documentation]
- [Tutorial or guide]
- [Community forum or chat]

### Getting Help

If you're stuck:
1. Check this guide and CLAUDE_CODE_SYSTEM_REQUIREMENTS.md
2. Search existing issues on [issue tracker]
3. Ask in [team channel / forum]
4. Contact [maintainer / team lead]

---

## Notes for AI Assistants (Claude Code)

When working with this project:

1. **Always read CLAUDE_CODE_SYSTEM_REQUIREMENTS.md** for technical standards
2. **Check KB_FILE_STRUCTURE.md** for project structure and file locations
3. **Follow the development workflow** outlined above
4. **Use the specified package manager** ([package manager])
5. **Run tests before suggesting deployment** ([test command])

Common patterns in this project:
- [Pattern 1]
- [Pattern 2]
- [Pattern 3]

Important considerations:
- [Consideration 1]
- [Consideration 2]
- [Consideration 3]

---

*Last Updated: [Date]*
*Project Version: [Version]*
