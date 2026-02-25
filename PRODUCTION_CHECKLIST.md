# Poker GTO Trainer V1.0 生产部署检查清单

## ✅ 部署前检查

### 1. 服务器配置
- [ ] 2GB+ RAM
- [ ] 2+ CPU 核心
- [ ] 20GB+ 磁盘空间
- [ ] Ubuntu 20.04+ / CentOS 8+

### 2. 域名与 SSL
- [ ] 已购买域名
- [ ] 已配置 DNS 解析
- [ ] 已准备 SSL 证书 (Let's Encrypt 或商业证书)

### 3. 安全配置
- [ ] 修改 `SECRET_KEY` (至少 32 位随机字符串)
- [ ] 修改数据库密码
- [ ] 配置防火墙 (仅开放 80/443)
- [ ] 配置 CORS 白名单

### 4. 支付配置
- [ ] 支付宝应用已创建
- [ ] APP ID 已配置
- [ ] RSA2 密钥对已生成
- [ ] 公钥已上传到支付宝
- [ ] 支付回调 URL 已配置

## 🚀 部署步骤

### 第一步: 环境准备
```bash
# 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 第二步: 项目部署
```bash
# 克隆项目
git clone <your-repo> poker-gto-trainer
cd poker-gto-trainer

# 配置环境
cp .env.example .env
nano .env  # 编辑配置

# 执行部署
./deploy.sh
```

### 第三步: SSL 配置 (Let's Encrypt)
```bash
# 安装 certbot
sudo apt install certbot

# 生成证书
sudo certbot certonly --standalone -d your-domain.com

# 复制证书
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem nginx/ssl/cert.pem
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem nginx/ssl/key.pem

# 重启 nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### 第四步: 自动续期
```bash
# 添加定时任务
sudo crontab -e

# 添加以下内容 (每月 1 日续期)
0 0 1 * * certbot renew --quiet && cp /etc/letsencrypt/live/your-domain.com/*.pem /path/to/poker-gto-trainer/nginx/ssl/ && docker-compose -f /path/to/poker-gto-trainer/docker-compose.prod.yml restart nginx
```

### 第五步: 自动备份
```bash
# 添加定时任务
sudo crontab -e

# 每天凌晨 3 点备份
0 3 * * * cd /path/to/poker-gto-trainer && ./backup.sh
```

## 🔍 部署后验证

### 功能测试
- [ ] 用户注册/登录
- [ ] 开始训练
- [ ] 提交答案
- [ ] 查看统计
- [ ] 支付宝支付 (测试 0.01 元)

### 性能测试
```bash
# 健康检查
curl https://your-domain.com/health

# 压力测试 (安装 wrk)
wrk -t4 -c100 -d30s https://your-domain.com/api/v1/health
```

### 安全检查
- [ ] HTTPS 强制跳转
- [ ] 安全响应头检查
- [ ] 数据库不暴露公网
- [ ] Redis 不暴露公网

## 📊 监控设置

### 基础监控
```bash
# 查看容器状态
docker-compose -f docker-compose.prod.yml ps

# 查看资源使用
docker stats

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

### 推荐第三方监控
- **Uptime**: https://uptime.com (网站可用性)
- **Sentry**: https://sentry.io (错误追踪)
- **Grafana + Prometheus**: 性能监控

## 🆘 应急方案

### 服务宕机
```bash
# 重启所有服务
docker-compose -f docker-compose.prod.yml restart

# 如果不行，重新部署
./deploy.sh
```

### 数据库恢复
```bash
# 从备份恢复
gunzip backups/poker_backup_YYYYMMDD_HHMMSS.sql.gz
docker-compose -f docker-compose.prod.yml exec -T db psql -U poker -d poker_gto < backups/poker_backup_YYYYMMDD_HHMMSS.sql
```

## 📞 联系方式

遇到问题？
- 提交 Issue: https://github.com/yourusername/poker-gto-trainer/issues
- 邮箱: support@poker-gto-trainer.com

---

**祝部署顺利！🎉**
