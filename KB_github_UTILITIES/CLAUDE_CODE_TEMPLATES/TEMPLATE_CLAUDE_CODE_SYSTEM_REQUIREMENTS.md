# Claude Code System Requirements - [PROJECT_NAME]

## Project Overview

**[PROJECT_NAME]** is [brief description]. This document defines the system requirements and development standards for working with Claude Code on this project.

---

## PROGRAMMING SYSTEM REQUIREMENTS

### Code & Structure
- **Primary Language:** [Language] [Version]
- **Package Manager:** [npm / pip / cargo / poetry / uv / go mod / etc.]
- **Framework/Runtime:** [Framework name and version]
- **Build System:** [Webpack / Vite / Cargo / Make / etc.]
- **Code Organization:** [How code is structured - monorepo / multi-package / single app / etc.]
- **All code must be placed in the correct directory** per the project structure (see KB_FILE_STRUCTURE.md)

### Package Management (CRITICAL)

**[PACKAGE_MANAGER_NAME]** is the ONLY approved package manager for this project.

**ALWAYS use:**
```bash
[install command]      # Install/add dependencies
[run command]          # Execute scripts
[test command]         # Run tests
[build command]        # Build project
```

**NEVER use:**
- ❌ [Alternative package manager 1]
- ❌ [Alternative package manager 2]
- ❌ Direct language commands without package manager

### File Naming & Versioning
- **Naming convention:** [snake_case / camelCase / PascalCase / kebab-case]
- **File extensions:** [Preferred extensions for each file type]
- **Version control:** via git commits, not file naming
- **No version numbers in filenames** (use git history instead)

### Code Header Format (if applicable)

For [file types], include a header/comment at the top:

```[language]
[Comment syntax]
Module: [Module name]
Purpose: [Brief description]
[Other required fields]
```

---

## TESTING REQUIREMENTS

### Test Organization

```
[test-directory]/
├── unit/                   # Unit tests
├── integration/            # Integration tests
├── e2e/                    # End-to-end tests
└── fixtures/               # Test data and mocks
```

### Test Files
- **Location:** [Where test files live relative to source]
- **Naming:** [test_*.ext / *.test.ext / *.spec.ext / etc.]
- **Structure:** [How tests should be organized]

### Running Tests

```bash
# Run all tests
[test-all command]

# Run specific test type
[unit-test command]
[integration-test command]
[e2e-test command]

# Run with coverage
[coverage command]

# Run in watch mode
[watch command]
```

### Test Requirements
- **Coverage:** Maintain >[X]% code coverage
- **Test before commit:** All tests must pass
- **Test before deploy:** Run full test suite
- **Mock external dependencies** in unit tests

### Test-Driven Development
1. Write test first (TDD approach)
2. Implement functionality
3. Run tests: `[test command]`
4. Refactor if needed
5. Verify all tests pass

---

## DEVELOPMENT WORKFLOW

### Standard Development Cycle

1. **Understand the task**
   - Read relevant documentation
   - Understand existing code patterns
   - Ask clarifying questions if needed

2. **Create feature branch**
   ```bash
   git checkout -b [branch-naming-convention]
   ```

3. **Write tests first** (if applicable)
   - Create test file
   - Define expected behavior
   - Run tests (should fail initially)

4. **Implement code**
   - Follow existing patterns
   - Keep it simple (no over-engineering)
   - Write clear, self-documenting code

5. **Test locally**
   ```bash
   [test command]
   [lint command]
   [type-check command]
   ```

6. **Commit changes**
   ```bash
   git add [files]
   git commit -m "[commit message format]"
   ```

7. **Push and create PR**
   ```bash
   git push origin [branch-name]
   # Create pull request
   ```

### Git Workflow
- **Main branch:** `[main / master / develop]`
- **Branch naming:** `[feature/ / bugfix/ / hotfix/][description]`
- **Commit messages:** [Format: conventional commits / semantic / etc.]
- **No force push** to protected branches

---

## CODE QUALITY STANDARDS

### Code Style
- **Style guide:** [Link to style guide or name]
- **Linter:** [ESLint / Pylint / Clippy / etc.]
- **Formatter:** [Prettier / Black / rustfmt / gofmt / etc.]
- **Configuration:** [Where config files are located]

### Running Quality Checks

```bash
# Lint code
[lint command]

# Format code
[format command]

# Type check (if applicable)
[type-check command]

# Run all checks
[check-all command]
```

### Code Quality Requirements
- ✅ All linter rules must pass
- ✅ Code must be formatted consistently
- ✅ No compiler/interpreter warnings
- ✅ Type safety enforced (if applicable)
- ✅ Comments only where logic is non-obvious
- ✅ Functions/methods have clear, single purposes

---

## INFRASTRUCTURE & DEPLOYMENT

### Environment Setup

**Required Tools:**
- [Tool 1] (version X.X+)
- [Tool 2] (version X.X+)
- [Tool 3]

**Configuration Files:**
- `.env` (environment variables, gitignored)
- `[config-file]` (application configuration)
- `[other config files]`

### Deployment Method
- **Target Platform:** [AWS / GCP / Azure / Docker / Kubernetes / Heroku / Vercel / etc.]
- **Deployment Tool:** [Terraform / CloudFormation / Kubernetes / Docker Compose / etc.]
- **CI/CD:** [GitHub Actions / GitLab CI / CircleCI / Jenkins / etc.]

### Deployment Process

```bash
# Build for production
[build command]

# Deploy to [environment]
[deploy command]

# Verify deployment
[verify command]

# Rollback if needed
[rollback command]
```

---

## ERROR HANDLING & DEBUGGING

### Common Issues

**Issue 1: [Common Problem]**
- **Symptom:** [How to recognize]
- **Fix:** [How to resolve]

**Issue 2: [Common Problem]**
- **Symptom:** [How to recognize]
- **Fix:** [How to resolve]

**Issue 3: [Common Problem]**
- **Symptom:** [How to recognize]
- **Fix:** [How to resolve]

### Debugging Process
1. **Reproduce locally** (use local dev environment)
2. **Check logs** (application logs, server logs)
3. **Verify configuration** (environment variables, config files)
4. **Test incrementally** (one change at a time)
5. **Check dependencies** (versions, installations)

### Logging
- **Log Level:** [DEBUG / INFO / WARN / ERROR]
- **Log Location:** [Where logs are stored]
- **Monitoring:** [Monitoring tool if applicable]

---

## SECURITY & BEST PRACTICES

### Security Requirements
- **Never commit secrets** (use environment variables)
- **Input validation** at all entry points
- **Sanitize user input** to prevent injection attacks
- **Use parameterized queries** for database access
- **Keep dependencies updated** (security patches)
- **Follow OWASP guidelines** (if applicable)

### Code Best Practices
- **KISS:** Keep It Simple, Stupid
- **DRY:** Don't Repeat Yourself (use shared utilities)
- **YAGNI:** You Aren't Gonna Need It (no premature features)
- **Single Responsibility:** One function, one purpose
- **No premature optimization:** Profile first, then optimize

### Specific to This Project
- [Project-specific best practice 1]
- [Project-specific best practice 2]
- [Project-specific best practice 3]

---

## CROSS-PLATFORM COMPATIBILITY

### Supported Platforms
- **Operating Systems:** [Windows / macOS / Linux / etc.]
- **Browsers:** (if web) [Chrome / Firefox / Safari / Edge / etc.]
- **Mobile:** (if applicable) [iOS / Android / etc.]

### Platform Considerations
- **Path handling:** Use [language]'s path utilities (not hardcoded paths)
- **Line endings:** Let git handle (configured in `.gitattributes`)
- **Case sensitivity:** Be aware of filesystem differences
- **Scripts:** Prefer [language] scripts over shell scripts (platform-independent)

---

## DOCUMENTATION REQUIREMENTS

### Code Documentation
- **Docstrings/Comments:** [When and what to document]
- **API Documentation:** [Tool: JSDoc / Sphinx / GoDoc / etc.]
- **Architecture Docs:** [Where architecture is documented]
- **Inline Comments:** Only where logic is non-obvious

### Project Documentation
- **README.md:** Project overview and quick start
- **CLAUDE.md:** AI assistant instructions
- **CLAUDE_CODE_SYSTEM_REQUIREMENTS.md:** This file - technical standards
- **KB_FILE_STRUCTURE.md:** Project structure and organization
- **[Other docs]:** [Additional documentation files]

---

## PERFORMANCE CONSIDERATIONS

### Performance Requirements
- **Response Time:** [Target response time]
- **Throughput:** [Target requests/operations per second]
- **Resource Usage:** [Memory / CPU limits]
- **Scalability:** [How the system should scale]

### Optimization Guidelines
1. **Profile before optimizing** (don't guess bottlenecks)
2. **Measure impact** (benchmark before and after)
3. **Cache strategically** (where it provides value)
4. **Lazy load** (load resources on demand)
5. **Batch operations** (reduce I/O and network calls)

---

## CONTINUOUS IMPROVEMENT

### Regular Maintenance
- **Update dependencies:** [Frequency - weekly / monthly]
- **Security patches:** Apply promptly
- **Code review:** Before merging
- **Refactoring:** When technical debt accumulates
- **Documentation:** Keep updated with code changes

### Monitoring & Metrics
- **Key Metrics:** [What to monitor]
- **Alerts:** [When to be notified]
- **Dashboards:** [Where to view metrics]
- **Logging:** [What to log and where]

---

## SUPPORT & RESOURCES

### Getting Help

**Internal Resources:**
- Team documentation: [Link]
- Team chat: [Channel/Tool]
- Issue tracker: [GitHub / Jira / etc.]

**External Resources:**
- Official [Technology] docs: [Link]
- Community forum: [Link]
- Stack Overflow tag: `[tag]`

### Contributing

See [CONTRIBUTING.md] for:
- How to submit issues
- How to propose changes
- Code review process
- Release process

---

## NOTES FOR AI ASSISTANTS (Claude Code)

When working with this project:

### Critical Rules
1. **ALWAYS use [package manager]** for package management
2. **NEVER use [alternative package managers]**
3. **Follow the test-first approach** when adding functionality
4. **Check [config file]** for project-specific settings
5. **Read KB_FILE_STRUCTURE.md** to understand project organization

### Common Patterns
- [Pattern 1 used in this project]
- [Pattern 2 used in this project]
- [Pattern 3 used in this project]

### Before Suggesting Code
1. Read relevant files to understand existing patterns
2. Check if similar functionality already exists
3. Consider simpler alternatives
4. Ensure the solution is testable
5. Follow existing code style exactly

### Testing Guidance
- **Always write tests** for new functionality
- **Run tests locally** before suggesting "done"
- **Test file location:** [Where test files should be created]
- **Test command:** `[test command]`

---

*Last Updated: [Date]*
*Project: [PROJECT_NAME]*
*Language: [Primary Language]*
*Framework: [Primary Framework]*
