# Claude Code Templates

Generic templates for setting up Claude Code documentation in any project.

## Overview

This directory contains **reusable templates** for creating Claude Code-compatible project documentation. These templates help you set up a consistent structure that Claude Code can automatically load and use.

### What's Included

1. **TEMPLATE_CLAUDE.md** - Main project instructions for Claude Code
2. **TEMPLATE_CLAUDE_CODE_SYSTEM_REQUIREMENTS.md** - Technical requirements and development standards
3. **TEMPLATE_KB_FILE_STRUCTURE.md** - Project structure and architecture documentation

## Why Use These Templates?

### Benefits

- ✅ **Consistent Structure:** All your projects follow the same documentation pattern
- ✅ **Auto-Loading:** Claude Code automatically loads these files in every session
- ✅ **Separation of Concerns:** Requirements, structure, and context in separate files
- ✅ **Easy Maintenance:** Update documentation without touching code
- ✅ **Project-Specific:** Each project's documentation is isolated
- ✅ **Claude-Aware:** Claude Code always understands your project standards

### How Claude Code Uses These Files

When you add these files to a project with the import mechanism:

1. Claude Code reads `CLAUDE.md`
2. Import directives load additional files automatically
3. All content becomes part of Claude's context
4. Claude follows your project's specific standards and patterns

## Quick Start

### For a New Project

1. **Copy the template files to your project root:**
   ```bash
   cp TEMPLATE_CLAUDE.md /path/to/your-project/CLAUDE.md
   cp TEMPLATE_CLAUDE_CODE_SYSTEM_REQUIREMENTS.md /path/to/your-project/CLAUDE_CODE_SYSTEM_REQUIREMENTS.md
   cp TEMPLATE_KB_FILE_STRUCTURE.md /path/to/your-project/KB_FILE_STRUCTURE.md
   ```

2. **Customize each file:**
   - Replace all `[PLACEHOLDER]` markers with project-specific values
   - Remove sections that don't apply to your project
   - Add project-specific sections as needed

3. **Verify the import directives:**
   - Open `/path/to/your-project/CLAUDE.md`
   - Ensure the first two lines are:
     ```markdown
     @./CLAUDE_CODE_SYSTEM_REQUIREMENTS.md
     @./KB_FILE_STRUCTURE.md
     ```

4. **Test in Claude Code:**
   ```bash
   cd /path/to/your-project
   # Open Claude Code in this directory
   # Run: /memory
   # Verify all three files are listed
   ```

### For an Existing Project

If you already have project documentation:

1. **Create the three files** using the templates as a starting point
2. **Migrate existing content** into the appropriate files:
   - Project context and instructions → `CLAUDE.md`
   - Technical requirements and standards → `CLAUDE_CODE_SYSTEM_REQUIREMENTS.md`
   - Project structure and architecture → `KB_FILE_STRUCTURE.md`
3. **Add import directives** to the top of `CLAUDE.md`
4. **Test and iterate** until Claude Code understands your project correctly

## Template Files Explained

### TEMPLATE_CLAUDE.md

**Purpose:** Main project instructions and context for Claude Code.

**Key Sections:**
- Project overview and description
- Directory structure summary
- Getting started guide
- Development workflow
- Common issues and troubleshooting
- Testing strategy
- Deployment process
- Notes for AI assistants

**Customize:**
- Replace `[PROJECT_NAME]` with your project name
- Fill in all `[PLACEHOLDER]` markers
- Add project-specific sections
- Remove sections that don't apply
- Keep language clear and concise

**Tips:**
- This is the entry point - Claude reads this first
- Use import directives at the top to load other files
- Focus on project context, not technical details (those go in SYSTEM_REQUIREMENTS)
- Include troubleshooting for common issues

### TEMPLATE_CLAUDE_CODE_SYSTEM_REQUIREMENTS.md

**Purpose:** Technical requirements, development standards, and best practices.

**Key Sections:**
- Programming requirements (language, package manager)
- Testing requirements (structure, commands, coverage)
- Development workflow (standard cycle)
- Code quality standards (linting, formatting)
- Infrastructure and deployment
- Error handling and debugging
- Security and best practices
- Cross-platform compatibility
- Documentation requirements
- Performance considerations

**Customize:**
- Specify your package manager and exact commands
- Define your testing strategy
- Document your deployment process
- Add project-specific requirements
- Remove generic sections that don't apply

**Tips:**
- This file defines "how Claude should work on this project"
- Be specific: exact commands, exact tools, exact versions
- Include what NOT to do (e.g., "NEVER use pip, ALWAYS use uv")
- Add common error patterns and fixes

### TEMPLATE_KB_FILE_STRUCTURE.md

**Purpose:** Project structure, architecture, and technology stack documentation.

**Key Sections:**
- File structure diagram (Mermaid)
- Directory purpose overview
- Key files to configure
- Standard file patterns
- Data flow architecture
- Technology stack
- Testing infrastructure
- Build and deployment structure
- Import mechanism explanation

**Customize:**
- Create accurate Mermaid diagram of your structure
- Document each directory's purpose
- List all important configuration files
- Add technology stack details
- Include architecture diagrams

**Tips:**
- Use Mermaid diagrams for visual representation
- Color-code different types of components
- Keep directory descriptions concise
- Update when structure changes

## Customization Guide

### Step-by-Step Customization

1. **Start with CLAUDE.md:**
   - Replace `[PROJECT_NAME]` everywhere
   - Fill in project overview
   - Document directory structure
   - Add getting started steps
   - Include common issues

2. **Move to CLAUDE_CODE_SYSTEM_REQUIREMENTS.md:**
   - Specify language and version
   - Define package manager commands
   - Document test structure and commands
   - Add deployment process
   - Include security requirements

3. **Finish with KB_FILE_STRUCTURE.md:**
   - Create Mermaid diagram of file structure
   - Document each directory
   - List configuration files
   - Add technology stack
   - Include architecture diagrams

4. **Test the setup:**
   - Open Claude Code in project
   - Run `/memory` command
   - Verify all files loaded
   - Test that Claude follows your standards

### Common Customizations by Project Type

#### Python Project (pip/poetry/uv)
- Package manager: `pip install`, `poetry add`, `uv add`
- Test command: `pytest`, `python -m pytest`
- Linter: `flake8`, `pylint`, `ruff`
- Formatter: `black`, `autopep8`

#### JavaScript/TypeScript Project (npm/yarn/pnpm)
- Package manager: `npm install`, `yarn add`, `pnpm add`
- Test command: `npm test`, `jest`, `vitest`
- Linter: `eslint`
- Formatter: `prettier`

#### Go Project
- Package manager: `go get`, `go mod`
- Test command: `go test`
- Linter: `golangci-lint`
- Formatter: `gofmt`

#### Rust Project
- Package manager: `cargo add`
- Test command: `cargo test`
- Linter: `clippy`
- Formatter: `rustfmt`

## Import Mechanism

### How It Works

Claude Code automatically discovers and loads files using import directives:

```markdown
@./CLAUDE_CODE_SYSTEM_REQUIREMENTS.md
@./KB_FILE_STRUCTURE.md

# [Your CLAUDE.md content follows]
```

### Import Rules

- **Syntax:** `@./relative/path/to/file.md`
- **Placement:** At the very top of CLAUDE.md (before any other content)
- **Max Depth:** 5 hops (recursive imports supported)
- **Relative Paths:** Always use `./` for same-directory files
- **File Types:** Only `.md` (Markdown) files can be imported
- **Order Matters:** Files are loaded in the order they appear

### Verification

To verify imports are working:

1. Open Claude Code in your project directory
2. Run the command: `/memory`
3. You should see all imported files listed
4. If files are missing, check your import syntax

## Examples

### Example 1: Python API Project

```markdown
# CLAUDE.md
@./CLAUDE_CODE_SYSTEM_REQUIREMENTS.md
@./KB_FILE_STRUCTURE.md

# MyAPI - AI Assistant Guide

## Project Overview
MyAPI is a RESTful API built with FastAPI for [purpose].

## Key Commands
- Start dev server: `uvicorn main:app --reload`
- Run tests: `pytest`
- Format code: `black .`
```

```markdown
# CLAUDE_CODE_SYSTEM_REQUIREMENTS.md
**Primary Language:** Python 3.11
**Package Manager:** pip (with requirements.txt)

ALWAYS use:
- `pip install` to add dependencies
- `python -m pytest` to run tests
- `black .` to format code

NEVER use:
- conda
- pipenv
```

### Example 2: React Frontend Project

```markdown
# CLAUDE.md
@./CLAUDE_CODE_SYSTEM_REQUIREMENTS.md
@./KB_FILE_STRUCTURE.md

# MyApp - AI Assistant Guide

## Project Overview
MyApp is a React application for [purpose].

## Key Commands
- Start dev: `npm run dev`
- Build: `npm run build`
- Test: `npm test`
```

```markdown
# CLAUDE_CODE_SYSTEM_REQUIREMENTS.md
**Primary Language:** TypeScript 5.0
**Package Manager:** npm

ALWAYS use:
- `npm install` to add dependencies
- `npm run dev` to start dev server
- `npm test` to run tests

NEVER use:
- yarn
- pnpm
```

## Best Practices

### Do's ✅

- **Be Specific:** Use exact commands, not general descriptions
- **Include Examples:** Show concrete examples of patterns
- **Update Regularly:** Keep documentation current with code
- **Test Changes:** Verify Claude Code loads files correctly
- **Use Placeholders:** Make templates easy to customize (`[PLACEHOLDER]`)
- **Separate Concerns:** Keep context, requirements, and structure separate
- **Document Exceptions:** Note project-specific quirks or workarounds

### Don'ts ❌

- **Don't Be Vague:** Avoid "use a package manager" - specify which one
- **Don't Over-Document:** Keep it concise and scannable
- **Don't Duplicate:** If it's in one file, don't repeat in another
- **Don't Forget Imports:** Always add import directives to CLAUDE.md
- **Don't Hardcode:** Use relative paths, not absolute paths
- **Don't Commit Secrets:** Keep `.env` and credentials out of docs
- **Don't Mix Concerns:** Keep technical details in SYSTEM_REQUIREMENTS, not CLAUDE.md

## Troubleshooting

### Problem: Claude Code doesn't follow my standards

**Solution:**
1. Run `/memory` to check if files are loaded
2. Verify import directives in CLAUDE.md
3. Check for typos in file paths
4. Ensure files are in the correct location
5. Try starting a new Claude Code session

### Problem: Import directives don't work

**Solution:**
1. Check syntax: must be `@./filename.md` (with `./`)
2. Ensure imports are at the TOP of CLAUDE.md
3. Verify file exists at the specified path
4. Check file has `.md` extension
5. Try absolute path if relative doesn't work: `@/full/path/to/file.md`

### Problem: Documentation is too long

**Solution:**
1. Move details to separate files (architecture.md, api-docs.md)
2. Import only the essentials
3. Use links to external docs for deep dives
4. Keep CLAUDE.md focused on essentials
5. Split large requirements into multiple files

### Problem: Claude Code seems confused

**Solution:**
1. Check for conflicting information across files
2. Ensure placeholders are all replaced
3. Remove contradictory statements
4. Be more specific (avoid vague language)
5. Add concrete examples

## Updating Templates

These templates should evolve with best practices:

1. **For Alex Project:** The Alex-specific files are NOT templates - they stay Alex-specific
2. **For Templates:** These are generic and should remain generic
3. **Improvements:** If you find better patterns, update these templates
4. **Versioning:** Consider dating updates to track template evolution

## Getting Help

### Resources

- **Claude Code Documentation:** [Check official docs]
- **Alex Project Example:** See `/alex/CLAUDE.md` for a working example
- **Template Issues:** Report issues with templates in the project repo

### Questions?

Common questions:

**Q: Can I use different file names?**
A: CLAUDE.md must be named exactly that. Other files can have different names if you update import directives.

**Q: How many files can I import?**
A: No hard limit, but keep it reasonable. 2-5 files is typical.

**Q: Can I import from subdirectories?**
A: Yes, use relative paths like `@./docs/architecture.md`

**Q: Do imports work recursively?**
A: Yes, imported files can import other files (max depth: 5)

**Q: Is there a size limit?**
A: Be mindful of context window. Keep files focused and concise.

## Contributing

Improvements to these templates are welcome:

1. Test your changes with real projects
2. Keep templates generic (no project-specific content)
3. Add examples to demonstrate patterns
4. Update this README with new features
5. Submit improvements via pull request

---

*Last Updated: November 2025*
*Template Version: 1.0*
*Part of: KB_github_UTILITIES*
