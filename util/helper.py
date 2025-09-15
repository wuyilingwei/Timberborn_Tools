"""
version: 1.0.0
author: Wuyilingwei
This module provides helper functions
"""
import os
import logging
from util.translator import *
def search_versions(path: str) -> list[str]:
    """
    Search for all versions in the given path
    Returns a list of version names
    'default' is key if no version found
    """
    logger = logging.getLogger(__name__)
    versions = []
    if not os.path.exists(path):
        logger.error(f"Path {path} does not exist")
        return versions
    for item in os.listdir(path):
        item_path = os.path.join(path, item)
        if os.path.isdir(item_path) and item.startswith('version-'):
            versions.append(item)
    logger.debug(f"Found versions: {versions}")
    if versions == []:
        logger.warning(f"No versions found in {path}")
        versions.append('default')
    versions.sort()
    return versions

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