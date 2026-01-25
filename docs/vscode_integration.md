# VS Code Integration Guide

This document explains how to work entirely within VS Code while leveraging the project's Make-based workflow.

## Overview

The project is orchestrated via **GNU Make**, but all functionality is accessible through VS Code's UI:

- **Tasks** for running builds, tests, and publishing
- **Launch configurations** for debugging Python scripts
- **Settings** for Python/Julia environment integration
- **Extensions** for enhanced development experience

---

## Quick Start

### 1. Install Recommended Extensions

When you open this workspace, VS Code will prompt you to install recommended extensions. Click **Install All** or install individually:

**Python Development:**
- Python (Microsoft)
- Black Formatter
- Ruff (linter)
- Mypy Type Checker

**Notebooks:**
- Jupyter (Microsoft)

**Git:**
- GitHub Pull Requests
- GitLens

**Utilities:**
- Makefile Tools
- Markdown All in One
- Todo Tree

### 2. Select Python Interpreter

1. Press **Ctrl+Shift+P** (Cmd+Shift+P on macOS)
2. Type: `Python: Select Interpreter`
3. Choose: `.env/bin/python` (project-local conda environment)

This should be auto-selected thanks to `.vscode/settings.json`.

### 3. Build Your First Artifact

**Via Command Palette:**
1. Press **Ctrl+Shift+P**
2. Type: `Tasks: Run Task`
3. Select: `Build all artifacts`

**Via Keyboard Shortcut:**
- Press **Ctrl+Shift+B** (default build task)

---

## Working with Tasks

Tasks provide access to all Makefile targets via VS Code's UI.

### Running Tasks

**Method 1: Command Palette**
1. **Ctrl+Shift+P** → `Tasks: Run Task`
2. Select from list

**Method 2: Keyboard Shortcut**
- **Ctrl+Shift+B**: Run default build task (`make all`)
- **Ctrl+Shift+T**: Run default test task (`make test`)

**Method 3: Terminal Menu**
- Menu: **Terminal** → **Run Task...**

### Available Tasks

#### Build Tasks
- **Build all artifacts** (default) - `make all`
- **Build price_base** - `make price_base`
- **Build remodel_base** - `make remodel_base`

#### Environment Tasks
- **Setup environment** - `make environment` (one-time setup)
- **Verify environment** - `make verify` (quick health check)

#### Testing Tasks
- **Run tests** (default test) - `make test`
- **Run tests with coverage** - `make test-cov`
- **Test outputs** - `make test-outputs` (verify expected files exist)
- **Compare outputs (diff)** - `make diff-outputs`

#### Publishing Tasks
- **Publish artifacts** - `make publish`

#### Quality Assurance Tasks
- **Pre-submission check** - `make pre-submit`
- **Generate replication report** - `make replication-report`
- **Log system info** - `make system-info`

#### Utility Tasks
- **Run examples** - `make examples`
- **Clean outputs** - `make clean`
- **Run Python script with environment** - Uses current file
- **Run Julia script with environment** - Uses current file

### Task Output

Task output appears in the **Terminal** panel (bottom of VS Code). You can:
- Click links to jump to errors
- Scroll through output
- Search output with **Ctrl+F**

---

## Debugging Python Scripts

Debug Python scripts with full environment configuration (Julia bridge, etc.).

### Debug Current File

1. Open any Python file (e.g., `build_price_base.py`)
2. Set breakpoints by clicking left of line numbers
3. Press **F5** or select **Run** → **Start Debugging**
4. Choose: `Python: Current File`

The debugger respects all environment variables (PYTHONPATH, Julia config, etc.).

### Debug Specific Analysis Scripts

Pre-configured debug configurations with correct arguments:

**Method 1: Debug Panel**
1. Click Debug icon in left sidebar (or **Ctrl+Shift+D**)
2. Select configuration from dropdown:
   - `Python: Debug build_price_base`
   - `Python: Debug build_remodel_base`
3. Press **F5** to start

**Method 2: Command Palette**
1. **Ctrl+Shift+P** → `Debug: Select and Start Debugging`
2. Choose configuration

### Debug Tests

**Run all tests with debugger:**
1. Select: `Python: Run Tests`
2. Press **F5**

**Run single test:**
1. Open test file (e.g., `tests/test_provenance.py`)
2. Click **Debug Test** above test function

### Debugging Tips

**Breakpoints:**
- Click left margin to set breakpoint
- Right-click → **Conditional Breakpoint** for advanced conditions
- **Logpoints** to print without stopping

**Debug Console:**
- Evaluate expressions while paused
- Import modules and explore state
- Type `dir()` to see available variables

**Call Stack:**
- See function call hierarchy
- Click frames to inspect variables at each level

---

## Running Scripts Without Debugging

### Via Tasks

Use the generic script runners:

1. Open Python or Julia file
2. **Ctrl+Shift+P** → `Tasks: Run Task`
3. Choose:
   - `Run Python script with environment` (uses `env/scripts/runpython`)
   - `Run Julia script with environment` (uses `env/scripts/runjulia`)

### Via Integrated Terminal

**Python:**
```bash
env/scripts/runpython your_script.py
```

**Julia:**
```bash
env/scripts/runjulia your_script.jl
```

**Or activate conda:**
```bash
conda activate .env
python your_script.py
```

---

## Testing Integration

### Run Tests via UI

**Method 1: Test Explorer**
1. Click Testing icon in left sidebar (beaker icon)
2. Click **Run All Tests** or run individual tests
3. View results in Test Explorer panel

**Method 2: CodeLens**
- Above each test function: `Run Test | Debug Test`
- Click to run/debug individual test

**Method 3: Tasks**
- **Ctrl+Shift+P** → `Tasks: Run Task` → `Run tests`

### Test Configuration

Tests are discovered automatically from `tests/` directory. Configuration in `.vscode/settings.json`:

```json
"python.testing.pytestEnabled": true,
"python.testing.pytestArgs": [
    "tests",
    "-v",
    "--tb=short"
]
```

### Coverage Reports

Run tests with coverage:
1. **Ctrl+Shift+P** → `Tasks: Run Task` → `Run tests with coverage`
2. Open `htmlcov/index.html` in browser to see coverage report

---

## Git Integration

### Built-in Git Features

**Source Control Panel** (Ctrl+Shift+G):
- See changed files
- Stage/unstage changes
- Commit with messages
- Push/pull
- View history

**GitLens Extension** (if installed):
- Line-by-line blame annotations
- Commit history for file
- File history explorer
- Repository insights

### Publishing Workflow

The project uses git safety checks when publishing. In VS Code:

1. **Make changes and build:**
   - Edit analysis scripts
   - **Ctrl+Shift+B** to rebuild

2. **Commit changes:**
   - **Ctrl+Shift+G** to open Source Control
   - Stage files, write commit message
   - Click checkmark to commit

3. **Publish artifacts:**
   - **Ctrl+Shift+P** → `Tasks: Run Task` → `Publish artifacts`
   - This runs `make publish` with git safety checks

If publishing fails due to dirty tree or outdated branch, fix via Source Control panel.

---

## Working with Notebooks

### Jupyter Integration

**Create Notebook:**
1. **Ctrl+Shift+P** → `Create: New Jupyter Notebook`
2. Select Python interpreter: `.env/bin/python`

**Run Cells:**
- Click **Run Cell** icon
- **Shift+Enter** to run and advance
- **Ctrl+Enter** to run and stay

**Import from Scripts:**
```python
# In notebook cell
from build_price_base import main
main()  # Or call specific functions
```

### Using juliacall in Notebooks

Julia integration works in notebooks:

```python
from juliacall import Main as jl

jl.seval("using DataFrames")
df = jl.DataFrame(x=[1,2,3], y=[4,5,6])
print(df)
```

---

## Environment Settings

### Python Configuration

`.vscode/settings.json` configures:

**Interpreter:**
- Uses project-local `.env/bin/python`
- No conda activation needed (already configured)

**Formatting:**
- Black formatter on save
- Import organization on save
- Settings read from `pyproject.toml`

**Linting:**
- Ruff linter enabled
- Mypy type checking enabled
- Configuration from `pyproject.toml`

**PYTHONPATH:**
- Automatically includes workspace root
- Allows `from scripts import ...` imports

### Julia Configuration

Julia extension is **intentionally disabled** for this workspace because:
- Julia is used as backend via juliacall
- Environment managed by wrappers (`env/scripts/runjulia`)
- Prevents conflicts with Python-based workflow

To run pure Julia scripts:
- Use task: `Run Julia script with environment`
- Or terminal: `env/scripts/runjulia script.jl`

### Environment Variables

All environment variables (JULIA_*, PYTHONPATH, etc.) are configured in:
- **Launch configurations** (`launch.json`) for debugging
- **Environment wrappers** (`env/scripts/runpython`) for CLI
- **Settings** (`settings.json`) for terminal

You don't need to set them manually!

---

## File Watching and Performance

### Excluded from Watcher

To improve performance, VS Code ignores changes in:
- `.env/`, `.julia/`, `.stata/` (environments)
- `output/`, `paper/` (build outputs)
- `__pycache__/`, `.pytest_cache/` (caches)

This prevents VS Code from indexing large binary files and temporary outputs.

### If Environment Changes

After updating environment (e.g., `make environment`):
1. **Reload VS Code**: **Ctrl+Shift+P** → `Developer: Reload Window`
2. Verify Python interpreter: Should still be `.env/bin/python`

---

## Keyboard Shortcuts Cheat Sheet

### Building
- **Ctrl+Shift+B** - Build all artifacts (default)
- **Ctrl+Shift+P** → `Tasks: Run Build Task`

### Debugging
- **F5** - Start debugging
- **F9** - Toggle breakpoint
- **F10** - Step over
- **F11** - Step into
- **Shift+F11** - Step out
- **Ctrl+Shift+F5** - Restart debugging

### Testing
- **Ctrl+Shift+T** - Run test task (if configured)
- Click **Run Test** above test function

### Git
- **Ctrl+Shift+G** - Open Source Control panel
- **Ctrl+Shift+P** → `Git: Commit`
- **Ctrl+Shift+P** → `Git: Push`

### Command Palette
- **Ctrl+Shift+P** - Open Command Palette (access all commands)

### Navigation
- **Ctrl+P** - Quick file open
- **Ctrl+Shift+F** - Search across files
- **F12** - Go to definition
- **Alt+F12** - Peek definition

---

## Common Workflows

### Workflow 1: Build and Test Changes

1. Edit `build_price_base.py`
2. **Ctrl+Shift+B** (build all)
3. Review output in Terminal panel
4. **Ctrl+Shift+P** → `Tasks: Run Task` → `Test outputs`
5. If errors, press **F5** to debug

### Workflow 2: Run Tests

1. **Ctrl+Shift+P** → `Tasks: Run Task` → `Run tests`
2. Or click Testing icon → **Run All Tests**
3. View results in Test Explorer
4. Click **Debug Test** for failing tests

### Workflow 3: Publish Workflow

1. **Ctrl+Shift+B** (rebuild everything)
2. **Ctrl+Shift+G** (open Source Control)
3. Stage all changes, commit
4. **Ctrl+Shift+P** → `Tasks: Run Task` → `Publish artifacts`
5. Verify `paper/` directory updated

### Workflow 4: Pre-Submission Check

1. **Ctrl+Shift+P** → `Tasks: Run Task` → `Pre-submission check`
2. Review output for issues
3. Fix any problems
4. **Ctrl+Shift+P** → `Tasks: Run Task` → `Generate replication report`
5. Open `output/replication_report.html` in browser

### Workflow 5: Quick Script Testing

1. Open Python file (e.g., `env/examples/sample_python.py`)
2. **Ctrl+Shift+P** → `Tasks: Run Task` → `Run Python script with environment`
3. Or press **F5** to debug

---

## Troubleshooting

### "Python interpreter not found"

**Fix:**
1. **Ctrl+Shift+P** → `Python: Select Interpreter`
2. Choose `.env/bin/python`
3. If not available, run: **Ctrl+Shift+P** → `Tasks: Run Task` → `Setup environment`

### "Import errors" when running scripts

**Ensure PYTHONPATH is set:**
- Check `.vscode/settings.json` has `PYTHONPATH` in terminal env
- Or run via task: `Run Python script with environment`

### Tasks don't appear

**Reload task list:**
1. **Ctrl+Shift+P** → `Tasks: Run Task`
2. If empty, check `.vscode/tasks.json` exists
3. **Ctrl+Shift+P** → `Developer: Reload Window`

### Julia errors in debugging

**Check environment variables in launch.json:**
- `JULIA_CONDAPKG_BACKEND` should be `Null`
- `JULIA_PROJECT` should point to `env/`
- Launch configs already configured correctly

### Tests not discovered

**Check test configuration:**
1. **Ctrl+Shift+P** → `Python: Configure Tests`
2. Select **pytest**
3. Select `tests` directory

### Linter/formatter not working

**Verify extensions installed:**
1. **Ctrl+Shift+X** (Extensions panel)
2. Search: "Black", "Ruff", "Mypy"
3. Install if missing

**Check settings:**
- Open `.vscode/settings.json`
- Verify `black-formatter.importStrategy: "fromEnvironment"`
- Verify `ruff.enable: true`

---

## Advanced: Customization

### Adding New Tasks

Edit `.vscode/tasks.json`:

```json
{
    "label": "My custom task",
    "type": "shell",
    "command": "make",
    "args": ["my-target"],
    "options": {
        "cwd": "${workspaceFolder}"
    },
    "problemMatcher": []
}
```

### Adding New Debug Configurations

Edit `.vscode/launch.json`:

```json
{
    "name": "Debug my analysis",
    "type": "debugpy",
    "request": "launch",
    "program": "${workspaceFolder}/build_my_analysis.py",
    "args": ["--data", "data/my_data.csv", ...],
    "console": "integratedTerminal",
    "env": {
        "PYTHONPATH": "${workspaceFolder}",
        "JULIA_CONDAPKG_BACKEND": "Null",
        ...
    }
}
```

### Custom Keyboard Shortcuts

**File** → **Preferences** → **Keyboard Shortcuts** (or **Ctrl+K Ctrl+S**)

Bind tasks to keys:
```json
{
    "key": "ctrl+alt+b",
    "command": "workbench.action.tasks.runTask",
    "args": "Build all artifacts"
}
```

---

## Integration with Make

VS Code tasks are **wrappers around Make targets**. When you run a task:

1. VS Code spawns shell process
2. Runs `make <target>` in workspace folder
3. Displays output in Terminal panel

**You can still use Make directly:**
- Open integrated terminal (**Ctrl+\`**)
- Run `make all`, `make publish`, etc.
- Same result as tasks, just different interface

**Benefits of VS Code integration:**
- UI-based task selection
- Keyboard shortcuts
- Integration with debugging
- Problem matcher for errors
- Output panel with clickable links

---

## Resources

### Documentation
- [README.md](../README.md) - Project overview
- [QUICKSTART.md](../QUICKSTART.md) - Getting started
- [docs/](../docs/) - Comprehensive documentation

### VS Code Documentation
- [Tasks](https://code.visualstudio.com/docs/editor/tasks)
- [Debugging](https://code.visualstudio.com/docs/editor/debugging)
- [Python in VS Code](https://code.visualstudio.com/docs/languages/python)

### Extensions
- [Python Extension](https://marketplace.visualstudio.com/items?itemName=ms-python.python)
- [Jupyter](https://marketplace.visualstudio.com/items?itemName=ms-toolsai.jupyter)
- [GitLens](https://marketplace.visualstudio.com/items?itemName=eamodio.gitlens)

---

## Summary

**Everything Make does is accessible in VS Code:**

| Make Command | VS Code Action |
|--------------|----------------|
| `make all` | **Ctrl+Shift+B** (default build) |
| `make test` | Testing panel → **Run All Tests** |
| `make publish` | Tasks → `Publish artifacts` |
| `make environment` | Tasks → `Setup environment` |
| `make verify` | Tasks → `Verify environment` |
| `env/scripts/runpython script.py` | **F5** (debug) or Tasks → `Run Python script` |

**You can work entirely in VS Code** without touching the command line, while still benefiting from Make's robust build orchestration.

---

**Version**: 1.0.0  
**Last Updated**: January 18, 2026
