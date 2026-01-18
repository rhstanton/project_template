# VS Code Quick Reference Card

One-page cheat sheet for working with this project in VS Code.

---

## 🎯 Essential Keyboard Shortcuts

| Action | Shortcut |
|--------|----------|
| **Build all artifacts** | `Ctrl+Shift+B` |
| **Run task** | `Ctrl+Shift+P` → "Tasks: Run Task" |
| **Start debugging** | `F5` |
| **Toggle breakpoint** | `F9` |
| **Open command palette** | `Ctrl+Shift+P` |
| **Quick file open** | `Ctrl+P` |
| **Source control** | `Ctrl+Shift+G` |
| **Testing panel** | Click beaker icon in sidebar |
| **Terminal** | ``Ctrl+` `` |

---

## 🔨 Common Tasks

**Access via:** `Ctrl+Shift+P` → "Tasks: Run Task"

### Build & Test
- `Build all artifacts` - Build everything
- `Build price_base` - Build single artifact
- `Run tests` - Run pytest suite
- `Test outputs` - Verify expected files exist

### Publishing
- `Publish artifacts` - Copy to paper/ with provenance
- `Compare outputs (diff)` - See what changed

### Quality Assurance
- `Pre-submission check` - Validate before journal submission
- `Generate replication report` - Create reviewer documentation
- `Verify environment` - Quick health check

### Environment
- `Setup environment` - One-time installation
- `Run examples` - Test Python/Julia/Stata

---

## 🐛 Debugging Workflows

### Debug Current File
1. Open Python file
2. Set breakpoints (click left margin)
3. Press `F5`
4. Choose "Python: Current File"

### Debug Analysis Script
1. `Ctrl+Shift+D` (Debug panel)
2. Select `Python: Debug build_price_base`
3. Press `F5`

### Debug Tests
1. Open test file
2. Click "Debug Test" above test function
3. Or select `Python: Run Tests` and `F5`

---

## 🧪 Testing

### Run All Tests
- Click Testing icon (beaker) → "Run All Tests"
- Or: `Ctrl+Shift+P` → "Tasks: Run Task" → "Run tests"

### Run Single Test
- Click "Run Test" above test function
- Or right-click test → "Run Test"

### Coverage Report
- Run task: `Run tests with coverage`
- Open `htmlcov/index.html` in browser

---

## 📝 Git Workflow

### Standard Commit Flow
1. Edit files
2. `Ctrl+Shift+B` (rebuild)
3. `Ctrl+Shift+G` (Source Control)
4. Stage changes, write message, commit
5. Run task: `Publish artifacts`

### Git Safety Checks
Publishing automatically checks:
- ✅ Working tree is clean
- ✅ Branch is not behind upstream
- ✅ Artifacts built from correct commit

---

## 🔍 Navigation

| Action | Shortcut |
|--------|----------|
| Go to definition | `F12` |
| Peek definition | `Alt+F12` |
| Find references | `Shift+F12` |
| Search files | `Ctrl+Shift+F` |
| Go to symbol | `Ctrl+T` |
| Go back | `Alt+Left` |

---

## 🎨 Python Development

### Auto-Configured
- **Formatter:** Black (on save)
- **Linter:** Ruff
- **Type Checker:** Mypy
- **Imports:** Auto-organize on save

### Manual Format
- `Shift+Alt+F` - Format document
- `Ctrl+K Ctrl+F` - Format selection

---

## 📊 Quick Workflows

### "I want to build and test"
1. `Ctrl+Shift+B` (build)
2. Click Testing → "Run All Tests"
3. Review output

### "I want to publish"
1. `Ctrl+Shift+B` (rebuild all)
2. `Ctrl+Shift+G` (commit changes)
3. Run task: `Publish artifacts`

### "I want to debug a failing test"
1. Open test file
2. Click "Debug Test" above failing test
3. Inspect variables in Debug panel

### "I want to prepare for journal submission"
1. Run task: `Pre-submission check`
2. Fix any issues
3. Run task: `Generate replication report`
4. Review `output/replication_report.html`

---

## 🔧 Troubleshooting

### "Python interpreter not found"
- `Ctrl+Shift+P` → "Python: Select Interpreter"
- Choose `.env/bin/python`

### "Import errors"
- Verify PYTHONPATH set (check settings.json)
- Or use task: "Run Python script with environment"

### "Tests not discovered"
- `Ctrl+Shift+P` → "Python: Configure Tests"
- Select pytest, then `tests` directory

### "Tasks don't appear"
- `Ctrl+Shift+P` → "Developer: Reload Window"

---

## 📚 Full Documentation

**Comprehensive guide:** See `docs/vscode_integration.md`

**Other resources:**
- `README.md` - Project overview
- `QUICKSTART.md` - 5-minute setup
- `docs/` - Full documentation

---

## 💡 Tips

**Multi-cursor editing:**
- `Alt+Click` - Add cursor
- `Ctrl+Alt+Up/Down` - Add cursor above/below
- `Ctrl+D` - Select next occurrence

**Terminal:**
- ``Ctrl+` `` - Toggle terminal
- `Ctrl+Shift+5` - Split terminal
- Multiple terminals: Click `+` dropdown

**Workspace:**
- `Ctrl+K Ctrl+O` - Open folder
- `Ctrl+K F` - Close folder
- Workspace saved automatically

---

**Print this page** and keep it handy while learning VS Code! 

For detailed explanations, see `docs/vscode_integration.md`.
