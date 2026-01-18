# repro-tools Git Submodule

This project uses [repro-tools](https://github.com/rhstanton/repro-tools) as a **git submodule** installed in **editable mode**. This setup provides the best of both worlds:

- ✅ Always uses the latest development version
- ✅ Changes to repro-tools are immediately available
- ✅ Portable - works for all users cloning this template
- ✅ No hardcoded absolute paths

---

## What is a Git Submodule?

A git submodule allows you to include another git repository inside your project at a specific path. The submodule tracks a specific commit of the external repository.

**In this project:**
- `lib/repro-tools/` contains the repro-tools repository
- It's tracked in `.gitmodules` and installed in editable mode via pip

---

## For Template Users (First Time Setup)

When you clone this template to create a new project, git submodules are **automatically initialized** by the Makefile:

```bash
# Option 1: Clone with submodules (faster, recommended)
git clone --recursive https://github.com/rhstanton/project_template.git my-project
cd my-project
make environment

# Option 2: Clone normally, auto-initialize on first make
git clone https://github.com/rhstanton/project_template.git my-project
cd my-project
make environment  # Auto-runs: git submodule update --init --recursive
```

**IMPORTANT:** Do NOT manually copy the `lib/repro-tools/` directory when creating a new project. Let git handle it via submodules.

The `make environment` target automatically runs:
```bash
git submodule update --init --recursive
```

This downloads repro-tools to `lib/repro-tools/` and installs it in editable mode.

---

## For Template Developers (Working on repro-tools)

### Making Changes to repro-tools

Since repro-tools is installed in editable mode (`pip install -e`), changes are immediately available:

```bash
# 1. Edit repro-tools code
cd lib/repro-tools
vim src/repro_tools/provenance.py
# Make your changes...

# 2. Test immediately (no reinstall needed!)
cd ../..
make all  # Uses your local edits automatically

# 3. Commit and push repro-tools changes
cd lib/repro-tools
git add -A
git commit -m "Improve provenance tracking"
git push origin main

# 4. Update project_template to use the new commit
cd ../..
git add lib/repro-tools
git commit -m "Update repro-tools submodule"
git push
```

### Updating to Latest repro-tools

To pull the latest changes from repro-tools:

```bash
# Option 1: Using Makefile (recommended - provides helpful output)
make update-submodules

# Option 2: Direct git command
git submodule update --remote lib/repro-tools

# Or manually pull in the submodule directory
cd lib/repro-tools
git pull origin main
cd ../..

# Commit the updated submodule reference
git add lib/repro-tools
git commit -m "Update repro-tools to latest"
```

### Checking Submodule Status

```bash
# See which commit the submodule is at
git submodule status

# See if submodule has uncommitted changes
cd lib/repro-tools
git status
```

---

## How It Works Technically

### 1. Submodule Configuration (`.gitmodules`)

```ini
[submodule "lib/repro-tools"]
    path = lib/repro-tools
    url = https://github.com/rhstanton/repro-tools.git
    branch = main
```

This tells git:
- Clone repro-tools to `lib/repro-tools/`
- Track the `main` branch
- Update to latest when running `git submodule update --remote`

### 2. Editable Install (`env/python.yml`)

```yaml
dependencies:
  - pip:
    - juliacall>=0.9.14
    - -e ../lib/repro-tools  # Editable install
```

The `-e` flag installs repro-tools in "editable" or "development" mode:
- Python imports `repro_tools` directly from `lib/repro-tools/src/`
- Changes to source files are immediately available
- No need to reinstall after editing

### 3. Automatic Initialization (`Makefile`)

```makefile
# At top of Makefile - runs once per make invocation
$(shell git submodule update --init --recursive 2>/dev/null || true)

# Also explicitly in environment target
environment:
    git submodule update --init --recursive
    make -C env all-env
```

This ensures submodules are always initialized before building.

---

## Troubleshooting

### "lib/repro-tools is empty"

**Cause:** Submodule not initialized

**Fix:**
```bash
git submodule update --init --recursive
```

### "ModuleNotFoundError: No module named 'repro_tools'"

**Cause:** Python environment not installed or repro-tools not in editable mode

**Fix:**
```bash
make environment  # Reinstall environment
# OR
conda run -p .env pip install -e lib/repro-tools
```

### "fatal: not a git repository" in lib/repro-tools

**Cause:** Submodule directory exists but isn't properly initialized

**Fix:**
```bash
rm -rf lib/repro-tools
git submodule update --init --recursive
```

### Submodule is detached HEAD

**Cause:** Submodules default to detached HEAD state (pointing to specific commit)

**Fix:** Switch to tracking branch
```bash
cd lib/repro-tools
git checkout main
git pull
cd ../..
git add lib/repro-tools
git commit -m "Update repro-tools submodule to latest main"
```

### "Changes not staged for commit: lib/repro-tools (new commits)"

**Meaning:** The submodule has newer commits than what project_template is tracking

**Options:**
1. Commit the update to use newer version:
   ```bash
   git add lib/repro-tools
   git commit -m "Update repro-tools to latest"
   ```

2. Reset submodule to tracked commit:
   ```bash
   git submodule update lib/repro-tools
   ```

---

## Comparison with Other Approaches

### Git Submodule (Current)
✅ Portable - works for all users  
✅ Editable - changes immediately available  
✅ Versioned - tracks specific commit  
✅ No absolute paths  
⚠️ Requires submodule commands  

### Absolute Path (-e /path/to/repro-tools)
✅ Editable - changes immediately available  
❌ Not portable - breaks on other machines  
❌ User-specific paths  

### GitHub Direct (git+https://github.com/...)
✅ Portable - works for all users  
❌ Not editable - requires reinstall  
❌ Doesn't use local development version  

### PyPI Package (pip install repro-tools)
✅ Portable - works for all users  
✅ Simple - standard pip install  
❌ Not editable - requires reinstall  
❌ Only works for released versions  
❌ Doesn't support active development  

---

## For Journal Submission

When creating a replication package for journal submission, the submodule is included automatically:

```bash
make journal-package
```

This creates `journal-package/` with:
- All analysis code
- `lib/repro-tools/` submodule (full source code)
- `.gitmodules` configuration
- Environment specifications

Reviewers can replicate your work with:
```bash
git clone journal-package.tar.gz
cd journal-package
make environment  # Auto-initializes submodule
make all
```

---

## Reference Commands

```bash
# Clone project with submodules
git clone --recursive https://github.com/rhstanton/project_template.git

# Initialize submodules in existing clone
git submodule update --init --recursive

# Update submodule to latest remote commit
git submodule update --remote lib/repro-tools

# Check submodule status
git submodule status

# See uncommitted changes in submodule
cd lib/repro-tools && git status

# Update all submodules to their tracked branches
git submodule foreach git pull origin main

# Remove submodule (if needed)
git submodule deinit -f lib/repro-tools
git rm -f lib/repro-tools
rm -rf .git/modules/lib/repro-tools
```

---

## See Also

- [repro-tools GitHub repository](https://github.com/rhstanton/repro-tools)
- [submodule_cheatsheet.md](submodule_cheatsheet.md) - Quick reference commands
- [Git Submodules Documentation](https://git-scm.com/book/en/v2/Git-Tools-Submodules)
- [Python Editable Installs](https://pip.pypa.io/en/stable/cli/pip_install/#editable-installs)
- [environment.md](environment.md) - Environment setup details
