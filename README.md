# Timberborn Tools

Tools for managing Timberborn mod translations and data updates.

## Version 3

V3 focuses on mod data preparation for cloud-based translation workflows.

### Key Changes in V3
- **No translation**: Translation handled by cloud workflow
- **No git operations**: Publishing handled by cloud workflow  
- **New TOML format**: Supports change detection with `new` field
- **Simplified workflow**: Focus on data preparation only

### Features
- Fetch new mods from Steam Workshop
- Download mods via SteamCMD
- Update TOML data files with change detection
- Prepare data for cloud translation workflow

### Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure `config.toml` (copy from `config.toml.example`)

3. Run:
   ```bash
   python main.py
   ```

### TOML Format

Change detection signals retranslation via `new` field:

```toml
name = "Metal Staircase Mod"

["KnatteTobbert.MetalStaircase.DisplayName"]
raw = "Metal Stairs"
new = "Metal Staircase"  # Cloud workflow translates and removes this
enUS = "Metal Stairs"
zhCN = "金属楼梯"
```

### Workflow

1. Tool discovers and downloads mods from Steam Workshop
2. Tool updates TOML files with change detection (adds `new` field where needed)
3. Cloud workflow detects entries with `new` field
4. Cloud workflow performs translation
5. Cloud workflow updates `raw` and language fields, removes `new` field
