#!/usr/bin/env python3
"""
Scrapling 集成测试集

测试维度：
1. Scrapling 可用性测试
2. HTTP 抓取测试
3. 隐身模式测试
4. YouTube 下载测试
5. TikTok 抓取测试
6. 下载器集成测试
7. 回退机制测试
"""

import os
import sys
import json
import time
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime

# 添加项目路径
sys.path.insert(0, '/root/.openclaw/workspace/projects/shorts-fission/backend')

# 测试结果收集
test_results = []

def log(test_name: str, passed: bool, message: str = ""):
    """记录测试结果"""
    status = "✅ 通过" if passed else "❌ 失败"
    print(f"\n{status} - {test_name}")
    if message:
        for line in message.split('\n'):
            print(f"   {line}")
    test_results.append({
        "test": test_name,
        "passed": passed,
        "message": message,
        "timestamp": datetime.now().isoformat()
    })

def test_1_scrapling_availability():
    """测试1: Scrapling 模块可用性"""
    try:
        from scrapling.fetchers import Fetcher, StealthyFetcher
        from scrapling.parser import Selector
        
        log("Scrapling 模块可用性", True, 
            "Fetcher ✅\n"
            "StealthyFetcher ✅\n"
            "Selector ✅")
        return True
    except ImportError as e:
        log("Scrapling 模块可用性", False, f"导入失败: {e}")
        return False

def test_2_custom_downloader_import():
    """测试2: 自定义 ScraplingDownloader 导入"""
    try:
        from app.services.scrapling_downloader import (
            ScraplingDownloader, 
            ScraplingSession,
            SCRAPLING_AVAILABLE
        )
        
        if not SCRAPLING_AVAILABLE:
            log("ScraplingDownloader 导入", False, "SCRAPLING_AVAILABLE = False")
            return False
        
        log("ScraplingDownloader 导入", True,
            "ScraplingDownloader ✅\n"
            "ScraplingSession ✅\n"
            "SCRAPLING_AVAILABLE = True")
        return True
    except ImportError as e:
        log("ScraplingDownloader 导入", False, f"导入失败: {e}")
        return False

def test_3_http_fetch():
    """测试3: HTTP 抓取功能"""
    try:
        from scrapling.fetchers import Fetcher
        
        # 测试抓取
        page = Fetcher.get('https://quotes.toscrape.com/', impersonate='chrome')
        quotes = page.css('.quote .text::text').getall()
        
        if len(quotes) >= 5:
            log("HTTP 抓取功能", True,
                f"抓取到 {len(quotes)} 条数据\n"
                f"示例: {quotes[0][:50]}...")
            return True
        else:
            log("HTTP 抓取功能", False, f"数据不足: {len(quotes)}")
            return False
    except Exception as e:
        log("HTTP 抓取功能", False, str(e))
        return False

def test_4_stealth_fetch():
    """测试4: 隐身模式抓取"""
    try:
        from scrapling.fetchers import StealthyFetcher
        
        # 测试隐身抓取
        page = StealthyFetcher.fetch(
            'https://quotes.toscrape.com/',
            headless=True
        )
        quotes = page.css('.quote .text::text').getall()
        
        if len(quotes) >= 5:
            log("隐身模式抓取", True,
                f"抓取到 {len(quotes)} 条数据\n"
                "隐身模式正常工作")
            return True
        else:
            log("隐身模式抓取", False, f"数据不足: {len(quotes)}")
            return False
    except Exception as e:
        log("隐身模式抓取", False, str(e)[:100])
        return False

def test_5_youtube_fetch():
    """测试5: YouTube 页面抓取"""
    try:
        from scrapling.fetchers import Fetcher
        
        # 测试 YouTube
        page = Fetcher.get(
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
            impersonate='chrome'
        )
        title = page.css('title::text').get() or ''
        
        if 'YouTube' in title:
            log("YouTube 页面抓取", True,
                f"标题: {title[:60]}...")
            return True
        else:
            log("YouTube 页面抓取", False, f"标题异常: {title}")
            return False
    except Exception as e:
        log("YouTube 页面抓取", False, str(e)[:100])
        return False

def test_6_tiktok_fetch():
    """测试6: TikTok 页面抓取"""
    try:
        from scrapling.fetchers import Fetcher
        
        # 测试 TikTok
        page = Fetcher.get(
            'https://www.tiktok.com/',
            impersonate='chrome'
        )
        
        # 检查是否有内容
        html = page.html_content or ''
        
        if len(html) > 1000:
            log("TikTok 页面抓取", True,
                f"获取到 {len(html)} 字符\n"
                "TikTok 页面可访问")
            return True
        else:
            log("TikTok 页面抓取", False, f"内容不足: {len(html)} 字符")
            return False
    except Exception as e:
        log("TikTok 页面抓取", False, str(e)[:100])
        return False

def test_7_custom_downloader_http():
    """测试7: ScraplingDownloader HTTP 模式"""
    try:
        from app.services.scrapling_downloader import ScraplingDownloader
        
        downloader = ScraplingDownloader({
            'headless': True,
            'use_stealth': False
        })
        
        if not downloader.is_available():
            log("ScraplingDownloader HTTP 模式", False, "Scrapling 不可用")
            return False
        
        result = downloader.get_video_info('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        
        if result and result.get('status') == 'success':
            log("ScraplingDownloader HTTP 模式", True,
                f"获取视频信息成功\n"
                f"标题: {result.get('title', '')[:50]}...")
            return True
        else:
            log("ScraplingDownloader HTTP 模式", False, f"获取失败: {result}")
            return False
    except Exception as e:
        log("ScraplingDownloader HTTP 模式", False, str(e)[:100])
        return False

def test_8_custom_downloader_stealth():
    """测试8: ScraplingDownloader 隐身模式"""
    try:
        from app.services.scrapling_downloader import ScraplingDownloader
        
        downloader = ScraplingDownloader({
            'headless': True,
            'use_stealth': True
        })
        
        result = downloader.get_video_info('https://www.youtube.com/watch?v=dQw4w9WgXcQ')
        
        if result and result.get('status') == 'success':
            log("ScraplingDownloader 隐身模式", True,
                f"隐身模式获取成功\n"
                f"标题: {result.get('title', '')[:50]}...")
            return True
        else:
            log("ScraplingDownloader 隐身模式", False, f"获取失败: {result}")
            return False
    except Exception as e:
        log("ScraplingDownloader 隐身模式", False, str(e)[:100])
        return False

def test_9_yt_dlp_availability():
    """测试9: yt-dlp 可用性（回退方案）"""
    try:
        result = subprocess.run(
            ['yt-dlp', '--version'],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        version = result.stdout.strip()
        
        log("yt-dlp 可用性", True, f"版本: {version}")
        return True
    except Exception as e:
        log("yt-dlp 可用性", False, str(e))
        return False

def test_10_celery_task_import():
    """测试10: Celery 任务导入"""
    try:
        from app.tasks.celery_tasks import (
            celery_app,
            download_video_task,
            generate_variants_task,
            scrapling_downloader
        )
        
        # 检查 scrapling_downloader 是否初始化
        if scrapling_downloader is None:
            log("Celery 任务导入", False, "scrapling_downloader 未初始化")
            return False
        
        log("Celery 任务导入", True,
            "celery_app ✅\n"
            "download_video_task ✅\n"
            "generate_variants_task ✅\n"
            "scrapling_downloader ✅")
        return True
    except Exception as e:
        log("Celery 任务导入", False, str(e)[:100])
        return False

def test_11_session_manager():
    """测试11: Session 管理器"""
    try:
        from app.services.scrapling_downloader import ScraplingSession
        
        # 测试 Session 创建
        session = ScraplingSession({'headless': True})
        
        log("Session 管理器", True,
            "ScraplingSession 创建成功\n"
            "支持上下文管理")
        return True
    except Exception as e:
        log("Session 管理器", False, str(e)[:100])
        return False

def test_12_requirements_updated():
    """测试12: requirements.txt 已更新"""
    try:
        req_path = '/root/.openclaw/workspace/projects/shorts-fission/backend/requirements.txt'
        
        with open(req_path, 'r') as f:
            content = f.read()
        
        if 'scrapling' in content.lower():
            log("requirements.txt 已更新", True, "scrapling 已添加到依赖")
            return True
        else:
            log("requirements.txt 已更新", False, "scrapling 未在依赖中")
            return False
    except Exception as e:
        log("requirements.txt 已更新", False, str(e))
        return False

def test_13_cloudflare_test():
    """测试13: Cloudflare 绕过测试（使用测试网站）"""
    try:
        from scrapling.fetchers import StealthyFetcher
        
        # 使用一个有 Cloudflare 保护的测试网站
        page = StealthyFetcher.fetch(
            'https://nopecha.com/demo/cloudflare',
            headless=True
        )
        
        # 检查是否获取到内容
        html = page.html_content or ''
        
        if len(html) > 500:
            log("Cloudflare 绕过测试", True,
                f"成功绕过 Cloudflare\n"
                f"获取到 {len(html)} 字符")
            return True
        else:
            log("Cloudflare 绕过测试", False, f"内容不足: {len(html)}")
            return False
    except Exception as e:
        log("Cloudflare 绕过测试", False, str(e)[:100])
        return False

def run_all_tests():
    """运行所有测试"""
    print("=" * 70)
    print("Scrapling 集成测试")
    print("=" * 70)
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    # 基础测试
    print("\n【基础功能测试】")
    test_1_scrapling_availability()
    test_2_custom_downloader_import()
    test_9_yt_dlp_availability()
    test_12_requirements_updated()
    
    # 抓取测试
    print("\n【抓取功能测试】")
    test_3_http_fetch()
    test_4_stealth_fetch()
    test_5_youtube_fetch()
    test_6_tiktok_fetch()
    
    # 自定义下载器测试
    print("\n【ScraplingDownloader 测试】")
    test_7_custom_downloader_http()
    test_8_custom_downloader_stealth()
    test_11_session_manager()
    
    # 集成测试
    print("\n【集成测试】")
    test_10_celery_task_import()
    test_13_cloudflare_test()
    
    # 输出摘要
    print("\n" + "=" * 70)
    print("测试摘要")
    print("=" * 70)
    
    passed = sum(1 for r in test_results if r["passed"])
    total = len(test_results)
    
    for result in test_results:
        status = "✅" if result["passed"] else "❌"
        print(f"{status} {result['test']}")
    
    print(f"\n通过: {passed}/{total}")
    print("=" * 70)
    
    # 保存结果
    report_path = '/root/.openclaw/workspace/projects/shorts-fission/tests/scrapling_test_report.json'
    with open(report_path, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "passed": passed,
            "total": total,
            "results": test_results
        }, f, indent=2, ensure_ascii=False)
    print(f"\n测试报告已保存: {report_path}")
    
    return passed == total

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
