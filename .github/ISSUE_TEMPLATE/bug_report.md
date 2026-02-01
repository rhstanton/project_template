---
name: Bug report
about: Create a report to help us improve
title: '[BUG] '
labels: bug
assignees: ''
---

## Bug Description

**Clear and concise description of what the bug is.**

## To Reproduce

Steps to reproduce the behavior:
1. Run command '...'
2. See error '...'

## Expected Behavior

**What you expected to happen.**

## Actual Behavior

**What actually happened.**

## Environment

**Please complete the following information:**

- OS: [e.g., Ubuntu 22.04, macOS 13, Windows 11 + WSL]
- GNU Make version: [output of `make --version`]
- Python version: [output of `.env/bin/python --version`]
- Julia version (if relevant): [output of `env/scripts/runjulia --version`]
- Installation method: [conda/micromamba/other]

**Environment setup:**
- [ ] Ran `make environment` successfully
- [ ] Tests pass with `make test`
- [ ] Running from clean clone or existing project?

## Error Messages / Logs

<details>
<summary>Error output (click to expand)</summary>

```
Paste error messages or relevant log output here
```

</details>

## Minimal Reproducible Example

**If possible, provide a minimal code example that reproduces the issue:**

```python
# Minimal code that triggers the bug
```

Or:
```bash
# Minimal shell commands that trigger the bug
make price_base  # Example
```

## Additional Context

**Add any other context about the problem here:**

- Does it happen consistently or intermittently?
- Did this work in a previous version?
- Have you made any customizations to the template?
- Any relevant provenance files or build logs?

## Possible Solution

**If you have suggestions on how to fix this, please share:**

## Checklist

Before submitting, please check:

- [ ] I've searched existing issues to avoid duplicates
- [ ] I've included all relevant environment information
- [ ] I've provided clear steps to reproduce
- [ ] I've included error messages or logs
- [ ] I've tested with a clean environment (`make cleanall && make environment`)
