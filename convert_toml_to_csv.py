#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import toml
import csv
import shutil
import sys

def convert_toml_to_csv(data_dir, mod_dir):
    """将TOML文件转换为CSV文件"""
    
    # 第一阶段：处理所有 TOML 文件（包括 default）
    default_files = {}  # 存储 default 版本的文件信息

    for file_name in os.listdir(data_dir):
        if file_name.endswith(".toml"):
            # 提取 mod_id 和 version
            if "_default.toml" in file_name:
                # 处理 default 版本
                mod_id = file_name.replace("_default.toml", "")
                version = "default"
            else:
                match = re.search(r"(\d+)_version-(.+)\.toml", file_name)
                if not match:
                    print(f"Skipping file {file_name}: does not match expected pattern")
                    continue
                mod_id, version = match.groups()
            
            version_folder = f"version-{version}" if version != "default" else "default"
            toml_path = os.path.join(data_dir, file_name)
            output_dir = os.path.join(mod_dir, version_folder, "Localizations")
            os.makedirs(output_dir, exist_ok=True)

            # 读取 TOML 文件
            try:
                with open(toml_path, "r", encoding="utf-8") as toml_file:
                    data = toml.load(toml_file)
                
                # 收集所有语言代码
                all_languages = set()
                for key, translations in data.items():
                    if isinstance(translations, dict):
                        for lang_code in translations.keys():
                            if lang_code != "raw":
                                all_languages.add(lang_code)
                
                # 为每种语言生成 CSV 文件
                generated_files = []
                for lang_code in all_languages:
                    csv_file_name = f"{lang_code}_{mod_id}.csv"
                    csv_path = os.path.join(output_dir, csv_file_name)
                    
                    empty_entries_count = 0
                    
                    with open(csv_path, "w", encoding="utf-8", newline="") as csv_file:
                        writer = csv.writer(csv_file)
                        writer.writerow(["ID", "Text", "Comment"])
                        
                        # 遍历所有翻译条目
                        for translation_key, translations in data.items():
                            if isinstance(translations, dict) and lang_code in translations:
                                translation_text = translations[lang_code]
                                # 检查空字符串并输出警告
                                if not translation_text or not translation_text.strip():
                                    empty_entries_count += 1
                                    print(f"[Warning] Empty translation for key '{translation_key}' in language '{lang_code}' (file: {file_name})")
                                else:
                                    writer.writerow([translation_key, translation_text, "-"])
                    
                    if empty_entries_count > 0:
                        print(f"[Info] Skipped {empty_entries_count} empty entries for {lang_code} in {file_name}")
                    
                    generated_files.append((csv_file_name, csv_path))
                
                # 如果是 default 版本，记录生成的文件
                if version == "default":
                    default_files[mod_id] = {
                        'output_dir': output_dir,
                        'files': generated_files
                    }
                    
            except Exception as e:
                print(f"[ERROR] Failed to process {toml_path}: {e}")

    # 第二阶段：将 default 文件复制到其他版本文件夹
    if default_files:
        version_dirs = [d for d in os.listdir(mod_dir) if d.startswith("version-") and os.path.isdir(os.path.join(mod_dir, d))]
        
        for mod_id, default_info in default_files.items():
            for version_dir in version_dirs:
                target_localization_dir = os.path.join(mod_dir, version_dir, "Localizations")
                os.makedirs(target_localization_dir, exist_ok=True)
                
                for csv_file_name, source_path in default_info['files']:
                    target_path = os.path.join(target_localization_dir, csv_file_name)
                    
                    # 只在目标文件不存在时复制
                    if not os.path.exists(target_path):
                        shutil.copy2(source_path, target_path)

    # 删除 default 目录
    default_dir = os.path.join(mod_dir, "default")
    if os.path.exists(default_dir):
        print(f"Removing default directory: {default_dir}")
        shutil.rmtree(default_dir)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: convert_toml_to_csv.py <data_dir> <mod_dir>")
        sys.exit(1)
    
    data_dir = sys.argv[1]
    mod_dir = sys.argv[2]
    
    convert_toml_to_csv(data_dir, mod_dir)
