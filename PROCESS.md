# Development Process

This document outlines the strict modular development workflow for WorldInsights.

## Core Principle

**"Modular, Tested, Committed."**
Every feature or change must be broken down into small, manageable modules. No code is committed without a passing test.

## Workflow Status

1. **Define Task**: Identify the micro-task (e.g., "Create API endpoint for Population data").
2. **Create Test**: Create a test file in `tests/` specifically for this module.
3. **Implement**: Write the code to fulfill the requirement.
4. **Verify**: Run the specific test.
   - Command: `python -m pytest tests/test_filename.py`
5. **Commit**: Only after the test passes, commit the changes to branch `bjach`.

## Git Workflow

- Remote: `origin` (https://github.com/bonzainsights/worldinsights.git)
- Branch: `bjach`

```bash
# After passing tests
git add .
git commit -m "feat: [module_name] implemented and verified"
git push origin bjach
```

## Testing Structure

- `tests/` directory mirrors the `app/` structure where possible.
- Use `pytest` for running tests.
