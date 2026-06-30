# 鲤鱼 AIOS 部署方案总结

## 已完成的配置

本文档总结了 鲤鱼 AIOS 完整部署方案的所有配置文件。

### 1. Docker 容器化

**文件**: `deploy/Dockerfile`

- 多阶段构建，最小化镜像体积
- 非 root 用户运行，安全性高
- 健康检查配置
- 资源限制配置

### 2. Docker Compose 编排

**文件**: `deploy/docker-compose.yml`

**服务列表**:
| 服务 | 端口 | 用途 |
|------|------|------|
| liyu-core | 8765 | 鲤鱼 核心服务 |
| nginx | 80, 443 | 反向代理 |
| redis | 6379 | 缓存服务 |
| prometheus | 9090 | 指标收集 |
| grafana | 3000 | 监控面板 |
| loki | 3100 | 日志聚合 |
| promtail | - | 日志收集 |

### 3. Nginx 反向代理

**文件**:
- `deploy/nginx/nginx.conf` - 主配置
- `deploy/nginx/conf.d/liyu.conf` - 站点配置

**功能**:
- SSL/TLS 终端
- 请求限流
- 安全头部
- Gzip 压缩
- WebSocket 支持
- SSE 支持

### 4. 监控配置

**Prometheus**:
- `deploy/prometheus/prometheus.yml` - 指标收集配置
- `deploy/prometheus/alert-rules.yml` - 告警规则

**Grafana**:
- `deploy/grafana/provisioning/datasources/datasource.yml` - 数据源配置
- `deploy/grafana/provisioning/dashboards/dashboard.yml` - 仪表盘配置
- `deploy/grafana/dashboards/liyu-overview.json` - 预置仪表盘

**Loki**:
- `deploy/loki/loki-config.yml` - 日志聚合配置

**Promtail**:
- `deploy/promtail/promtail-config.yml` - 日志收集配置

### 5. CI/CD 流水线

**文件**: `.github/workflows/ci.yml`

**工作流**:
1. 代码检查（Lint + Type Check）
2. 单元测试 + 集成测试
3. 安全扫描
4. Docker 镜像构建
5. 部署到生产环境
6. 发布 Release

### 6. 环境配置

**文件**: `deploy/config/liyu.env`

**配置项**:
- 鲤鱼 Core 配置
- Redis 配置
- Nginx 配置
- 监控配置
- Sentry 配置
- 安全配置
- 限流配置
- 日志配置
- 备份配置
- 健康检查配置
- 资源限制配置

### 7. 部署脚本

**文件**: `deploy/scripts/deploy.sh`

**命令**:
- `init` - 初始化部署环境
- `start` - 启动所有服务
- `stop` - 停止所有服务
- `restart` - 重启所有服务
- `status` - 查看服务状态
- `logs` - 查看服务日志
- `backup` - 备份数据
- `restore` - 恢复数据
- `update` - 更新服务
- `health` - 健康检查

### 8. Makefile 快捷命令

**文件**: `deploy/Makefile`

**常用命令**:
```bash
make init        # 初始化
make start       # 启动服务
make stop        # 停止服务
make restart     # 重启服务
make status      # 查看状态
make logs        # 查看日志
make backup      # 备份数据
make update      # 更新服务
make health      # 健康检查
make test        # 运行测试
make lint        # 代码检查
make format      # 代码格式化
```

### 9. Python 依赖

**文件**: `requirements.txt`

**依赖分类**:
- 核心依赖（Redis、Prometheus 客户端）
- 监控依赖（Sentry、Prometheus）
- 工具依赖（HTTP 客户端、JSON 处理）
- 安全依赖（JWT、加密）
- 开发依赖（测试、代码质量）

### 10. 部署文档

**文件**: `deploy/README.md`

**内容**:
- 系统要求
- 快速开始
- 详细部署指南
- 配置说明
- 监控与日志
- 故障排除
- 维护指南

---

## 快速开始

### 1. 克隆代码

```bash
git clone https://github.com/your-org/liyu-aios.git
cd liyu-aios
```

### 2. 配置环境变量

```bash
cp deploy/config/liyu.env .env
vim .env  # 修改敏感信息
```

### 3. 初始化部署

```bash
cd deploy
make init
```

### 4. 启动服务

```bash
make start
```

### 5. 验证部署

```bash
make health
```

### 6. 访问服务

- 鲤鱼 Dashboard: http://localhost:8765
- Grafana 监控: http://localhost:3000
- Prometheus 指标: http://localhost:9090

---

## 生产环境部署

### 1. 配置域名

编辑 `deploy/nginx/conf.d/liyu.conf`:

```nginx
server_name your-domain.com www.your-domain.com;
```

### 2. 配置 SSL 证书

```bash
# 使用 Let's Encrypt
sudo certbot certonly --standalone -d your-domain.com

# 复制证书
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem deploy/nginx/ssl/liyu.crt
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem deploy/nginx/ssl/liyu.key
```

### 3. 配置环境变量

编辑 `.env` 文件，修改以下配置:

```bash
# 修改密码
REDIS_PASSWORD=your_secure_redis_password
GRAFANA_PASSWORD=your_secure_grafana_password
JWT_SECRET=your_secure_jwt_secret
API_KEY=your_secure_api_key

# 配置 Sentry
SENTRY_DSN=your_sentry_dsn

# 配置域名
GRAFANA_URL=https://grafana.your-domain.com
```

### 4. 部署

```bash
make start
make health
```

---

## 监控告警

### 预置告警规则

| 告警名称 | 级别 | 触发条件 |
|----------|------|----------|
| PhoenixCoreDown | critical | 服务宕机 > 1 分钟 |
| PhoenixHighLatency | warning | 响应时间 > 2 秒 |
| PhoenixHighErrorRate | warning | 5xx 错误率 > 5% |
| NginxDown | critical | Nginx 宕机 |
| RedisDown | critical | Redis 宕机 |
| HighCpuUsage | warning | CPU > 80% |
| LowDiskSpace | warning | 磁盘 < 10% |

### Grafana 仪表盘

预置仪表盘包含以下面板:

1. **Service Status** - 服务状态
2. **Request Rate** - 请求速率
3. **Response Time** - 响应时间（P50/P95/P99）
4. **Error Rate** - 错误率
5. **Memory Usage** - 内存使用
6. **Active Connections** - 活跃连接数
7. **8-Sense Health** - 鲤鱼 8-Sense 健康状态

---

## 维护指南

### 日常维护

```bash
# 查看服务状态
make status

# 查看日志
make logs

# 健康检查
make health

# 备份数据
make backup
```

### 更新服务

```bash
# 拉取最新代码
git pull

# 更新服务
make update
```

### 清理磁盘空间

```bash
# 清理 Docker 缓存
make clean
```

---

## 安全建议

1. **修改所有默认密码**
2. **配置防火墙限制访问**
3. **使用 SSL/TLS 加密通信**
4. **定期备份数据**
5. **定期更新镜像**
6. **监控安全漏洞**

---

## 文件清单

```
deploy/
├── Dockerfile                    # Docker 容器化配置
├── docker-compose.yml            # Docker Compose 编排
├── Makefile                      # 快捷命令
├── README.md                     # 部署文档
├── DEPLOYMENT-SUMMARY.md         # 部署方案总结
├── .gitignore                    # Git 忽略文件
├── config/
│   └── liyu.env               # 环境变量配置
├── nginx/
│   ├── nginx.conf                # Nginx 主配置
│   ├── conf.d/
│   │   └── liyu.conf          # 站点配置
│   └── ssl/                      # SSL 证书目录
├── prometheus/
│   ├── prometheus.yml            # Prometheus 配置
│   └── alert-rules.yml           # 告警规则
├── grafana/
│   ├── provisioning/
│   │   ├── datasources/
│   │   │   └── datasource.yml    # 数据源配置
│   │   └── dashboards/
│   │       └── dashboard.yml     # 仪表盘配置
│   └── dashboards/
│       └── liyu-overview.json # 预置仪表盘
├── loki/
│   └── loki-config.yml           # Loki 配置
├── promtail/
│   └── promtail-config.yml       # Promtail 配置
└── scripts/
    └── deploy.sh                 # 部署脚本
```

---

## 支持与反馈

- **文档**: [鲤鱼 文档](https://docs.liyu.dev)
- **问题反馈**: [GitHub Issues](https://github.com/your-org/liyu-aios/issues)
- **安全漏洞**: security@liyu.dev
