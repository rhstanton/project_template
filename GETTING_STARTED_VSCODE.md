# Getting Started in VS Code

**New to this project? Start here!**

---

## 🎯 First Time Setup

1. **Install Recommended Extensions**
   - VS Code will prompt you on first open
   - Click "Install All" or install individually
   - **Key extension:** "Makefile Tools" shows all Make targets in sidebar

2. **Open Command Palette**
   - Press `Ctrl+Shift+P` (or `Cmd+Shift+P` on Mac)
   - This is your gateway to everything!

3. **Setup Environment** (first time only)
   - `Ctrl+Shift+P` → type "task" → Enter
   - Select: **"Setup environment"**
   - Wait ~10-15 minutes for installation

4. **Verify Setup**
   - Run task: **"Verify environment"**
   - Should see: ✅ Python, Julia, packages OK

---

## 💡 Core Workflow

### Building Artifacts

**Build everything:**

- Press `Ctrl+Shift+B` (fastest!)
- Or run task: "Build all artifacts"

**Build specific artifact:**

- `Ctrl+Shift+P` → "Tasks: Run Task"
- Select: "Build price_base" or "Build remodel_base"
- Or use integrated terminal: ``Ctrl+` `` then type `make price_base`

### Testing

**Run tests:**

- Click **Testing** icon in left sidebar (beaker icon)
- Click "Run All Tests"
- Or run task: "Run tests"

### Publishing

**Publish to paper directory:**

- Run task: "Publish artifacts"
- (Make sure you've committed changes first!)

---

## 🔍 How to Find Available Tasks

**Method 1: Task Picker**

1. Press `Ctrl+Shift+P`
2. Type: `task run`
3. Press Enter
4. **Browse the full list** of available tasks!

**Method 2: Makefile Tools Extension**

1. Install "Makefile Tools" extension (recommended automatically)
2. Click **Makefile icon** in left sidebar
3. See **all Make targets** from Makefile
4. Click any target to run it!

**Method 3: Integrated Terminal**

- Press ``Ctrl+` `` to open terminal
- Type any `make` command directly
- Same as command line!

---

## 📚 Full Documentation

- **`.vscode/QUICK_REFERENCE.md`** - One-page cheat sheet (print and keep handy!)
- **`docs/vscode_integration.md`** - Complete VS Code guide (500+ lines)
- **`README.md`** - Project overview
- **`QUICKSTART.md`** - 5-minute command-line guide

---

## 🎨 Keyboard Shortcuts to Remember

| Action | Shortcut |
|--------|----------|
| **Build all** | `Ctrl+Shift+B` |
| **Command Palette** | `Ctrl+Shift+P` |
| **Run Task** | `Ctrl+Shift+P` → "task" |
| **Debug** | `F5` |
| **Terminal** | ``Ctrl+` `` |
| **Source Control** | `Ctrl+Shift+G` |
| **Testing** | Click beaker icon |

---

## 🆘 Forgot How to Use VS Code?

**Just remember one shortcut: `Ctrl+Shift+P`**

Type what you want to do:

- "task" → Run tasks
- "debug" → Start debugging  
- "test" → Configure tests
- "python" → Python commands
- "git" → Git commands

The Command Palette is **searchable** - you don't need to memorize anything!

---

## 🚀 Quick Start Example

**Let me build and test something:**

1. Press `Ctrl+Shift+B` → Builds all artifacts
2. Click Testing icon → "Run All Tests"
3. Press `Ctrl+Shift+G` → Commit changes
4. `Ctrl+Shift+P` → "task" → "Publish artifacts"

Done! All without touching the command line.

---

## 🔗 See Also

- [.vscode/QUICK_REFERENCE.md](.vscode/QUICK_REFERENCE.md) - Keyboard shortcuts reference
- [docs/vscode_integration.md](docs/vscode_integration.md) - Complete guide
- [docs/troubleshooting.md](docs/troubleshooting.md) - Common issues

**Last updated:** January 18, 2026
