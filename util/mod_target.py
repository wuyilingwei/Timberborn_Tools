"""
ModTarget class for managing mod translations across multiple versions
"""
import os
import logging
from typing import Dict, List, Optional, Tuple
from .file import CSV_File

logger = logging.getLogger(__name__)

class ModTarget:
    """管理单个mod的多个版本翻译"""
    
    def __init__(self, mod_id: str, mod_name: str, mod_path: str, target_lang: str, translator):
        self.mod_id = mod_id
        self.mod_name = mod_name
        self.mod_path = mod_path
        self.target_lang = target_lang
        self.translator = translator
        self.versions: Dict[str, CSV_File] = {}
        self.version_priority: List[str] = []
        
    def add_version(self, version: str, raw_file_path: str) -> bool:
        """添加版本和对应的原始文件"""
        try:
            csv_file = CSV_File(
                id=self.mod_id,
                name=self.mod_name,
                raw=raw_file_path,
                target=self.target_lang,
                translator=self.translator
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
    
    def cross_version_copy(self):
        """跨版本复制相同的键值对"""
        if len(self.versions) <= 1:
            return
            
        # 按优先级遍历版本
        for i, source_version in enumerate(self.version_priority):
            if source_version not in self.versions:
                continue
                
            source_file = self.versions[source_version]
            source_data = source_file.get_translation_data()
            
            # 向优先级较低的版本复制
            for target_version in self.version_priority[i+1:]:
                if target_version not in self.versions:
                    continue
                    
                target_file = self.versions[target_version]
                target_raw_data = target_file.get_raw_data()
                
                copied_count = 0
                for key, source_info in source_data.items():
                    if key in target_raw_data:
                        target_raw = target_raw_data[key]
                        source_raw = source_info.get('raw', '')
                        
                        # 如果原始文本相同且目标版本没有翻译
                        if (target_raw == source_raw and 
                            not target_file.has_translation(key)):
                            target_file.copy_translation(key, source_info)
                            copied_count += 1
                
                if copied_count > 0:
                    logger.info(f"Copied {copied_count} translations from {source_version} to {target_version} for mod {self.mod_id}")
    
    def translate_all(self):
        """翻译所有版本，使用增强的上下文信息"""
        for version in self.version_priority:
            if version not in self.versions:
                continue
                
            csv_file = self.versions[version]
            logger.info(f"Translating mod {self.mod_id} version {version}")
            
            # 获取辅助翻译信息
            auxiliary_info = self._get_auxiliary_translation_info(version)
            csv_file.translate_with_context(auxiliary_info)
    
    def _get_auxiliary_translation_info(self, current_version: str) -> Dict:
        """获取辅助翻译信息（其他版本的翻译结果）"""
        auxiliary_info = {}
        
        for version in self.version_priority:
            if version == current_version or version not in self.versions:
                continue
                
            other_file = self.versions[version]
            other_data = other_file.get_translation_data()
            
            for key, translation_info in other_data.items():
                if key not in auxiliary_info:
                    auxiliary_info[key] = []
                auxiliary_info[key].append({
                    'version': version,
                    'raw': translation_info.get('raw', ''),
                    'translation': translation_info.get('translation', ''),
                    'auxiliary_lang': translation_info.get('auxiliary_lang', '')
                })
        
        return auxiliary_info
    
    def save_all_data(self, data_path: str):
        """保存所有版本的数据"""
        for version, csv_file in self.versions.items():
            csv_file.save_data(data_path, f"{self.mod_id}_{version}")
            logger.info(f"Saved data for mod {self.mod_id} version {version}")
    
    def has_valid_versions(self) -> bool:
        """检查是否有有效的版本"""
        return len(self.versions) > 0
