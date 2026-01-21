"""
version: 3.0.0
author: Wuyilingwei
This module provides CSV file management
This module is used to read and write CSV/TOML files
For v3: Focus on data update with change detection, no translation
Target utils version:
None (standalone)
"""
import os
import csv
import toml
import logging
from collections import OrderedDict



class CSV_File:
    """
    CSV file reader and TOML data updater for v3
    Handles data comparison and change detection
    No translation - only data preparation for cloud workflow
    """
    id: int
    old_data: dict[str, dict]
    data: dict[str, dict]
    new_raw_data: dict[str, str]
    logger: logging.Logger

    def __init__(self, id: int, name: str, raw: str) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.id = id
        self.name = name
        self.old_data = {}
        self.data = OrderedDict()
        self.new_raw_data = {}
        self.load_raw(raw)

    def load_raw(self, path: str) -> None:
        """Load raw CSV file from mod"""
        try:
            with open(path, 'r', encoding='utf-8') as file:
                first_line = file.readline()
                if first_line.startswith('\ufeff'):
                    first_line = first_line.lstrip('\ufeff')  # Remove BOM
                reader = csv.reader([first_line] + file.readlines())
                for row in reader:
                    if not row:
                        continue
                    key = row[0]
                    # Skip header and comment rows
                    if key in ['id', 'ID']:
                        continue
                    # Skip comment rows based on the Comment column
                    if len(row) > 2 and row[2].strip().lower() == 'comment':
                        continue
                    if len(row) > 1:
                        values = row[1:]
                        self.new_raw_data[key] = values[0] if values[0] else ""
            self.logger.info(f"Loaded {len(self.new_raw_data)} entries from {path}")
        except FileNotFoundError:
            self.logger.error(f"File not found: {path}")
        except Exception as e:
            self.logger.error(f"Error loading data from {path}: {e}")

    def load_old_data(self, path: str) -> None:
        """Load existing TOML file if it exists"""
        try:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as file:
                    self.old_data = toml.load(file, _dict=OrderedDict)
                self.logger.info(f"Loaded old data from {path}")
            else:
                self.logger.info(f"No existing data file found: {path}")
                self.old_data = OrderedDict()
        except Exception as e:
            self.logger.error(f"Error loading old data from {path}: {e}")
            self.old_data = OrderedDict()

    def save_data(self, path: str, filename: str) -> None:
        """Save updated data to TOML file"""
        try:
            if not os.path.exists(path):
                os.makedirs(path)
            file_path = os.path.join(path, f"{filename}.toml")
            with open(file_path, 'w', encoding='utf-8') as file:
                toml.dump(self.data, file)
            self.logger.info(f"Saved data to {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving data to {file_path}: {e}")

    def update_data(self) -> None:
        """
        Update data according to v3 requirements:
        - Add/update 'name' field with mod name
        - For new keys: create with 'new' field only
        - For existing keys with changed raw: add 'new' field alongside existing data
        - For unchanged keys: keep as-is
        - Preserve 'prompt' and 'field_prompt' fields
        """
        self.data = OrderedDict()
        
        # Always update name field to current mod name
        self.data['name'] = self.name
        
        # Preserve field_prompt if it exists
        if 'field_prompt' in self.old_data:
            self.data['field_prompt'] = self.old_data['field_prompt']
        
        # Process each key from raw data
        for key, new_value in self.new_raw_data.items():
            if key in self.old_data and isinstance(self.old_data[key], dict):
                # Key exists in old data
                old_entry = self.old_data[key]
                self.data[key] = OrderedDict()
                
                # Check if raw value changed
                old_raw = old_entry.get('raw', '')
                
                if old_raw != new_value:
                    # Value changed - add 'new' field
                    # Copy all existing fields except old 'new' field
                    for field, value in old_entry.items():
                        if field != 'new':
                            self.data[key][field] = value
                    
                    # Add 'new' field to indicate retranslation needed
                    self.data[key]['new'] = new_value
                    
                    self.logger.info(f"Updated key '{key}': value changed from '{old_raw}' to '{new_value}'")
                else:
                    # Value unchanged - keep as-is
                    self.data[key] = old_entry.copy()
            else:
                # New key - create with 'new' field only
                self.data[key] = OrderedDict()
                self.data[key]['new'] = new_value
                self.logger.info(f"New key '{key}' added with value '{new_value}'")
        
        # Preserve keys from old data that are not in new raw data
        for key in self.old_data:
            if key not in ['name', 'field_prompt'] and key not in self.data:
                self.data[key] = self.old_data[key]
                self.logger.debug(f"Preserved old key '{key}' (not in new raw data)")


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
