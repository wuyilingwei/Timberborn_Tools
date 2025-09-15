"""
version: 2.2.0
author: Wuyilingwei
Main script for the mod translation tool
Target utils version:
workshop: 1.0.x
config: 1.0.x
file: 1.1.x
steamcmd: 1.0.x
git: 1.0.x
"""
from util.workshop import *
from util.translator import *
from util.config import *
from util.file import *
from util.steamcmd import *
from util.git import *
from util.helper import *
from util.mod_target import ModTarget
import logging
import shutil
import os

workpath = os.getcwd()
config = Config(os.path.join(workpath, "config.toml"))
game_mod_path = os.path.join(workpath, "steamcmd", "steamapps", "workshop", "content", str(config["workshop"]["game_id"]))
git_path = os.path.join(workpath, "git")
if not os.path.exists(git_path):
    os.makedirs(git_path)
if config["git"]["enabled"]:
    git = Git(git_path, config["git"]["branch"])
data_path = os.path.join(git_path, "data")
if not os.path.exists(data_path):
    os.makedirs(data_path)
result_path = os.path.join(git_path, "mod")
if os.path.exists(result_path):
    shutil.rmtree(result_path)
os.makedirs(result_path)

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

if config["git"]["enabled"]:
    git.pull()

# Get the latest mods from the Steam Workshop
workshop = WorkshopNewMods(config["workshop"]["game_id"], config["workshop"]["text"])
new_mods = workshop.get_mods(config["workshop"]["depth"])

# Combine the new mods with the existing ones
for mod_id in new_mods:
    if mod_id not in config["workshop"]["ids"]:
        config["workshop"]["ids"].append(mod_id)
        logger.info(f"New mod found: {mod_id}")

for black_id in config["workshop"]["blacklist_ids"]:
    if black_id in config["workshop"]["ids"]:
        config["workshop"]["ids"].remove(black_id)
        logger.info(f"Mod {black_id} is blacklisted and removed from the list")

# Download the mods using steamcmd
steamClient = steamdownloader(config["steam"]["username"], os.path.join(workpath, "steamcmd"))
steamClient.download(config["workshop"]["game_id"], config["workshop"]["ids"])

# Load the translator
if config["translator"]["type"] == "LLM":
    translator = TranslatorLLM(config["translator"]["min_length"], config["translator"]["max_length"], config["translator"]["rate_limit"], config["translator"]["LLM_configs"])
elif config["translator"]["type"] == "google":
    translator = GoogleTranslator(config["translator"]["min_length"], config["translator"]["max_length"], config["translator"]["rate_limit"])
else:
    logger.error("Unsupported translator type")
    exit(1)

# Create ModTarget instances for each mod
mod_targets = {}
valid_mod_ids = []

for id in config["workshop"]["ids"]:
    mod_path = os.path.join(game_mod_path, id)
    mod_name = parse_mod_info(os.path.join(mod_path, "workshop_data.json"))
    support_versions = search_versions(mod_path)

    if support_versions == {} or support_versions is None:
        logger.warning(f"Mod {id} cannot find any translation files")
        continue
    
    # Create ModTarget instance
    mod_target = ModTarget(
        mod_id=id,
        mod_name=mod_name,
        mod_path=mod_path,
        target_lang=config["translator"]["target_lang"],
        translator=translator
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

# Update the config with only valid mod IDs
config["workshop"]["ids"] = valid_mod_ids

# Process each ModTarget
for mod_id, mod_target in mod_targets.items():
    logger.info(f"Processing mod {mod_id}: {mod_target.mod_name}")
    
    # Load historical data
    mod_target.load_old_data(data_path)
    
    # Perform cross-version copying
    mod_target.cross_version_copy()
    
    # Translate with enhanced context
    mod_target.translate_all()
    
    # Save all version data
    mod_target.save_all_data(data_path)

if config["git"]["enabled"]:
    git.pull()
    git.push()

config.save_config()