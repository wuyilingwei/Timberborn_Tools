"""
ModTarget class for managing mod data updates across multiple versions (v3)
No translation - only data preparation with change detection
"""
import os
import logging
from typing import Dict, List, Tuple
from .file import CSV_File

logger = logging.getLogger(__name__)

class ModTarget:
    """管理单个mod的多个版本数据更新"""
    
    def __init__(self, mod_id: str, mod_name: str, mod_path: str):
        self.mod_id = mod_id
        self.mod_name = mod_name
        self.mod_path = mod_path
        self.versions: Dict[str, CSV_File] = {}
        self.version_priority: List[str] = []
        
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
            return tuple(map(int, version.split('.')))
        except:
            return (0,)
    
    def load_old_data(self, data_path: str):
        """加载所有版本的历史数据"""
        for version in self.versions:
            old_data_file = os.path.join(data_path, f"{self.mod_id}_{version}.toml")
            if os.path.exists(old_data_file):
                self.versions[version].load_old_data(old_data_file)
                logger.info(f"Loaded old data for {self.mod_id} version {version}")
    
    def update_all_data(self):
        """更新所有版本的数据 (v3: 只进行数据对比，不翻译)"""
        for version in self.version_priority:
            if version not in self.versions:
                continue
                
            csv_file = self.versions[version]
            logger.info(f"Updating data for mod {self.mod_id} version {version}")
            csv_file.update_data()
    
    def save_all_data(self, data_path: str):
        """保存所有版本的数据"""
        for version, csv_file in self.versions.items():
            csv_file.save_data(data_path, f"{self.mod_id}_{version}")
            logger.info(f"Saved data for mod {self.mod_id} version {version}")
    
    def has_valid_versions(self) -> bool:
        """检查是否有有效的版本"""
        return len(self.versions) > 0

