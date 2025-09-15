"""
version: 1.1.0
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

    def get_translation_data(self) -> Dict:
        """获取翻译数据字典"""
        if not hasattr(self, 'data') or self.data is None:
            return {}
        
        translation_data = {}
        for key, item in self.data.items():
            if isinstance(item, dict):
                translation_data[key] = {
                    'raw': item.get('raw', ''),
                    'translation': item.get('translation', ''),
                    'auxiliary_lang': item.get('auxiliary_lang', ''),
                    'last_update': item.get('last_update', ''),
                    'status': item.get('status', 'pending')
                }
        return translation_data
    
    def get_raw_data(self) -> Dict:
        """获取原始文本数据"""
        if not hasattr(self, 'raw_data'):
            self._load_raw_data()
        return getattr(self, 'raw_data', {})
    
    def _load_raw_data(self):
        """加载原始CSV文件数据"""
        self.raw_data = {}
        try:
            import pandas as pd
            df = pd.read_csv(self.raw)
            if 'Key' in df.columns and 'Text' in df.columns:
                for _, row in df.iterrows():
                    key = str(row['Key']).strip()
                    text = str(row['Text']).strip()
                    if key and text:
                        self.raw_data[key] = text
        except Exception as e:
            logger.error(f"Failed to load raw data from {self.raw}: {e}")
    
    def has_translation(self, key: str) -> bool:
        """检查指定键是否已有翻译"""
        if not hasattr(self, 'data') or self.data is None:
            return False
        
        item = self.data.get(key, {})
        if isinstance(item, dict):
            translation = item.get('translation', '').strip()
            return bool(translation)
        return False
    
    def copy_translation(self, key: str, source_info: Dict):
        """从其他版本复制翻译"""
        if not hasattr(self, 'data'):
            self.data = {}
        
        if key not in self.data:
            self.data[key] = {}
        
        # 复制翻译信息
        self.data[key]['translation'] = source_info.get('translation', '')
        self.data[key]['auxiliary_lang'] = source_info.get('auxiliary_lang', '')
        self.data[key]['status'] = 'copied'
        self.data[key]['last_update'] = source_info.get('last_update', '')
        
        # 确保原始文本信息存在
        raw_data = self.get_raw_data()
        if key in raw_data:
            self.data[key]['raw'] = raw_data[key]
    
    def translate_with_context(self, auxiliary_info: Dict):
        """使用增强上下文进行翻译"""
        if not hasattr(self, 'data'):
            self.data = {}
        
        raw_data = self.get_raw_data()
        
        for key, raw_text in raw_data.items():
            # 跳过已有翻译的项目
            if self.has_translation(key):
                continue
            
            # 跳过长度不符合要求的文本
            if not self._should_translate(raw_text):
                continue
            
            # 准备翻译上下文
            context = self._prepare_translation_context(key, raw_text, auxiliary_info)
            
            try:
                # 执行翻译
                translation_result = self.translator.translate_with_context(
                    text=raw_text,
                    context=context,
                    target_lang=self.target
                )
                
                # 保存翻译结果
                if key not in self.data:
                    self.data[key] = {}
                
                self.data[key]['raw'] = raw_text
                self.data[key]['translation'] = translation_result.get('translation', '')
                self.data[key]['auxiliary_lang'] = translation_result.get('auxiliary_lang', '')
                self.data[key]['status'] = 'translated'
                self.data[key]['last_update'] = translation_result.get('timestamp', '')
                
                logger.info(f"Translated key '{key}' for {self.name}")
                
            except Exception as e:
                logger.error(f"Failed to translate key '{key}' for {self.name}: {e}")
                if key not in self.data:
                    self.data[key] = {}
                self.data[key]['raw'] = raw_text
                self.data[key]['status'] = 'failed'
    
    def _should_translate(self, text: str) -> bool:
        """检查文本是否应该被翻译"""
        if not text or not text.strip():
            return False
        
        text_length = len(text.strip())
        min_length = getattr(self.translator, 'min_length', 0)
        max_length = getattr(self.translator, 'max_length', float('inf'))
        
        return min_length <= text_length <= max_length
    
    def _prepare_translation_context(self, key: str, raw_text: str, auxiliary_info: Dict) -> Dict:
        """准备翻译上下文信息"""
        context = {
            'key': key,
            'raw_text': raw_text,
            'mod_name': self.name,
            'previous_translations': [],
            'similar_translations': []
        }
        
        # 添加其他版本的翻译信息
        if key in auxiliary_info:
            for aux_info in auxiliary_info[key]:
                if aux_info['translation']:
                    context['previous_translations'].append({
                        'version': aux_info['version'],
                        'raw': aux_info['raw'],
                        'translation': aux_info['translation'],
                        'auxiliary_lang': aux_info['auxiliary_lang']
                    })
        
        # 查找相似的翻译（基于原始文本相似度）
        for aux_key, aux_versions in auxiliary_info.items():
            if aux_key != key:
                for aux_info in aux_versions:
                    if (aux_info['raw'] and aux_info['translation'] and 
                        self._is_similar_text(raw_text, aux_info['raw'])):
                        context['similar_translations'].append({
                            'key': aux_key,
                            'raw': aux_info['raw'],
                            'translation': aux_info['translation']
                        })
        
        return context
    
    def _is_similar_text(self, text1: str, text2: str) -> bool:
        """检查两个文本是否相似"""
        if not text1 or not text2:
            return False
        
        # 简单的相似度检查：长度相近且有共同词汇
        len_diff = abs(len(text1) - len(text2))
        if len_diff > min(len(text1), len(text2)) * 0.5:
            return False
        
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        if not words1 or not words2:
            return False
        
        common_words = words1.intersection(words2)
        similarity = len(common_words) / min(len(words1), len(words2))
        
        return similarity > 0.6  # 60%相似度阈值
