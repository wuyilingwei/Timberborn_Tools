"""
ModTarget class for managing mod data updates with single-version tracking (v3)
No translation - only data preparation with change detection
Only keeps the latest version, merging unique keys from older versions
"""
import os
import logging
import toml
from typing import Dict, List, Tuple
from collections import OrderedDict
from .file import CSV_File

logger = logging.getLogger(__name__)

class ModTarget:
    """管理单个mod的单版本数据更新，合并旧版本的独立键值对"""
    
    def __init__(self, mod_id: str, mod_name: str, mod_path: str):
        self.mod_id = mod_id
        self.mod_name = mod_name
        self.mod_path = mod_path
        self.versions: Dict[str, CSV_File] = {}
        self.version_priority: List[str] = []
        self.old_version_data: Dict[str, OrderedDict] = {}  # 存储所有旧版本数据用于合并
        
    def add_version(self, version: str, raw_file_path: str) -> bool:
        """添加版本和对应的原始文件"""
        try:
            csv_file = CSV_File(
                id=self.mod_id,
                name=self.mod_name,
                raw=raw_file_path
            )
            self.versions[version] = csv_file
            self._update_version_priority(version)
            logger.info(f"Added version {version} for mod {self.mod_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to add version {version} for mod {self.mod_id}: {e}")
            return False
    
    def _update_version_priority(self, new_version: str):
        """更新版本优先级：最高版本>最低版本>default"""
        if new_version in self.version_priority:
            return
            
        if new_version == "default":
            self.version_priority.append(new_version)
        else:
            # 按版本号排序，最高版本优先
            numeric_versions = [v for v in self.version_priority if v != "default"]
            numeric_versions.append(new_version)
            numeric_versions.sort(key=lambda x: self._parse_version(x), reverse=True)
            
            # 重建优先级列表
            self.version_priority = numeric_versions
            if "default" in [v for v in self.versions.keys()]:
                self.version_priority.append("default")
    
    def _parse_version(self, version: str) -> Tuple[int, ...]:
        """解析版本号为元组用于排序"""
        try:
            # Remove 'version-' prefix if present
            version_str = version.replace('version-', '')
            return tuple(map(int, version_str.split('.')))
        except:
            return (0,)
    
    def load_old_data(self, data_path: str):
        """加载所有版本的历史数据"""
        
        # Load single-file format (new format without version suffix)
        old_data_file = os.path.join(data_path, f"{self.mod_id}.toml")
        if os.path.exists(old_data_file):
            try:
                with open(old_data_file, 'r', encoding='utf-8') as f:
                    self.old_version_data['single'] = toml.load(f, _dict=OrderedDict)
                logger.info(f"Loaded old single-file data for {self.mod_id}")
            except Exception as e:
                logger.error(f"Error loading old single-file data: {e}")
        
        # Also load old multi-version format files for migration
        for version in self.versions:
            old_data_file = os.path.join(data_path, f"{self.mod_id}_{version}.toml")
            if os.path.exists(old_data_file):
                try:
                    with open(old_data_file, 'r', encoding='utf-8') as f:
                        self.old_version_data[version] = toml.load(f, _dict=OrderedDict)
                    logger.info(f"Loaded old data for {self.mod_id} version {version}")
                except Exception as e:
                    logger.error(f"Error loading old data for version {version}: {e}")
    
    def update_all_data(self):
        """更新数据：只使用最新版本，合并旧版本的独立键值对"""
        if not self.version_priority:
            logger.warning(f"No versions available for mod {self.mod_id}")
            return
        
        # Get the latest version
        latest_version = self.version_priority[0]
        logger.info(f"Using latest version {latest_version} for mod {self.mod_id}")
        
        if latest_version not in self.versions:
            logger.error(f"Latest version {latest_version} not found in versions")
            return
        
        latest_csv = self.versions[latest_version]
        
        # Merge old version data into latest CSV for loading
        merged_old_data = self._merge_old_version_data()
        if merged_old_data:
            latest_csv.old_data = merged_old_data
        
        # Update the latest version data
        logger.info(f"Updating data for mod {self.mod_id} with latest version {latest_version}")
        latest_csv.update_data()
        
        # Store the result back
        self.versions[latest_version] = latest_csv
    
    def _merge_old_version_data(self) -> OrderedDict:
        """合并所有旧版本数据：以最新版本为基础，添加旧版本的独立键值对"""
        merged = OrderedDict()
        
        # Start with single-file format if it exists (use OrderedDict constructor for proper copying)
        if 'single' in self.old_version_data:
            merged = OrderedDict(self.old_version_data['single'])
            logger.info(f"Base: single-file format with {len(merged)} keys")
        
        # Get the latest version's old data if it exists
        if self.version_priority:
            latest_version = self.version_priority[0]
            if latest_version in self.old_version_data:
                # Use latest version as base or merge it
                if not merged:
                    merged = OrderedDict(self.old_version_data[latest_version])
                    logger.info(f"Base: version {latest_version} with {len(merged)} keys")
                else:
                    # Merge latest version data, prioritizing it over single-file
                    for key, value in self.old_version_data[latest_version].items():
                        merged[key] = value
                    logger.info(f"Merged version {latest_version}")
        
        # Now merge unique keys from older versions (process from older to newer, so newer values overwrite)
        for version in self.version_priority[1:]:  # Skip latest version
            if version in self.old_version_data:
                old_data = self.old_version_data[version]
                added_count = 0
                
                for key, value in old_data.items():
                    # Skip meta fields
                    if key in ['name', 'field_prompt']:
                        continue
                    
                    # Only add if key doesn't exist in merged data
                    if key not in merged:
                        merged[key] = value
                        added_count += 1
                
                if added_count > 0:
                    logger.info(f"Added {added_count} unique keys from version {version}")
        
        return merged
    
    def save_all_data(self, data_path: str):
        """保存单个版本的数据（不带版本后缀）"""
        if not self.version_priority:
            logger.warning(f"No versions to save for mod {self.mod_id}")
            return
        
        # Only save the latest version as a single file
        latest_version = self.version_priority[0]
        if latest_version in self.versions:
            csv_file = self.versions[latest_version]
            csv_file.save_data(data_path, f"{self.mod_id}")
            logger.info(f"Saved data for mod {self.mod_id} (latest version: {latest_version})")
    
    def has_valid_versions(self) -> bool:
        """检查是否有有效的版本"""
        return len(self.versions) > 0

