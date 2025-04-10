from util.workshop import *
from util.translator import *
from util.config import *
from util.file import *
from util.steamcmd import *
from util.git import *
import logging
import argparse
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
if not os.path.exists(result_path):
    os.makedirs(result_path)
for game_version in config["game"]["versions"]:
    output_path = os.path.join(result_path, game_version)
    if not os.path.exists(output_path):
        os.makedirs(output_path)

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

if config["git"]["enabled"]:
    git.pull()

# Get the latest mods from the Steam Workshop
workshop = WorkshopNewMods(config["workshop"]["game_id"], config["workshop"]["text"])
new_mods = workshop.get_mods(config["workshop"]["depth"])

# Combine the new mods with the existing ones
for mod_id in new_mods:
    if mod_id not in config["workshop"]["ids"]:
        config["workshop"]["ids"].append(mod_id)
        logging.info(f"New mod found: {mod_id}")

# Download the mods using steamcmd
steamClient = steamdownloader(config["steam"]["username"], os.path.join(workpath, "steamcmd"))
steamClient.download(config["workshop"]["game_id"], config["workshop"]["ids"])

# Load the translator
if config["translator"]["type"] == "LLM":
    translator = TranslatorLLM(config["translator"]["min_length"], config["translator"]["max_length"], config["translator"]["rate_limit"], config["translator"]["LLM_configs"])
elif config["translator"]["type"] == "google":
    translator = GoogleTranslator(config["translator"]["min_length"], config["translator"]["max_length"], config["translator"]["rate_limit"])
else:
    logging.error("Unsupported translator type")
    translator = GoogleTranslator()

for id in config["workshop"]["ids"]:
    mod_path = os.path.join(game_mod_path, id)
    mod_name = parse_mod_info(os.path.join(mod_path, "workshop_data.json"))
    support_versions = search_file(mod_path, config["game"]["versions"])

    if support_versions == {} or support_versions is None:
        logging.warning(f"Mod {id} cannot find any translation files")
        config["workshop"]["ids"].remove(id)
        continue
    for support_version in support_versions:
        file = CSV_File(id=id, name=mod_name, raw=support_versions[support_version], target=config["translator"]["target_lang"], translator=translator)
        if os.path.exists(os.path.join(data_path, f"{id}_{support_version}.toml")):
            file.load_old_data(os.path.join(data_path, f"{id}_{support_version}.toml"))
        file.transfer_data()
        file.save_data(data_path, f"{id}_{support_version}")
        if support_version == "default":
            for game_version in config["game"]["versions"]:
                file.save_result(os.path.join(result_path, game_version))
        else:
            file.save_result(os.path.join(result_path, support_version))

if config["git"]["enabled"]:
    git.push()

config.save_config()