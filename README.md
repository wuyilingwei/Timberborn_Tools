# Timberborn Tools

Tools for managing Timberborn mod translations and data updates.

## Version 3 (Current)

V3 focuses on mod data preparation for cloud-based translation workflows.

### Features
- Fetch new mods from Steam Workshop
- Download mods via SteamCMD
- Update TOML data files with change detection
- Prepare data for cloud translation workflow

### Quick Start

1. Install dependencies:
   ```bash
   pip install -r requirments.txt
   ```

2. Configure `config.toml` (copy from `config.toml.example`)

3. Run:
   ```bash
   python main_v3.py
   ```

### Documentation
- [V3 Migration Guide](V3_MIGRATION_GUIDE.md) - Detailed documentation and migration from v2

### Key Changes in V3
- **No translation**: Translation handled by cloud workflow
- **No git operations**: Publishing handled by cloud workflow  
- **New TOML format**: Supports change detection with `new` field
- **Simplified workflow**: Focus on data preparation only

For legacy v2 functionality, see `main.py` (deprecated).
