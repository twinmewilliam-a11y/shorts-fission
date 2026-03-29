#!/usr/bin/env python3
"""
Shorts-Fission 缓存清理 Hook

集成到变体生成流程中，自动清理过期的 PNG 序列。

使用方式：
1. 在 Celery 任务中调用（推荐）
2. 添加到定时任务（cron）
"""

import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional
from loguru import logger


class CacheCleanupHook:
    """缓存清理 Hook"""
    
    def __init__(
        self,
        project_root: str = None,
        max_cache_age_hours: int = 24,
        max_cache_size_mb: int = 500,
        enabled: bool = True,
    ):
        self.enabled = enabled
        self.max_age = timedelta(hours=max_cache_age_hours)
        self.max_size_mb = max_cache_size_mb
        
        # 项目根目录
        if project_root:
            self.project_root = Path(project_root)
        else:
            # 自动检测
            self.project_root = Path(__file__).parent.parent
        
        # 缓存目录
        self.remotion_out = self.project_root / 'remotion-caption' / 'out'
    
    def after_variant_generated(self, video_id: int, variant_id: int = None):
        """
        变体生成后清理 Hook
        
        在每个变体生成完成后调用，自动清理过期的 PNG 序列。
        
        Args:
            video_id: 视频ID
            variant_id: 变体ID（可选）
        """
        if not self.enabled:
            return
        
        try:
            # 1. 清理当前视频的 PNG 序列（如果生成完成）
            if variant_id:
                self._cleanup_video_png(video_id)
            
            # 2. 检查总缓存大小，超过限制则清理最旧的
            self._cleanup_by_size()
            
        except Exception as e:
            logger.warning(f"[CacheHook] 清理失败: {e}")
    
    def _cleanup_video_png(self, video_id: int):
        """清理指定视频的 PNG 序列"""
        png_dir = self.remotion_out / f'png_{video_id}'
        
        if not png_dir.exists():
            return
        
        try:
            size = self._get_dir_size(png_dir)
            logger.info(f"[CacheHook] 清理视频 #{video_id} 的 PNG 序列: {size/(1024*1024):.1f}MB")
            shutil.rmtree(png_dir)
        except Exception as e:
            logger.warning(f"[CacheHook] 清理 PNG 失败: {png_dir}, error={e}")
    
    def _cleanup_by_size(self):
        """按大小清理缓存（保留最新的）"""
        if not self.remotion_out.exists():
            return
        
        # 获取所有 png_* 目录
        png_dirs = [
            item for item in self.remotion_out.iterdir()
            if item.is_dir() and item.name.startswith('png_')
        ]
        
        if not png_dirs:
            return
        
        # 计算总大小
        total_size = sum(self._get_dir_size(d) for d in png_dirs)
        total_size_mb = total_size / (1024 * 1024)
        
        if total_size_mb <= self.max_size_mb:
            logger.debug(f"[CacheHook] 缓存大小正常: {total_size_mb:.1f}MB / {self.max_size_mb}MB")
            return
        
        # 按修改时间排序（最旧的在前）
        png_dirs.sort(key=lambda d: d.stat().st_mtime)
        
        # 清理最旧的，直到总大小低于限制
        cleaned_count = 0
        for png_dir in png_dirs:
            if total_size_mb <= self.max_size_mb * 0.8:  # 清理到 80%
                break
            
            try:
                size = self._get_dir_size(png_dir)
                logger.info(f"[CacheHook] 清理过期缓存: {png_dir.name} ({size/(1024*1024):.1f}MB)")
                shutil.rmtree(png_dir)
                total_size_mb -= size / (1024 * 1024)
                cleaned_count += 1
            except Exception as e:
                logger.warning(f"[CacheHook] 清理失败: {png_dir}, error={e}")
        
        if cleaned_count > 0:
            logger.info(f"[CacheHook] 清理完成: 删除 {cleaned_count} 个目录，剩余 {total_size_mb:.1f}MB")
    
    def _get_dir_size(self, dir_path: Path) -> int:
        """获取目录大小（字节）"""
        total = 0
        try:
            for item in dir_path.rglob('*'):
                if item.is_file():
                    total += item.stat().st_size
        except:
            pass
        return total


# 全局实例
_cache_hook: Optional[CacheCleanupHook] = None


def get_cache_hook(
    project_root: str = None,
    max_cache_age_hours: int = 24,
    max_cache_size_mb: int = 500,
    enabled: bool = True,
) -> CacheCleanupHook:
    """获取缓存清理 Hook 实例"""
    global _cache_hook
    
    if _cache_hook is None:
        _cache_hook = CacheCleanupHook(
            project_root=project_root,
            max_cache_age_hours=max_cache_age_hours,
            max_cache_size_mb=max_cache_size_mb,
            enabled=enabled,
        )
    
    return _cache_hook


# 便捷函数
def cleanup_after_variant(video_id: int, variant_id: int = None):
    """变体生成后清理缓存的便捷函数"""
    hook = get_cache_hook()
    hook.after_variant_generated(video_id, variant_id)
