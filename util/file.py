"""
version: 1.0.0
author: Wuyilingwei
This module provides CSV file management
This module is used to read and write CSV files
This module is also used to handle translation process for CSV files
Target utils version:
translator: 1.0.x
TODO: Ignore built-in key in game.
"""
import os
import csv
import toml
import logging
from util.translator import *

def search_file(path: str, versions: list[str], keyword = "en") -> dict[str, str]:
    """
    search for the file in the path and versions
    path: the path to search
    versions: the versions to search for
    keyword: the keyword to search for
    If not multiple versions, will return the default
    """
    logger = logging.getLogger(__name__)
    def search_helper(path: str, keyword) -> str:
        for root, dirs, files in os.walk(path):
            for file in files:
                if keyword in file and (file.endswith('.csv') or file.endswith('.txt')):
                    # check header
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        firstline = f.readline().strip()
                        if 'ID,Text,Comment' in firstline:
                            return os.path.join(root, file)
            for file in files:
                # try match other language file
                if file.endswith('.csv') or file.endswith('.txt'):
                    with open(os.path.join(root, file), 'r', encoding='utf-8') as f:
                        firstline = f.readline().strip()
                        if 'ID,Text,Comment' in firstline:
                            return os.path.join(root, file)
        return None
    logger = logging.getLogger(__name__)
    result = {}
    is_mult_version = False
    for version in versions:
        logger.debug(f"Searching for {keyword} in {os.path.join(path, version)}")
        if os.path.exists(os.path.join(path, version)):
            result[version] = search_helper(os.path.join(path, version), keyword)
            is_mult_version = True
    if not is_mult_version:
        logger.debug(f"Searching for {keyword} in {path}")
        result["default"] = search_helper(path, keyword)
    if len(result) == 0:
        logger.error(f"ERROR: {path} not found")
        return None
    return result


class CSV_File:
    """
    csv file reader and translator
    all target languages should be import as a list of strings
    eg: ['en', 'zh', 'ja', 'ko']
    the retruned data should be a dict of dicts
    eg: {key1: {raw: 'import value1', en: 'value1', zh: '值1'}, key2: {raw: 'import value2', en: 'value2', zh: '值2'}}

    """
    id: int
    target: list[str]
    old_data: dict[str, dict]
    data: dict[str, dict]
    translator: Translator
    logger: logging.Logger

    def __init__(self, id: int, name:str, raw: str, target: list[str], translator: Translator) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.id = id
        self.name = name
        self.old_data = {}
        self.data = {}
        self.target = target
        self.translator = translator
        self.load_raw(raw)

    def load_raw(self, path: str) -> None:
        try:
            with open(path, 'r', encoding='utf-8') as file:
                first_line = file.readline()
                if first_line.startswith('\ufeff'):
                    first_line = first_line.lstrip('\ufeff')  # 移除 BOM
                reader = csv.reader([first_line] + file.readlines())
                for row in reader:
                    key = row[0]
                    if key == 'id' or key == 'ID' or "Comment" in self.old_data.get(key, {}).get('raw', ''):
                        continue
                    values = row[1:]
                    self.data[key] = {'raw': values[0]}
            self.logger.info(f"Loaded data from {path}")
            self.logger.debug(f"Data: {self.data}")
        except FileNotFoundError:
            self.logger.error(f"File not found: {path}")
        except Exception as e:
            self.logger.error(f"Error loading data from {path}: {e}")

    def load_old_data(self, path: str) -> None:
        """
        Load old data from a TOML file into old_data.
        """
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as file:
                    self.old_data = toml.load(file)
                self.logger.info(f"Loaded old data from {path}")
            else:
                self.logger.warning(f"Old data file not found: {path}")
                self.old_data = {}
        except Exception as e:
            self.logger.error(f"Error loading old data from {path}: {e}")
            self.old_data = {}

    def save_data(self, path: str, filename: str) -> None:
        """
        Save current data to a TOML file.
        """
        try:
            # 确保目录存在
            if not os.path.exists(path):
                os.makedirs(path)
            file_path = os.path.join(path, f"{filename}.toml")
            with open(file_path, 'w', encoding='utf-8') as file:
                toml.dump(self.data, file)
            self.logger.info(f"Saved data to {file_path}/{filename}.toml")
        except Exception as e:
            self.logger.error(f"Error saving data to {file_path}/{filename}.toml: {e}")

    def save_result(self, path: str) -> None:
        """
        Save translation results to separate files for each target language.
        Each file contains only the ID and Text fields, with Comment as a placeholder.
        """
        if not os.path.exists(path):
            os.makedirs(path)
        try:
            for lang in self.target:
                file_path = os.path.join(path, f"{lang}_{self.id}_{self.name}.csv".replace(" ", "_"))
                with open(file_path, 'w', encoding='utf-8', newline='') as file:
                    writer = csv.writer(file)
                    header = ['ID', 'Text', 'Comment']
                    writer.writerow(header)
                    for key, values in self.data.items():
                        text = values.get(lang, '')
                        row = [key, text, '-']
                        writer.writerow(row)
                self.logger.info(f"Saved result for language '{lang}' to {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving result to {path}: {e}")

    def transfer_data(self) -> dict[str, dict]:
        for lang in self.target:
            # for each language
            if lang == 'raw':
                continue
            for key, values in self.data.items():
                # check if the key is in old data and the value is the same
                if key in self.old_data and lang in self.old_data[key] and values['raw'].replace('\u00A0', ' ') == self.old_data[key]['raw']:
                    self.data[key][lang] = self.old_data[key][lang]
                    self.logger.info(f"Matched {values['raw']} to {lang}: {self.data[key][lang]}")
                else:
                    try:
                        # check if the value is empty
                        max_retries = 3
                        while max_retries > 0:
                            result = self.translator.translate(values['raw'], lang)
                            self.logger.debug(f"Translation result: {result}")
                            if result["code"] == 200:
                                break
                            else:
                                max_retries -= 1
                                self.logger.warning(f"Retrying translation for {values['raw']} to {lang}, attempts left: {max_retries}")
                        if max_retries == 0 and result["code"] != 200:
                            self.logger.error(f"Translation failed for {values['raw']} to {lang}: {result['text']}")
                            self.data[key][lang] = values['raw']
                            raise Exception("Max retries exceeded")
                        self.data[key][lang] = result["text"]
                    except Exception as e:
                        self.logger.error(f"Error translating {values['raw']} to {lang}: {e}")
                        self.data[key][lang] = values['raw']
        self.logger.info("Data transfer completed")
        self.logger.debug(f"Final Data: {self.data}")
        return self.data
