# Project Initialization (One-Time Setup)

**Document Type**: Bootstrap instructions  
**Target Audience**: LLMs (executing setup)  
**Purpose**: Get project environment running from fresh clone  
**Usage**: Run once after cloning repository, never again  
**Last Updated**: 2025-12-30

---

## Prerequisites Check

Before running these commands, verify:
- Python 3.8+ installed and in PATH
- Git installed (you cloned the repo, so ✓)
- VS Code installed (recommended, not required)

---

## Setup Procedure

### Step 1: Create Virtual Environment

```powershell
# Windows
python -m venv .venv
```

```bash
# macOS/Linux
python3 -m venv .venv
```

**Expected result**: `.venv/` directory created in project root

---

### Step 2: Activate Virtual Environment

```powershell
# Windows
.venv\Scripts\Activate.ps1
```

```bash
# macOS/Linux
source .venv/bin/activate
```

**Expected result**: Prompt shows `(.venv)` prefix

**Note**: If Windows PowerShell execution policy blocks activation:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

### Step 3: Upgrade pip

```powershell
python -m pip install --upgrade pip
```

**Expected result**: Latest pip version installed

---

### Step 4: Install Dependencies

```powershell
pip install -r requirements.txt
```

**Expected result**: All packages from requirements.txt installed

**Current dependencies** (as of 2025-12-15):
**Current dependencies**: See `requirements.txt` (source of truth).

Key packages used by the empirical Wikipedia N-link analysis include:
- duckdb
- pyarrow
- numpy
- pandas

---

### Step 5: Verify Installation

```powershell
# Check Python environment
python --version

# Check installed packages
pip list
```

**Expected result**: 
- Python 3.8+
- All dependencies listed

---

### Step 6: Open in VS Code (Optional)

```powershell
code self-reference-modeling.code-workspace
```

**Expected result**: 
- Workspace opens with correct settings
- Python interpreter auto-detected at `.venv/Scripts/python.exe` (Windows) or `.venv/bin/python` (macOS/Linux)
- System prompts loaded from `.vscode/settings.json`

---

## Validation Checklist

After setup, verify:

- [ ] Virtual environment created (`.venv/` directory exists)
- [ ] Virtual environment activated (prompt shows `(.venv)`)
- [ ] Dependencies installed (`pip list` shows mwparserfromhell, mwxml, requests)
- [ ] VS Code workspace opens (if using VS Code)
- [ ] Python interpreter configured (check VS Code status bar)

---

## Next Steps

**For LLMs**: After completing initialization, read bootstrap documentation:
1. [llm-facing-documentation/README.md](llm-facing-documentation/README.md) - Project overview and navigation
2. [llm-facing-documentation/project-timeline.md](llm-facing-documentation/project-timeline.md) - Recent 3-5 entries
3. Ask user what to work on

**For humans**: See [human-facing-documentation/project-setup.md](human-facing-documentation/project-setup.md) for complete setup guide with context.

---

## Troubleshooting

**Issue**: `python` not found
- **Solution**: Try `python3` or verify Python installation in PATH

**Issue**: Virtual environment won't activate (Windows)
- **Solution**: Run PowerShell as Administrator, set execution policy (see Step 2)

**Issue**: pip install fails with permission error
- **Solution**: Ensure virtual environment is activated (`.venv` prefix in prompt)

**Issue**: VS Code doesn't detect Python interpreter
- **Solution**: Open command palette (Ctrl+Shift+P), search "Python: Select Interpreter", choose `.venv/Scripts/python.exe`

---

## Platform-Specific Notes

**Windows**:
- Virtual environment: `.venv\Scripts\`
- Python executable: `.venv\Scripts\python.exe`
- Activation: `.venv\Scripts\Activate.ps1`

**macOS/Linux**:
- Virtual environment: `.venv/bin/`
- Python executable: `.venv/bin/python`
- Activation: `source .venv/bin/activate`

---

**After initialization, this document is not needed for regular work.**
