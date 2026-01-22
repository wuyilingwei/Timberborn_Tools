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


def reorder_entry_fields(entry: OrderedDict) -> OrderedDict:
    """
    Reorder fields in entry to: raw, new, status, then language codes
    """
    if not isinstance(entry, dict):
        return entry
    
    ordered = OrderedDict()
    
    # Priority order: raw, new, status
    for field in ['raw', 'new', 'status']:
        if field in entry:
            ordered[field] = entry[field]
    
    # Then all other fields (language codes and others)
    for field, value in entry.items():
        if field not in ['raw', 'new', 'status']:
            ordered[field] = value
    
    return ordered



class CSV_File:
    """
    CSV file reader and TOML data updater for v3
    Handles data comparison and change detection
    No translation - only data preparation for cloud workflow
    """

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
                    # Skip keys containing '//' as they are used as separators
                    # Note: This checks for '//' anywhere in the key string
                    if '//' in key:
                        self.logger.debug(f"Skipping key '{key}' containing '//' (separator)")
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
            
            # Perform round-trip comparison for keys with 'new' field
            self._remove_identical_new_values(file_path)
        except Exception as e:
            self.logger.error(f"Error saving data to {file_path}: {e}")
    
    def _remove_identical_new_values(self, file_path: str) -> None:
        """
        Read back the saved TOML file and compare 'new' and 'raw' values.
        If they are identical after TOML round-trip, remove the 'new' field.
        """
        try:
            # Read back the file
            with open(file_path, 'r', encoding='utf-8') as file:
                saved_data = toml.load(file, _dict=OrderedDict)
            
            modified = False
            for key in saved_data:
                if key == '_meta':
                    continue
                entry = saved_data[key]
                if isinstance(entry, dict) and 'new' in entry and 'raw' in entry:
                    # Compare after round-trip
                    if entry['new'] == entry['raw']:
                        del entry['new']
                        modified = True
                        self.logger.info(f"Removed 'new' field for key '{key}': identical to 'raw' after TOML round-trip")
            
            # Save back if modified
            if modified:
                with open(file_path, 'w', encoding='utf-8') as file:
                    toml.dump(saved_data, file)
                self.logger.info(f"Updated {file_path} after round-trip comparison")
        except Exception as e:
            self.logger.error(f"Error in round-trip comparison for {file_path}: {e}")

    def update_data(self) -> None:
        """
        Update data according to v3 requirements:
        - Add/update '_meta' section with 'name' and 'field_prompt' fields
        - For new keys: create with 'new' field only
        - For existing keys with changed raw: add 'new' field alongside existing data
        - For unchanged keys: keep as-is
        - Preserve 'prompt' fields in individual entries
        """
        self.data = OrderedDict()
        
        # Create _meta section for metadata
        self.data['_meta'] = OrderedDict()
        self.data['_meta']['name'] = self.name
        
        # Preserve field_prompt if it exists in old data
        if 'field_prompt' in self.old_data:
            self.data['_meta']['field_prompt'] = self.old_data['field_prompt']
        elif '_meta' in self.old_data and isinstance(self.old_data['_meta'], dict) and 'field_prompt' in self.old_data['_meta']:
            self.data['_meta']['field_prompt'] = self.old_data['_meta']['field_prompt']
        
        # Process each key from raw data
        for key, new_value in self.new_raw_data.items():
            # Check both regular key and _meta section for existing data
            if key in self.old_data and isinstance(self.old_data[key], dict):
                # Key exists in old data
                old_entry = self.old_data[key]
                self.data[key] = OrderedDict()
                
                # Check if raw value changed
                old_raw = old_entry.get('raw', '')
                
                if old_raw != new_value:
                    # Value changed - add 'new' field
                    # Copy all existing fields except old 'new' field
                    temp_entry = OrderedDict()
                    for field, value in old_entry.items():
                        if field != 'new':
                            temp_entry[field] = value
                    
                    # Add 'new' field to indicate retranslation needed
                    temp_entry['new'] = new_value
                    
                    # Ensure status field exists (keep existing or set to "normal")
                    if 'status' not in temp_entry:
                        temp_entry['status'] = 'normal'
                    
                    # Reorder fields: raw, new, status, language codes
                    self.data[key] = reorder_entry_fields(temp_entry)
                    
                    self.logger.info(f"Updated key '{key}': value changed from '{old_raw}' to '{new_value}'")
                else:
                    # Value unchanged - keep as-is, but ensure status and reorder fields
                    temp_entry = old_entry.copy()
                    if 'status' not in temp_entry:
                        temp_entry['status'] = 'normal'
                    self.data[key] = reorder_entry_fields(temp_entry)
            else:
                # New key - create with 'new' field and status
                self.data[key] = OrderedDict()
                self.data[key]['new'] = new_value
                self.data[key]['status'] = 'normal'
                self.logger.info(f"New key '{key}' added with value '{new_value}'")
        
        # Preserve keys from old data that are not in new raw data
        # Set status field based on whether key was from older version
        for key in self.old_data:
            if key not in ['name', 'field_prompt', '_meta'] and key not in self.data:
                old_entry = self.old_data[key]
                if isinstance(old_entry, dict):
                    # Check if this key already has status "old" (from older version)
                    if old_entry.get('status') != 'old':
                        # This key was in the latest version but no longer exists in raw data
                        # Set status to "abandoned"
                        entry_copy = OrderedDict(old_entry)
                        entry_copy['status'] = 'abandoned'
                        self.data[key] = reorder_entry_fields(entry_copy)
                        self.logger.info(f"Key '{key}' status: abandoned (no longer in raw data)")
                    else:
                        # This key was from an older version, keep as-is with status "old"
                        self.data[key] = reorder_entry_fields(old_entry)
                        self.logger.debug(f"Preserved old key '{key}' from older version (status: old)")
                else:
                    self.data[key] = old_entry
                    self.logger.debug(f"Preserved key '{key}' (not in new raw data)")
