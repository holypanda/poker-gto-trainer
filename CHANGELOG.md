# 更新日志

所有重要更新都会记录在此文件。

## [1.0.0] - 2024-01-01

### 🎉 首个正式版本

### 新增
- 完整的 6max 翻前 GTO 训练系统
- 支持 50bb 和 100bb 筹码深度
- 6个位置: UTG, MP, CO, BTN, SB, BB
- 多种训练场景: 开牌、面对加注、面对 3bet、面对 All-in
- 实时 GTO 频率可视化
- 详细的统计分析系统
- 位置分析、手牌类型分析、每日趋势
- 支付宝订阅支付 (1元/月)
- 免费用户每日 20 次训练限制
- JWT Token 认证系统
- 响应式 Web 设计
- Docker 容器化部署
- Nginx 反向代理
- 生产环境一键部署脚本
- 自动数据库备份

### 技术栈
- 后端: FastAPI + SQLAlchemy + PostgreSQL + Redis
- 前端: React 18 + TypeScript + Tailwind CSS + Zustand
- 支付: 支付宝 SDK
- 部署: Docker + Docker Compose + Nginx

### 安全特性
- bcrypt 密码加密
- JWT Token 认证
- CORS 跨域限制
- 安全响应头
- SQL 注入防护

---

## 版本格式说明

版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/):

- **MAJOR**: 不兼容的 API 修改
- **MINOR**: 向下兼容的功能新增
- **PATCH**: 向下兼容的问题修复

格式: `[MAJOR.MINOR.PATCH]`
