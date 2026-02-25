#!/bin/bash

# ============================================
# Poker GTO Trainer V1.0 生产部署脚本
# ============================================

set -e  # 遇到错误立即退出

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Poker GTO Trainer V1.0 生产部署${NC}"
echo "=========================================="

# 检查环境
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Docker Compose 未安装${NC}"
    exit 1
fi

# 检查 .env 文件
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env 文件不存在，从 .env.example 创建${NC}"
    cp .env.example .env
    echo -e "${RED}❌ 请先编辑 .env 文件配置必要参数${NC}"
    exit 1
fi

# 加载环境变量
export $(grep -v '^#' .env | xargs)

# 检查必要配置
if [ "$SECRET_KEY" = "your-super-secret-key-min-32-characters-long" ]; then
    echo -e "${RED}❌ 请修改 SECRET_KEY 配置${NC}"
    exit 1
fi

if [ "$DB_PASSWORD" = "your_secure_password_here" ]; then
    echo -e "${RED}❌ 请修改数据库密码${NC}"
    exit 1
fi

echo -e "${GREEN}✅ 环境检查通过${NC}"

# 创建必要目录
mkdir -p postgres_data redis_data nginx/ssl

# 拉取最新代码 (如果是 git 仓库)
if [ -d .git ]; then
    echo -e "${YELLOW}📦 拉取最新代码...${NC}"
    git pull origin main || true
fi

# 停止旧服务
echo -e "${YELLOW}🛑 停止旧服务...${NC}"
docker-compose -f docker-compose.prod.yml down --remove-orphans || true

# 清理旧镜像 (可选)
read -p "是否清理旧镜像? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}🧹 清理旧镜像...${NC}"
    docker system prune -f
fi

# 构建并启动
echo -e "${YELLOW}🏗️  构建服务...${NC}"
docker-compose -f docker-compose.prod.yml build --no-cache

echo -e "${YELLOW}🚀 启动服务...${NC}"
docker-compose -f docker-compose.prod.yml up -d

# 等待服务启动
echo -e "${YELLOW}⏳ 等待服务启动...${NC}"
sleep 10

# 健康检查
echo -e "${YELLOW}🏥 健康检查...${NC}"
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 服务运行正常${NC}"
else
    echo -e "${RED}❌ 健康检查失败${NC}"
    echo "查看日志: docker-compose -f docker-compose.prod.yml logs"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 部署成功!${NC}"
echo "=========================================="
echo "📱 访问地址:"
echo "   - 网站: http://localhost"
echo "   - API: http://localhost/api"
echo "   - 健康: http://localhost/health"
echo ""
echo "📋 常用命令:"
echo "   查看日志: docker-compose -f docker-compose.prod.yml logs -f"
echo "   停止服务: docker-compose -f docker-compose.prod.yml down"
echo "   重启服务: docker-compose -f docker-compose.prod.yml restart"
echo "   查看状态: docker-compose -f docker-compose.prod.yml ps"
echo ""
echo -e "${YELLOW}⚠️  生产环境建议:${NC}"
echo "   1. 配置 HTTPS (SSL 证书)"
echo "   2. 配置域名解析"
echo "   3. 配置防火墙规则"
echo "   4. 定期备份数据库"
echo ""
