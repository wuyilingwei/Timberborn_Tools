# Timberborn Tools v3 Migration Guide

## Overview

Version 3 is a major refactoring that simplifies the tool's responsibility. All translation and publishing work is now handled by cloud workflows, so this tool focuses exclusively on:

1. Fetching new mods from Steam Workshop
2. Downloading mods via SteamCMD
3. Updating TOML data files with mod information

## Key Changes from v2 to v3

### What's Changed
- **Translation removed**: No longer performs translation - this is handled by cloud workflow
- **Git operations removed**: No longer pushes to git - this is handled by cloud workflow
- **New TOML format**: Updated data structure to support cloud workflow
- **Simplified workflow**: Focus on data preparation only

### New TOML Format

Each TOML file represents a mod, with the following structure:

```toml
name = "Mod Name"  # Optional, updated with mod name from workshop
field_prompt = ""  # Optional, extra prompt (not managed by this tool)

["ModKey.ItemName"]
raw = "Original Text"  # The original/current value
new = "Updated Text"   # Present when raw has been updated, needs retranslation
prompt = ""            # Optional, for additional context (not managed by this tool)
enUS = "Original Text"
zhCN = "原文"
zhTW = "原文"
ruRU = "Оригинальный текст"
jaJP = "原文"
frFR = "Texte original"
deDE = "Originaltext"
plPL = "Oryginalny tekst"
ptBR = "Texto Original"
```

### Field Behavior

1. **For new entries** (first time seeing this key):
   - Creates entry with only `new` field
   - Example: `new = "New Text"`
   - After translation: `raw` and language fields added, `new` removed

2. **For unchanged entries** (value hasn't changed):
   - Keeps all existing fields as-is
   - No `new` field added

3. **For changed entries** (value has changed):
   - Preserves all existing fields including `raw` and translations
   - Adds `new` field with the updated value
   - Example: `raw = "Old Text"`, `new = "New Text"`
   - After translation: `raw` updated to match `new`, `new` removed

4. **Name field**:
   - Always updated to match current mod name
   - Helps identify older data that might be missing optional fields

## Usage

### Running v3

```bash
python main_v3.py
```

### Prerequisites

1. Install dependencies:
   ```bash
   pip install -r requirments.txt
   ```

2. Configure `config.toml` (copy from `config.toml.example`):
   ```toml
   [workshop]
   game_id = 1062090
   text = "Mod"
   depth = 2
   ids = []
   blacklist_ids = []
   
   [steam]
   username = "your_steam_username"
   
   [common]
   consoleLevel = "INFO"
   fileLevel = "WARNING"
   logPath = "log.txt"
   ```

### Output

- TOML files are saved to `./data/` directory
- Format: `{mod_id}_{version}.toml`
- Example: `3275060459_version-0.6.toml`

## Workflow

### 1. Mod Discovery
```
Steam Workshop → Fetch new mods → Add to support list
```

### 2. Mod Download
```
SteamCMD → Download mods → Extract to steamcmd/steamapps/workshop/content/
```

### 3. Data Update
```
For each mod:
  - Load CSV translation file from mod
  - Load existing TOML (if exists)
  - Compare values:
    * New keys → add with 'new' field
    * Changed keys → add 'new' field alongside existing data
    * Unchanged keys → keep as-is
  - Save updated TOML
```

### 4. Cloud Workflow (not part of this tool)
```
- Detects 'new' fields in TOML files
- Performs translation
- Updates 'raw' and language fields
- Removes 'new' field
- Publishes to mod repository
```

## Testing

Run the test suite to verify functionality:

```bash
python test_v3.py
```

The test suite covers:
- New mod scenario
- Existing mod with no changes
- Existing mod with changes
- Mixed scenarios

## Migration from v2

### Code Changes
- Use `main_v3.py` instead of `main.py`
- Use `file_v3.py` instead of `file.py`
- `mod_target.py` and translation logic no longer needed

### Data Format
- Old TOML files will be automatically migrated on first run
- New structure will be generated based on current mod data

### Configuration
- Same `config.toml` structure
- Git configuration sections no longer used
- Translation configuration no longer used

## Architecture

```
main_v3.py
├── workshop.py      → Fetch new mods from Steam
├── steamcmd.py      → Download mods
├── file_v3.py       → Update TOML data
├── helper.py        → Search for version/files
└── config.py        → Configuration management
```

## Example Scenario

### Scenario: Mod author updates item name

**Before (existing TOML):**
```toml
["ModName.Item"]
raw = "Metal Stairs"
enUS = "Metal Stairs"
zhCN = "金属楼梯"
```

**After mod update (CSV now has "Metal Staircase"):**
```toml
["ModName.Item"]
raw = "Metal Stairs"
new = "Metal Staircase"  # ← Signals retranslation needed
enUS = "Metal Stairs"
zhCN = "金属楼梯"
```

**After cloud workflow translates:**
```toml
["ModName.Item"]
raw = "Metal Staircase"  # ← Updated
enUS = "Metal Staircase"  # ← Retranslated
zhCN = "金属楼梯间"       # ← Retranslated
# 'new' field removed
```

## Troubleshooting

### "No translation files found"
- Mod doesn't have a CSV file with format `ID,Text,Comment`
- Mod might not support localization
- Add to blacklist if not translatable

### "Version not found"
- Mod doesn't follow version folder structure
- Will use "default" version

### "Mod path does not exist"
- SteamCMD download failed
- Check Steam credentials
- Check network connection

## FAQ

**Q: Why remove translation from this tool?**
A: Cloud workflows provide better scalability, versioning, and collaboration for translation management.

**Q: What happens to old translations?**
A: They are preserved in the TOML files and only retranslated when values change.

**Q: Can I still use v2?**
A: Yes, but v3 is recommended for new deployments as it aligns with the cloud workflow architecture.

**Q: How do I contribute translations?**
A: Through the cloud workflow - this tool only prepares the data.

## Version History

- **v3.0.0**: Major refactor - focus on data preparation only
- **v2.x**: Integrated translation with LLM/Google Translate
- **v1.x**: Initial release with basic translation

## Support

For issues or questions:
- GitHub Issues: [wuyilingwei/Timberborn_Tools](https://github.com/wuyilingwei/Timberborn_Tools)
