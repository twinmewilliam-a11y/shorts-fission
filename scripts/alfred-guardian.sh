#!/bin/bash
# Alfred Guardian - Shorts-Fission 服务监控脚本
# 每5分钟执行一次

PROJECT_DIR="/root/.openclaw/workspace/projects/shorts-fission"
LOG_FILE="$PROJECT_DIR/logs/alfred-guardian.log"
DATE=$(date '+%Y-%m-%d %H:%M:%S')

# 创建日志目录
mkdir -p "$PROJECT_DIR/logs"

log() {
    echo "[$DATE] $1" >> "$LOG_FILE"
}

log "=== Alfred Guardian 开始健康检查 ==="

# 1. 检查后端 API
BACKEND_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/videos 2>/dev/null)
if [ "$BACKEND_OK" != "200" ]; then
    log "⚠️ 后端无响应 (HTTP $BACKEND_OK)，尝试重启..."
    pkill -f "uvicorn app.main:app" 2>/dev/null
    sleep 2
    cd "$PROJECT_DIR/backend" && source venv/bin/activate
    nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$PROJECT_DIR/backend.log" 2>&1 &
    sleep 5
    BACKEND_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/videos 2>/dev/null)
    if [ "$BACKEND_OK" = "200" ]; then
        log "✅ 后端重启成功"
    else
        log "❌ 后端重启失败"
    fi
else
    log "✅ 后端正常 (HTTP 200)"
fi

# 2. 检查 Celery Workers
CELERY_COUNT=$(ps aux | grep "celery.*celery_tasks" | grep -v grep | wc -l)
if [ "$CELERY_COUNT" -lt 2 ]; then
    log "⚠️ Celery Workers 不足 ($CELERY_COUNT)，尝试重启..."
    pkill -f "celery.*celery_tasks" 2>/dev/null
    sleep 2
    cd "$PROJECT_DIR/backend" && source venv/bin/activate
    nohup celery -A app.tasks.celery_tasks worker --loglevel=info > "$PROJECT_DIR/celery.log" 2>&1 &
    sleep 5
    CELERY_COUNT=$(ps aux | grep "celery.*celery_tasks" | grep -v grep | wc -l)
    if [ "$CELERY_COUNT" -ge 2 ]; then
        log "✅ Celery 重启成功 ($CELERY_COUNT workers)"
    else
        log "❌ Celery 重启失败"
    fi
else
    log "✅ Celery 正常 ($CELERY_COUNT workers)"
fi

# 3. 检查前端
FRONTEND_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null)
if [ "$FRONTEND_OK" != "200" ]; then
    log "⚠️ 前端无响应 (HTTP $FRONTEND_OK)，尝试重启..."
    pkill -f "vite" 2>/dev/null
    sleep 2
    cd "$PROJECT_DIR/frontend"
    nohup npm run dev > "$PROJECT_DIR/frontend.log" 2>&1 &
    sleep 5
    FRONTEND_OK=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 2>/dev/null)
    if [ "$FRONTEND_OK" = "200" ]; then
        log "✅ 前端重启成功"
    else
        log "❌ 前端重启失败"
    fi
else
    log "✅ 前端正常 (HTTP 200)"
fi

# 4. 修复数据库状态（小写转大写）
cd "$PROJECT_DIR"
LOWERCASE_COUNT=$(sqlite3 data/shorts_fission.db "SELECT COUNT(*) FROM videos WHERE status IN ('completed', 'processing', 'pending', 'downloading', 'downloaded', 'failed');" 2>/dev/null)
if [ "$LOWERCASE_COUNT" -gt 0 ]; then
    log "⚠️ 发现 $LOWERCASE_COUNT 条小写状态记录，正在修复..."
    sqlite3 data/shorts_fission.db "UPDATE videos SET status='COMPLETED' WHERE status='completed';"
    sqlite3 data/shorts_fission.db "UPDATE videos SET status='PROCESSING' WHERE status='processing';"
    sqlite3 data/shorts_fission.db "UPDATE videos SET status='PENDING' WHERE status='pending';"
    sqlite3 data/shorts_fission.db "UPDATE videos SET status='DOWNLOADING' WHERE status='downloading';"
    sqlite3 data/shorts_fission.db "UPDATE videos SET status='DOWNLOADED' WHERE status='downloaded';"
    sqlite3 data/shorts_fission.db "UPDATE videos SET status='FAILED' WHERE status='failed';"
    log "✅ 数据库状态已修复"
fi

# 5. 检查正在处理的任务
PROCESSING_COUNT=$(sqlite3 data/shorts_fission.db "SELECT COUNT(*) FROM videos WHERE status='PROCESSING';" 2>/dev/null)
if [ "$PROCESSING_COUNT" -gt 0 ]; then
    log "📊 当前有 $PROCESSING_COUNT 个任务正在处理中"
    # 列出处理超过30分钟的任务（可能卡住）
    STUCK_COUNT=$(sqlite3 data/shorts_fission.db "SELECT COUNT(*) FROM videos WHERE status='PROCESSING' AND updated_at < datetime('now', '-30 minutes');" 2>/dev/null)
    if [ "$STUCK_COUNT" -gt 0 ]; then
        log "⚠️ 发现 $STUCK_COUNT 个可能卡住的任务（超过30分钟）"
    fi
fi

log "=== Alfred Guardian 健康检查完成 ==="
echo "" >> "$LOG_FILE"
