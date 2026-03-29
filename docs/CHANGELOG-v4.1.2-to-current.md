# Shorts-Fission 版本更新记录

## v4.1.2 → 当前版本 (2026-03-29)

---

## 🎨 前端 UI/UX 优化

### 深色主题 (2026-03-29)
- **主色**: #EC4899 (视频粉)
- **强调色**: #2563EB (时间线蓝)
- **背景**: #0F172A (深色 OLED)
- **卡片**: #192134
- **字体**: Plus Jakarta Sans
- **图标**: Lucide React (SVG)

### 修改文件
- `tailwind.config.js` - 深色主题配色
- `src/index.css` - CSS 变量 + 动画
- `src/App.tsx` - 深色导航栏 + SVG 图标
- `src/pages/Dashboard.tsx` - 深色仪表盘
- `src/pages/Videos.tsx` - 批量操作功能
- `src/pages/Downloads.tsx` - 深色下载页
- `src/components/VideoCard.tsx` - 深色卡片 + 编号
- `src/components/VideoUploader.tsx` - 深色拖拽区
- `src/components/Toast.tsx` - 深色通知

---

## 🆕 新增功能

### 1. 视频编号显示
- 左上角显示编号（#022, #023...）
- **编号来源**: 数据库 ID（`video.id`）
- **与下载一致**: 前端 #022 = 后端 `/variants/22/download`

### 2. 批量操作功能
- **批量选择模式**: 点击进入选择模式
- **全选/取消全选**: 一键操作
- **批量下载**: 逐个下载每个视频的 ZIP
- **批量删除**: 带确认弹窗

### 3. 下载功能优化
- **单个视频下载**: 不打开新页面
- **单个变体下载**: 修复跨域问题
- **批量下载**: 2 秒延迟间隔

---

## 🐛 Bug 修复

### 跨域下载问题
**问题**: `net::ERR_FAILED 200 (OK)` - 浏览器无法处理跨域响应流

**尝试方案**:
1. ❌ `fetch` + `blob` → CORS 错误
2. ❌ `window.open()` → 打开新页面
3. ❌ `<a>` 标签无延迟 → 只触发第一个下载
4. ❌ `iframe` → 不触发任何下载
5. ✅ **`<a>` 标签 + 2 秒延迟** → 成功

**修复文件**:
- `Videos.tsx` - handleDownloadVariants, handleBatchDownload
- `VideoDetailModal.tsx` - handleDownloadVariant
- `variants.py` - 添加 `FileResponse` 导入

### 后端错误
- **问题**: `FileResponse` 未导入导致 500 错误
- **修复**: 在 `variants.py` 添加 `from fastapi.responses import FileResponse`

---

## 🔧 后端优化

### 新增 API
- `POST /api/variants/batch-download` - 批量下载
- `POST /api/videos/batch-delete` - 批量删除

### 批量删除逻辑
1. 删除数据库中的视频记录
2. 删除关联的变体记录
3. 删除对应的存储文件夹（源视频 + 变体）

---

## 🧹 缓存清理方案

### 新增文件
- `scripts/cleanup_cache.py` - 定时清理脚本
- `backend/app/hooks/cache_cleanup.py` - 自动清理 Hook

### 清理策略
| 类型 | 触发条件 | 清理目标 |
|------|---------|---------|
| 即时清理 | 变体生成完成 | 当前视频的 PNG 序列 |
| 定时清理 | 每天凌晨 3:00 | 超过 24 小时的所有缓存 |
| 大小清理 | 缓存 > 500 MB | 清理最旧的直到 80% |

### Cron 配置
```bash
0 3 * * * cd /root/.openclaw/workspace/projects/shorts-fission && python3 scripts/cleanup_cache.py --max-age-hours 24
```

---

## 📝 文档更新

| 文档 | 说明 |
|------|------|
| `docs/UI-UX-OPTIMIZATION.md` | UI/UX 优化文档 |
| `docs/CACHE-CLEANUP.md` | 缓存清理文档 |

---

## 📊 代码统计

| 类型 | 文件数 | 变更 |
|------|--------|------|
| 前端修改 | 9 | UI/UX + 新功能 |
| 后端修改 | 2 | API + 修复 |
| 新增脚本 | 2 | 缓存清理 |
| 文档更新 | 2 | 功能文档 |

---

## 🔗 相关文档

- [UI/UX 优化文档](./UI-UX-OPTIMIZATION.md)
- [缓存清理文档](./CACHE-CLEANUP.md)
- [Animated Caption v4.1](./Animated_Caption_v4.1_Documentation.md)
- [PIP 变体引擎 v4.0](./TikTok_Visual_Dedup_v4.0_PIP.md)

---

*最后更新: 2026-03-29*
