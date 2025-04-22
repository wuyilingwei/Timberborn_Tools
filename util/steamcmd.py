"""
version: 1.0.0
author: Wuyilingwei
This module provides steamcmd actions
"""
import os
import subprocess
import logging
import json
import zipfile

class steamdownloader:
    """
    Steam Workshop Downloader
    This class is used to download steam workshop items using steamcmd
    """
    def __init__(self, steam_username: str, steamcmd_workpath: str) -> None:
        self.steam_username = steam_username
        self.steamcmd_workpath = steamcmd_workpath
        self.logger = logging.getLogger(self.__class__.__name__)
        self.init_steamcmd()

    def init_steamcmd(self) -> None:
        if not os.path.exists(self.steamcmd_workpath):
            os.makedirs(self.steamcmd_workpath)
            self.logger.info(f"Created steamcmd work path {self.steamcmd_workpath}")
        if not os.path.exists(os.path.join(self.steamcmd_workpath, 'steamcmd.exe')):
            self.logger.info("Downloading steamcmd.zip")
            subprocess.run(['curl', '-o', os.path.join(self.steamcmd_workpath, 'steamcmd.zip'), 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip'], cwd=self.steamcmd_workpath)
            self.logger.info("Extracting steamcmd")
            with zipfile.ZipFile(os.path.join(self.steamcmd_workpath, 'steamcmd.zip'), 'r') as zip_ref:
                zip_ref.extractall(self.steamcmd_workpath)
            os.remove(os.path.join(self.steamcmd_workpath, 'steamcmd.zip'))
            self.logger.info("SteamCMD initialized")
            subprocess.run(['steamcmd/steamcmd.exe', '+login', self.steam_username, '+quit'], cwd='steamcmd')
        else:
            self.logger.info("SteamCMD already exists, skipping download")

    def download(self, gameid: str, ids: list[str]) -> None:
        """
        Download steam workshop items using steamcmd
        :param ids: List of steam workshop item IDs to download
        """
        if not os.path.exists(self.steamcmd_workpath):
            self.logger.error(f"SteamCMD work path {self.steamcmd_workpath} does not exist")
            return

        order_file_path = os.path.join(self.steamcmd_workpath, 'steamorder.txt')
        with open(order_file_path, 'w') as steamorder:
            steamorder.write(f'login {self.steam_username}\n')

            for id in ids:
                steamorder.write(f'workshop_download_item {gameid} {id.strip()}\n')
            steamorder.write('quit\n')

        subprocess.run([os.path.join(self.steamcmd_workpath, 'steamcmd.exe'), '+runscript', order_file_path], cwd=self.steamcmd_workpath)

        steam_workshop_dir = os.path.join(self.steamcmd_workpath, 'steamcmd', 'steamapps', 'workshop', 'content', '1062090')
        self.logger.info(f"Downloaded items to {steam_workshop_dir}")

def parse_mod_info(file_path) -> str:
    mod_info = 'Unknown'
    try:
        with open(file_path, 'r', encoding='utf-8-sig') as file:
            for line in file:
                line = line.strip()
                if ("\"Name\"" in line or "\"name\"" in line) and mod_info == 'Unknown':
                    mod_info = line.split(':')[1].strip().strip('",')
                    break
    except FileNotFoundError:
        logging.error(f"File not found: {file_path}")
    except json.JSONDecodeError:
        logging.error(f"Error decoding JSON from file: {file_path}")
    except Exception as e:
        logging.error(f"Error reading file {file_path}: {e}")
    return mod_info