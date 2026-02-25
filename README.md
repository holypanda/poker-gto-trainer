# Poker GTO Trainer V1.0 | 德州扑克翻前 GTO 训练模拟器

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/yourusername/poker-gto-trainer)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

一个专业的德州扑克翻前（Preflop）GTO 近似训练 Web 应用，支持 6max 桌型、50bb 和 100bb 筹码深度。

🌐 **在线演示**: https://poker-gto-trainer.com (示例)

![Screenshot](docs/screenshot.png)

## ✨ 功能特性

- 🎯 **GTO 训练**: 基于行业标准求解器的近似 GTO 翻前策略
- 📊 **详细统计**: 正确率、位置分析、手牌类型分析、每日趋势
- 🪑 **6max 支持**: 支持 UTG/MP/CO/BTN/SB/BB 所有位置
- 💰 **多筹码深度**: 支持 50bb 和 100bb
- 💎 **VIP 订阅**: 1元/月即可享受无限训练
- 🔐 **支付宝支付**: 集成支付宝订阅支付
- 📱 **H5 移动端**: PWA 支持、响应式设计、触摸优化
- 🚀 **生产就绪**: Docker 部署、SSL 支持、自动备份

## 🚀 快速开始

### 环境要求
- Docker 20.10+ 和 Docker Compose 2.0+
- 或 Python 3.11+ 和 Node.js 18+
- 2GB RAM, 1 CPU 核心

### 生产部署 (推荐)

```bash
# 1. 克隆项目
git clone https://github.com/yourusername/poker-gto-trainer.git
cd poker-gto-trainer

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置数据库密码、密钥、支付宝配置

# 3. 执行部署脚本
./deploy.sh

# 4. 访问应用
# 网站: http://your-server-ip
# API 文档: http://your-server-ip/docs
```

### 开发环境

```bash
# 启动开发环境
docker-compose up -d

# 或手动启动
# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# 前端
cd frontend
npm install
npm start
```

## 📁 项目结构

```
poker-gto-trainer/
├── backend/                    # FastAPI 后端
│   ├── app/
│   │   ├── api/               # API 路由 (auth, training, payment)
│   │   ├── core/              # 配置、安全、中间件
│   │   ├── models/            # 数据库模型
│   │   ├── schemas/           # Pydantic 模型
│   │   ├── services/          # 业务逻辑
│   │   │   ├── gto_engine.py  # GTO 策略引擎
│   │   │   └── payment_service.py
│   │   └── main.py            # 应用入口
│   ├── Dockerfile.prod        # 生产 Dockerfile
│   └── requirements.txt
├── frontend/                   # React 前端
│   ├── src/
│   │   ├── pages/             # Dashboard, Training, Stats, Subscription
│   │   ├── services/          # API 服务
│   │   └── store/             # Zustand 状态管理
│   ├── Dockerfile.prod
│   └── package.json
├── nginx/                      # Nginx 配置
│   └── nginx.conf
├── docker-compose.prod.yml     # 生产部署配置
├── deploy.sh                   # 一键部署脚本
├── backup.sh                   # 数据库备份脚本
└── README.md
```

## ⚙️ 配置说明

### 必需配置 (.env)

```env
# 数据库 (必须修改密码)
DB_PASSWORD=your_secure_password
DATABASE_URL=postgresql://poker:your_secure_password@db:5432/poker_gto

# 安全密钥 (必须修改，至少32位)
SECRET_KEY=your-super-secret-key-min-32-characters

# 支付宝 (用于订阅支付)
ALIPAY_APP_ID=your_alipay_app_id
ALIPAY_PRIVATE_KEY=-----BEGIN RSA PRIVATE KEY-----
...
-----END RSA PRIVATE KEY-----
ALIPAY_PUBLIC_KEY=-----BEGIN PUBLIC KEY-----
...
-----END PUBLIC KEY-----

# 前端 API 地址
REACT_APP_API_URL=https://your-domain.com/api
```

### 支付宝配置步骤

1. 登录 [支付宝开放平台](https://open.alipay.com/)
2. 创建网页/移动应用
3. 获取 APP ID
4. 生成 RSA2 密钥对
5. 上传公钥到支付宝
6. 将私钥和支付宝公钥填入 `.env`

## 📱 H5 移动端开发

项目已全面适配移动端 H5:

- ✅ PWA 支持 (添加到主屏幕)
- ✅ 响应式布局 (手机/平板/桌面)
- ✅ 底部导航栏 (移动端专属)
- ✅ 触摸反馈优化
- ✅ iOS/Android 刘海屏适配

查看 [H5 开发指南](./H5_GUIDE.md) 了解更多。

## 📊 GTO 策略说明

### 策略来源
本应用使用的 GTO 策略基于以下原则构建：
- **位置重要性**: BTN > CO > MP > UTG > SB > BB
- **筹码深度影响**: 浅筹码 (50bb) 倾向于更紧的范围和更多 all-in
- **行业标准**: 参考 Monker Solver 和 PioSolver 计算结果

### 场景覆盖
- ✅ 开牌 (Open)
- ✅ 面对加注 (vs Raise 2bb/2.5bb/3bb/4bb)
- ✅ 面对溜入 (vs Limp)
- ✅ 面对 3bet (vs 3bet)
- ✅ 面对 All-in (vs All-in)

注意：这是简化的近似 GTO 策略，适合训练使用。对于专业级精确策略，建议使用 PioSolver。

## 💎 定价方案

| 功能 | 免费版 | VIP (1元/月) |
|-----|-------|-------------|
| 每日训练 | 20次 | 无限 |
| 筹码深度 | 50bb/100bb | 50bb/100bb |
| GTO 策略 | 基础 | 完整 |
| 统计分析 | 基础 | 详细 |
| 历史记录 | 最近10条 | 全部 |
| 客服支持 | 社区 | 优先 |

## 🛠️ 运维命令

```bash
# 查看日志
docker-compose -f docker-compose.prod.yml logs -f

# 查看后端日志
docker-compose -f docker-compose.prod.yml logs -f backend

# 重启服务
docker-compose -f docker-compose.prod.yml restart

# 数据库备份
./backup.sh

# 更新部署
./deploy.sh

# 进入数据库
docker-compose -f docker-compose.prod.yml exec db psql -U poker -d poker_gto
```

## 🔒 安全配置

- ✅ JWT Token 认证
- ✅ 密码 bcrypt 加密
- ✅ CORS 跨域限制
- ✅ 安全响应头 (HSTS, CSP, XSS Protection)
- ✅ SQL 注入防护 (SQLAlchemy ORM)
- ✅ HTTPS 支持 (配置 SSL 证书)

## 📈 监控与日志

```bash
# 查看实时日志
docker-compose -f docker-compose.prod.yml logs -f --tail=100

# 查看性能指标
curl http://localhost/api/v1/health/detailed

# 磁盘使用情况
docker system df
```

## 🆘 故障排查

### 常见问题

**1. 服务无法启动**
```bash
# 检查端口占用
sudo lsof -i :80
sudo lsof -i :443

# 检查日志
docker-compose -f docker-compose.prod.yml logs
```

**2. 数据库连接失败**
```bash
# 检查数据库状态
docker-compose -f docker-compose.prod.yml ps

# 重启数据库
docker-compose -f docker-compose.prod.yml restart db
```

**3. 支付回调失败**
- 检查服务器防火墙是否开放 80/443 端口
- 检查支付宝配置的 notify_url 是否正确
- 查看后端日志中的支付相关错误

## 📝 更新日志

### V1.0.0 (2024-01-01)
- 🎉 首个正式版本发布
- ✅ 6max GTO 翻前训练
- ✅ 50bb/100bb 筹码深度支持
- ✅ 支付宝订阅支付
- ✅ 完整的统计系统
- ✅ Docker 生产部署

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 项目
2. 创建分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

[MIT](LICENSE) © 2024 Poker GTO Trainer

---

<p align="center">
  Made with ❤️ for poker enthusiasts
</p>
