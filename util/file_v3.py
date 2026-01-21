"""
version: 3.0.0
author: Wuyilingwei
This module provides TOML file management for v3
This module is used to read and write TOML files for mod data updates
No translation logic - only data preparation for cloud workflow
"""
import os
import csv
import toml
import logging
from collections import OrderedDict


class TomlFile:
    """
    TOML file reader and updater for mod data
    Prepares data for cloud translation workflow
    """
    
    def __init__(self, mod_id: str, mod_name: str, raw_csv_path: str) -> None:
        self.logger = logging.getLogger(self.__class__.__name__)
        self.mod_id = mod_id
        self.mod_name = mod_name
        self.raw_csv_path = raw_csv_path
        self.old_data = {}
        self.new_raw_data = {}
        self.updated_data = OrderedDict()
        
    def load_raw_csv(self) -> None:
        """Load raw CSV file from mod"""
        try:
            with open(self.raw_csv_path, 'r', encoding='utf-8') as file:
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
            self.logger.info(f"Loaded {len(self.new_raw_data)} entries from {self.raw_csv_path}")
        except FileNotFoundError:
            self.logger.error(f"File not found: {self.raw_csv_path}")
        except Exception as e:
            self.logger.error(f"Error loading data from {self.raw_csv_path}: {e}")
    
    def load_old_toml(self, toml_path: str) -> None:
        """Load existing TOML file if it exists"""
        try:
            if os.path.exists(toml_path):
                with open(toml_path, 'r', encoding='utf-8') as file:
                    self.old_data = toml.load(file, _dict=OrderedDict)
                self.logger.info(f"Loaded old data from {toml_path}")
            else:
                self.logger.info(f"No existing data file found: {toml_path}")
                self.old_data = OrderedDict()
        except Exception as e:
            self.logger.error(f"Error loading old data from {toml_path}: {e}")
            self.old_data = OrderedDict()
    
    def update_data(self) -> None:
        """
        Update data according to v3 requirements:
        - Add/update 'name' field with mod name
        - For new keys: create with 'new' field only
        - For existing keys with changed raw: add 'new' field alongside existing data
        - For unchanged keys: keep as-is
        - Preserve 'prompt' and 'field_prompt' fields
        """
        self.updated_data = OrderedDict()
        
        # Always update name field to current mod name
        self.updated_data['name'] = self.mod_name
        
        # Preserve field_prompt if it exists
        if 'field_prompt' in self.old_data:
            self.updated_data['field_prompt'] = self.old_data['field_prompt']
        
        # Process each key from raw data
        for key, new_value in self.new_raw_data.items():
            if key in self.old_data and isinstance(self.old_data[key], dict):
                # Key exists in old data
                old_entry = self.old_data[key]
                self.updated_data[key] = OrderedDict()
                
                # Check if raw value changed
                old_raw = old_entry.get('raw', '')
                
                if old_raw != new_value:
                    # Value changed - add 'new' field
                    # Copy all existing fields except old 'new' field
                    for field, value in old_entry.items():
                        if field != 'new':
                            self.updated_data[key][field] = value
                    
                    # Add 'new' field to indicate retranslation needed
                    self.updated_data[key]['new'] = new_value
                    
                    self.logger.info(f"Updated key '{key}': value changed from '{old_raw}' to '{new_value}'")
                else:
                    # Value unchanged - keep as-is
                    self.updated_data[key] = old_entry.copy()
            else:
                # New key - create with 'new' field only
                self.updated_data[key] = OrderedDict()
                self.updated_data[key]['new'] = new_value
                self.logger.info(f"New key '{key}' added with value '{new_value}'")
        
        # Preserve keys from old data that are not in new raw data
        # (they might have been removed from mod but we keep them for reference)
        for key in self.old_data:
            if key not in ['name', 'field_prompt'] and key not in self.updated_data:
                self.updated_data[key] = self.old_data[key]
                self.logger.debug(f"Preserved old key '{key}' (not in new raw data)")
    
    def save_toml(self, output_path: str, filename: str) -> None:
        """Save updated data to TOML file"""
        try:
            if not os.path.exists(output_path):
                os.makedirs(output_path)
            file_path = os.path.join(output_path, f"{filename}.toml")
            
            with open(file_path, 'w', encoding='utf-8') as file:
                toml.dump(self.updated_data, file)
            
            self.logger.info(f"Saved data to {file_path}")
        except Exception as e:
            self.logger.error(f"Error saving data to {output_path}/{filename}.toml: {e}")
    
    def process(self, old_toml_path: str, output_path: str, output_filename: str) -> None:
        """
        Complete processing pipeline:
        1. Load raw CSV from mod
        2. Load existing TOML if exists
        3. Update data according to v3 rules
        4. Save updated TOML
        """
        self.load_raw_csv()
        self.load_old_toml(old_toml_path)
        self.update_data()
        self.save_toml(output_path, output_filename)
