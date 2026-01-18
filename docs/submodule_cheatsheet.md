# Git Submodule Workflow Cheatsheet

Quick reference for working with repro-tools submodule.

---

## TL;DR - Most Common Tasks

```bash
# Update repro-tools to latest version
git submodule update --remote lib/repro-tools
git add lib/repro-tools
git commit -m "Update repro-tools to latest"

# Check if submodule is up to date
git submodule status
cd lib/repro-tools && git status && git log HEAD..origin/main --oneline
```

---

## Creating a New Project from Template

### ✅ DO THIS (Option 1 - Recommended)
```bash
git clone --recursive https://github.com/rhstanton/project_template.git my-project
cd my-project
make environment
```

### ✅ DO THIS (Option 2 - Also Fine)
```bash
git clone https://github.com/rhstanton/project_template.git my-project
cd my-project
make environment  # Auto-initializes submodules
```

### ❌ DON'T DO THIS
```bash
# Wrong - don't manually copy lib/repro-tools/
cp -r project_template/lib/repro-tools my-project/lib/
```

**Why?** Git needs to manage the submodule via its commit hash, not file copies.

---

## Editing repro-tools (Your Development Workflow)

```bash
# 1. Make changes
cd lib/repro-tools
vim src/repro_tools/provenance.py

# 2. Test (changes immediately available - no reinstall!)
cd ../..
make all

# 3. Commit repro-tools changes
cd lib/repro-tools
git status
git add -A
git commit -m "Improve feature X"
git push origin main

# 4. Update project_template to reference new commit
cd ../..
git status  # Shows: modified: lib/repro-tools (new commits)
git add lib/repro-tools
git commit -m "Update repro-tools to latest"
git push
```

---

## Updating to Latest repro-tools

```bash
# Pull latest from main branch
git submodule update --remote lib/repro-tools

# Commit the update
git add lib/repro-tools
git commit -m "Update repro-tools to latest"
```

---

## Checking Submodule Status

```bash
# See current submodule commit
git submodule status

# See if submodule has uncommitted changes
cd lib/repro-tools && git status

# See if submodule has new commits not yet tracked by project_template
git status  # Look for "modified: lib/repro-tools (new commits)"
```

---

## Common Scenarios

### Submodule is empty
```bash
git submodule update --init --recursive
```

### Submodule is on wrong commit
```bash
git submodule update lib/repro-tools
```

### Want to work on a different branch of repro-tools
```bash
cd lib/repro-tools
git checkout feature-branch
git pull
cd ../..
# Test your changes...
# Don't commit lib/repro-tools unless you want to track this branch
```

### Reset submodule to tracked commit
```bash
git submodule update --init lib/repro-tools
```

---

## What's Tracked in Git

| Item | Tracked? | What's Stored |
|------|----------|---------------|
| `.gitmodules` | ✅ Yes | Submodule URL and config |
| `lib/` directory | ✅ Yes | Empty directory marker |
| `lib/repro-tools/` commit hash | ✅ Yes | Specific commit reference |
| `lib/repro-tools/` file contents | ❌ No | Lives in repro-tools repo |

---

## Troubleshooting

### "lib/repro-tools is empty"
```bash
git submodule update --init --recursive
```

### "fatal: not a git repository" in lib/repro-tools
```bash
rm -rf lib/repro-tools
git submodule update --init --recursive
```

### Can't push submodule changes
```bash
cd lib/repro-tools
git remote -v  # Verify you have push access
git push origin main
```

### Project shows "modified: lib/repro-tools" but you didn't change it
This means the submodule has newer commits. Options:
1. Commit the update: `git add lib/repro-tools && git commit -m "Update repro-tools"`
2. Reset to tracked commit: `git submodule update lib/repro-tools`

---

## Key Principles

1. **Never manually copy lib/repro-tools/** - Let git manage it
2. **Always use `--recursive` when cloning** - Or let `make environment` handle it
3. **Editable install means immediate changes** - No reinstall needed
4. **Two separate repos** - project_template tracks a commit hash from repro-tools
5. **Commit both repos** - Push to repro-tools, then update reference in project_template

---

## Quick Test

```bash
# Verify submodule is working
git submodule status
ls -la lib/repro-tools/src/repro_tools/
conda run -p .env pip show repro-tools
```

Should show:
- Submodule at specific commit
- repro-tools source files present
- Editable install location: `.../lib/repro-tools`
