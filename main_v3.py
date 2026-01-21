"""
version: 3.0.0
author: Wuyilingwei
Main script for the mod data update tool (v3)
Focus: Fetch new mods, download them, and update TOML data files
Translation and publishing are handled by cloud workflow
Target utils version:
workshop: 1.0.x
config: 1.0.x
file_v3: 3.0.x
steamcmd: 1.0.x
helper: 1.0.x
"""
import os
import sys
import logging
from util.workshop import WorkshopNewMods
from util.config import Config
from util.file_v3 import TomlFile
from util.steamcmd import steamdownloader, parse_mod_info
from util.helper import search_versions, search_file

# Setup paths
workpath = os.getcwd()
config = Config(os.path.join(workpath, "config.toml"))
game_mod_path = os.path.join(workpath, "steamcmd", "steamapps", "workshop", "content", str(config["workshop"]["game_id"]))
data_path = os.path.join(workpath, "data")

# Ensure data directory exists
if not os.path.exists(data_path):
    os.makedirs(data_path)

# Basic logger setup
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
logger.info("Starting Timberborn Mod Data Update Tool v3")
logger.info("=" * 80)

# Step 1: Get the latest mods from the Steam Workshop
logger.info("Step 1: Fetching latest mods from Steam Workshop...")
workshop = WorkshopNewMods(config["workshop"]["game_id"], config["workshop"]["text"])
new_mods = workshop.get_mods(config["workshop"]["depth"])

# Combine the new mods with the existing ones
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

# Step 2: Download the mods using steamcmd
logger.info("Step 2: Downloading mods using SteamCMD...")
steamClient = steamdownloader(config["steam"]["username"], os.path.join(workpath, "steamcmd"))
steamClient.download(config["workshop"]["game_id"], config["workshop"]["ids"])

# Step 3: Update TOML data files for each mod
logger.info("Step 3: Updating TOML data files...")
valid_mod_ids = []
processed_count = 0
error_count = 0

for mod_id in config["workshop"]["ids"]:
    try:
        mod_path = os.path.join(game_mod_path, mod_id)
        
        # Check if mod path exists
        if not os.path.exists(mod_path):
            logger.warning(f"Mod {mod_id} path does not exist: {mod_path}")
            continue
        
        # Get mod name
        mod_name = parse_mod_info(os.path.join(mod_path, "workshop_data.json"))
        logger.info(f"Processing mod {mod_id}: {mod_name}")
        
        # Search for versions
        versions = search_versions(mod_path)
        
        if not versions:
            logger.warning(f"Mod {mod_id} has no valid versions")
            continue
        
        # Search for translation files in each version
        version_files = search_file(mod_path, versions, keyword="en")
        
        if not version_files or all(v is None for v in version_files.values()):
            logger.warning(f"Mod {mod_id} cannot find any translation files")
            continue
        
        # Process each version
        for version, raw_file_path in version_files.items():
            if raw_file_path is None:
                logger.warning(f"Mod {mod_id} version {version} has no translation file")
                continue
            
            try:
                # Create TomlFile instance
                toml_file = TomlFile(
                    mod_id=mod_id,
                    mod_name=mod_name,
                    raw_csv_path=raw_file_path
                )
                
                # Process: load raw, load old, update, save
                old_toml_path = os.path.join(data_path, f"{mod_id}_{version}.toml")
                output_filename = f"{mod_id}_{version}"
                
                toml_file.process(old_toml_path, data_path, output_filename)
                
                logger.info(f"Successfully processed mod {mod_id} version {version}")
                
            except Exception as e:
                logger.error(f"Error processing mod {mod_id} version {version}: {e}")
                error_count += 1
        
        valid_mod_ids.append(mod_id)
        processed_count += 1
        
    except Exception as e:
        logger.error(f"Error processing mod {mod_id}: {e}")
        error_count += 1

# Update the config with only valid mod IDs
config["workshop"]["ids"] = valid_mod_ids

# Step 4: Save updated config
logger.info("Step 4: Saving updated configuration...")
config.save_config()

# Summary
logger.info("=" * 80)
logger.info("Processing complete!")
logger.info(f"Total mods processed: {processed_count}")
logger.info(f"Errors encountered: {error_count}")
logger.info(f"Data files saved to: {data_path}")
logger.info("Next: Cloud workflow will handle translation and publishing")
logger.info("=" * 80)
