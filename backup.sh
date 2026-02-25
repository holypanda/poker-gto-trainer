#!/bin/bash

# ============================================
# Poker GTO Trainer 数据库备份脚本
# ============================================

BACKUP_DIR="./backups"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="poker_backup_${DATE}.sql"
RETENTION_DAYS=30

# 创建备份目录
mkdir -p $BACKUP_DIR

echo "📦 开始备份数据库..."

# 执行备份
docker-compose -f docker-compose.prod.yml exec -T db pg_dump \
    -U ${DB_USER:-poker} \
    -d ${DB_NAME:-poker_gto} \
    > "$BACKUP_DIR/$BACKUP_FILE"

# 压缩备份
gzip "$BACKUP_DIR/$BACKUP_FILE"

echo "✅ 备份完成: $BACKUP_DIR/${BACKUP_FILE}.gz"

# 清理旧备份
echo "🧹 清理 $RETENTION_DAYS 天前的备份..."
find $BACKUP_DIR -name "poker_backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "✅ 备份任务完成"
