"""
version: 3.1.0
author: Wuyilingwei
Main script for the mod data update tool
Focus: Fetch new mods, download them, and update TOML data files
Translation handled by cloud workflow, but git operations for data repository remain
Single-version tracking: Only keep latest version, merge unique keys from older versions
Target utils version:
workshop: 1.0.x
config: 1.0.x
file: 3.0.x
steamcmd: 1.0.x
helper: 1.0.x
mod_target: 3.1.x
git: 1.0.x
"""
from util.workshop import *
from util.config import *
from util.file import *
from util.steamcmd import *
from util.helper import *
from util.git import *
from util.mod_target import ModTarget
import logging
import os

# Step 1: Initialize paths and configuration
workpath = os.getcwd()
config = Config(os.path.join(workpath, "config.toml"))
game_mod_path = os.path.join(workpath, "steamcmd", "steamapps", "workshop", "content", str(config["workshop"]["game_id"]))

# Setup git paths
git_path = os.path.join(workpath, "git")
if not os.path.exists(git_path):
    os.makedirs(git_path)
if config["git"]["enabled"]:
    git = Git(git_path, config["git"]["branch"])
data_path = os.path.join(git_path, "data")
if not os.path.exists(data_path):
    os.makedirs(data_path)

# Step 2: Setup logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler(config["common"]["logPath"], encoding='utf-8')
file_handler.setLevel(config["common"]["fileLevel"])
file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(file_formatter)

console_handler = logging.StreamHandler()
console_handler.setLevel(config["common"]["consoleLevel"])
console_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(console_formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)

logger.info("=" * 80)
logger.info("Timberborn Mod Data Update Tool v3.1")
logger.info("Single-version tracking with old version key merging")
logger.info("=" * 80)

# Pull data repository if git enabled
if config["git"]["enabled"]:
    logger.info("Step 0: Pulling data repository...")
    git.pull()

# Fetch new mods from Steam Workshop
logger.info("Step 1: Fetching latest mods from Steam Workshop...")
workshop = WorkshopNewMods(config["workshop"]["game_id"], config["workshop"]["text"])
new_mods = workshop.get_mods(config["workshop"]["depth"])

# Combine new mods with existing ones
new_mod_count = 0
for mod_id in new_mods:
    if mod_id not in config["workshop"]["ids"]:
        config["workshop"]["ids"].append(mod_id)
        new_mod_count += 1
        logger.info(f"New mod found: {mod_id}")
logger.info(f"Found {new_mod_count} new mods")

# Remove blacklisted mods
for black_id in config["workshop"]["blacklist_ids"]:
    if black_id in config["workshop"]["ids"]:
        config["workshop"]["ids"].remove(black_id)
        logger.info(f"Mod {black_id} is blacklisted and removed from the list")

logger.info(f"Total mods to process: {len(config['workshop']['ids'])}")

# Download mods using steamcmd
logger.info("Step 2: Downloading mods using SteamCMD...")
steamClient = steamdownloader(config["steam"]["username"], os.path.join(workpath, "steamcmd"))
steamClient.download(config["workshop"]["game_id"], config["workshop"]["ids"])

# Create ModTarget instances for each mod
logger.info("Step 3: Creating mod targets...")
mod_targets = {}
valid_mod_ids = []

for id in config["workshop"]["ids"]:
    mod_path = os.path.join(game_mod_path, id)
    mod_name = parse_mod_info(os.path.join(mod_path, "workshop_data.json"))
    versions = search_versions(mod_path)
    support_versions = search_file(mod_path, versions, keyword="en")

    if support_versions == {} or support_versions is None:
        logger.warning(f"Mod {id} cannot find any translation files")
        continue
    
    # Create ModTarget instance (no translator needed in v3)
    mod_target = ModTarget(
        mod_id=id,
        mod_name=mod_name,
        mod_path=mod_path
    )
    
    # Add all versions to the ModTarget
    for support_version, raw_file_path in support_versions.items():
        if mod_target.add_version(support_version, raw_file_path):
            logger.info(f"Added version {support_version} for mod {id}")
    
    if mod_target.has_valid_versions():
        mod_targets[id] = mod_target
        valid_mod_ids.append(id)
    else:
        logger.warning(f"Mod {id} has no valid versions")

# Update config with only valid mod IDs
config["workshop"]["ids"] = valid_mod_ids

# Process each ModTarget to update data
logger.info("Step 4: Updating TOML data files...")
processed_count = 0
error_count = 0

for mod_id, mod_target in mod_targets.items():
    try:
        logger.info(f"Processing mod {mod_id}: {mod_target.mod_name}")
        
        # Load historical data (both single-file and multi-version formats for migration)
        mod_target.load_old_data(data_path)
        
        # Update data with change detection (uses latest version, merges old unique keys)
        mod_target.update_all_data()
        
        # Save single version data (without version suffix)
        mod_target.save_all_data(data_path)
        
        processed_count += 1
    except Exception as e:
        logger.error(f"Error processing mod {mod_id}: {e}")
        error_count += 1

# Save configuration
logger.info("Step 5: Saving configuration...")
config.save_config()

# Push data repository if git enabled
if config["git"]["enabled"]:
    logger.info("Step 6: Pushing updated data to repository...")
    git.pull()  # Pull first to avoid conflicts
    git.push()

# Summary
logger.info("=" * 80)
logger.info("Processing complete!")
logger.info(f"Mods processed: {processed_count}")
logger.info(f"Errors: {error_count}")
logger.info(f"Data files saved to: {data_path}")
logger.info("Next: Cloud workflow will handle translation and publishing")
logger.info("=" * 80)