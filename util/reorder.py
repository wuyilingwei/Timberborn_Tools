import time
from typing import List

def batch_download_with_delay(steamcmd_instance, game_id: str, mod_ids: List[str], batch_size: int = 5, delay_minutes: int = 5):
    """
    分批下载Steam Workshop物品，每批之间有延迟
    
    Args:
        steamcmd_instance: steamdownloader实例
        game_id: 游戏ID
        mod_ids: 要下载的mod ID列表
        batch_size: 每批下载的数量，默认5个
        delay_minutes: 批次间的延迟时间（分钟），默认5分钟
    """
    import logging
    logger = logging.getLogger("batch_download")
    
    total_mods = len(mod_ids)
    total_batches = (total_mods + batch_size - 1) // batch_size
    
    logger.info(f"开始分批下载 {total_mods} 个mod，共 {total_batches} 批，每批 {batch_size} 个")
    
    for i in range(0, total_mods, batch_size):
        batch_num = i // batch_size + 1
        batch_ids = mod_ids[i:i + batch_size]
        
        logger.info(f"正在下载第 {batch_num}/{total_batches} 批: {len(batch_ids)} 个mod")
        logger.info(f"批次mod IDs: {', '.join(batch_ids)}")
        
        # 下载当前批次
        steamcmd_instance.download(game_id, batch_ids)
        
        # 如果不是最后一批，等待指定时间
        if i + batch_size < total_mods:
            logger.info(f"批次 {batch_num} 完成，等待 {delay_minutes} 分钟后继续...")
            time.sleep(delay_minutes * 60)
        else:
            logger.info(f"最后一批 {batch_num} 完成，下载结束")


def reorder_toml_sections(toml_text: str) -> str:
    """
    重新排序TOML文件的sections，确保_meta始终在最前面，其子项目也在前面
    基于translate_mods.py中的reorder_glossary_blocks逻辑修改
    """
    import re
    from typing import List, Tuple, Optional
    
    lines = toml_text.splitlines(keepends=True)
    if not lines:
        return toml_text

    blocks = []
    current_header = None
    current_lines: List[str] = []

    def _is_table_header(line: str) -> bool:
        stripped = line.lstrip()
        return stripped.startswith("[") and stripped.rstrip().endswith("]")

    for line in lines:
        if _is_table_header(line):
            if current_lines:
                blocks.append((current_header, current_lines))
            current_header = line.strip()
            current_lines = [line]
        else:
            current_lines.append(line)

    if current_lines:
        blocks.append((current_header, current_lines))

    # 检查是否有_meta section
    has_meta = any((h and h.strip() == "[_meta]") for h, _ in blocks)
    if not has_meta:
        return "".join("".join(block) for block in blocks)

    preamble = []
    meta_block = None
    meta_sub_blocks = []  # _meta的子section
    other_blocks = []

    for header, block_lines in blocks:
        if not header:  # 文件开头的注释或空行
            preamble.append(block_lines)
        elif header.strip() == "[_meta]":
            meta_block = block_lines
        elif header.startswith("[_meta."):
            meta_sub_blocks.append(block_lines)
        else:
            other_blocks.append(block_lines)

    if meta_block is None:
        return "".join("".join(block) for block in blocks)

    # 在meta子块和其他块之间添加空行（如果需要）
    if meta_sub_blocks and other_blocks:
        # 检查最后一个meta子块是否以空行结尾
        last_meta_sub_block = meta_sub_blocks[-1]
        if last_meta_sub_block and not last_meta_sub_block[-1].strip():
            pass  # 已有空行
        else:
            # 添加空行
            meta_sub_blocks[-1] = meta_sub_blocks[-1] + ["\n"]

    # 重新排序：前言 + _meta + _meta子sections + 其他blocks
    ordered_blocks = preamble + [meta_block] + meta_sub_blocks + other_blocks
    return "".join("".join(block) for block in ordered_blocks)