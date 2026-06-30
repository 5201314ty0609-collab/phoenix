# 鲤鱼 AIOS 部署文档

## 目录

- [概述](#概述)
- [系统要求](#系统要求)
- [快速开始](#快速开始)
- [详细部署](#详细部署)
- [配置说明](#配置说明)
- [监控与日志](#监控与日志)
- [故障排除](#故障排除)
- [维护指南](#维护指南)

---

## 概述

鲤鱼 AIOS 是一个基于 Python 的智能操作系统，提供完整的容器化部署方案。

### 架构组件

```
┌─────────────────────────────────────────────────────────────────┐
│                        Nginx (反向代理)                         │
│                    端口: 80 (HTTP), 443 (HTTPS)                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                    鲤鱼 Core (核心服务)                       │
│                         端口: 8765                              │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│    Redis     │      │  Prometheus  │      │     Loki     │
│    缓存      │      │   指标收集    │      │   日志聚合   │
└──────────────┘      └──────────────┘      └──────────────┘
                              │
                              ▼
                      ┌──────────────┐
                      │   Grafana    │
                      │   监控面板    │
                      └──────────────┘
```

### 技术栈

| 组件 | 技术 | 版本 | 用途 |
|------|------|------|------|
| 核心服务 | Python | 3.11+ | 鲤鱼 API + Dashboard |
| 反向代理 | Nginx | 1.25 | 负载均衡 + SSL 终端 |
| 缓存 | Redis | 7.x | 会话存储 + 数据缓存 |
| 指标收集 | Prometheus | 2.48 | 时序数据存储 |
| 监控面板 | Grafana | 10.2 | 可视化监控 |
| 日志聚合 | Loki | 2.9 | 日志存储和查询 |
| 日志收集 | Promtail | 2.9 | 日志采集器 |
| CI/CD | GitHub Actions | - | 自动化构建部署 |

---

## 系统要求

### 硬件要求

| 环境 | CPU | 内存 | 磁盘 |
|------|-----|------|------|
| 开发环境 | 2 核 | 4 GB | 20 GB |
| 生产环境 | 4 核 | 8 GB | 50 GB |
| 高可用 | 8 核 | 16 GB | 100 GB |

### 软件要求

- **操作系统**: Linux (Ubuntu 20.04+, Debian 11+, CentOS 8+)
- **Docker**: 24.0+
- **Docker Compose**: 2.20+
- **Git**: 2.30+
- **curl**: 用于健康检查

### 网络要求

| 端口 | 协议 | 用途 |
|------|------|------|
| 80 | TCP | HTTP 访问 |
| 443 | TCP | HTTPS 访问 |
| 8765 | TCP | 鲤鱼 API（内部） |
| 3000 | TCP | Grafana（可选外部访问） |
| 9090 | TCP | Prometheus（可选外部访问） |

---

## 快速开始

### 1. 克隆代码

```bash
git clone https://github.com/your-org/liyu-aios.git
cd liyu-aios
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp deploy/config/liyu.env .env

# 编辑配置文件
vim .env
```

**必须修改的配置项**:

```bash
# Redis 密码
REDIS_PASSWORD=your_secure_redis_password

# Grafana 管理员密码
GRAFANA_PASSWORD=your_secure_grafana_password

# JWT 密钥
JWT_SECRET=your_secure_jwt_secret

# API 密钥
API_KEY=your_secure_api_key
```

### 3. 生成 SSL 证书（开发环境）

```bash
# 创建自签名证书（仅用于开发）
mkdir -p deploy/nginx/ssl

openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout deploy/nginx/ssl/liyu.key \
  -out deploy/nginx/ssl/liyu.crt \
  -subj "/C=CN/ST=Beijing/L=Beijing/O=鲤鱼/CN=liyu.local"
```

### 4. 启动服务

```bash
# 启动所有服务
docker compose -f deploy/docker-compose.yml up -d

# 查看服务状态
docker compose -f deploy/docker-compose.yml ps

# 查看日志
docker compose -f deploy/docker-compose.yml logs -f
```

### 5. 验证部署

```bash
# 检查 鲤鱼 Core
curl -f http://localhost:8765/api/status

# 检查 Nginx
curl -f http://localhost/health

# 检查 Grafana
curl -f http://localhost:3000/api/health
```

---

## 详细部署

### 生产环境部署

#### 1. 服务器准备

```bash
# 更新系统
sudo apt update && sudo apt upgrade -y

# 安装 Docker
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# 安装 Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# 验证安装
docker --version
docker-compose --version
```

#### 2. 配置防火墙

```bash
# 允许 SSH
sudo ufw allow 22/tcp

# 允许 HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 启用防火墙
sudo ufw enable
```

#### 3. 配置 SSL 证书（生产环境）

```bash
# 安装 Certbot
sudo apt install certbot

# 获取 Let's Encrypt 证书
sudo certbot certonly --standalone -d your-domain.com

# 复制证书
sudo cp /etc/letsencrypt/live/your-domain.com/fullchain.pem deploy/nginx/ssl/liyu.crt
sudo cp /etc/letsencrypt/live/your-domain.com/privkey.pem deploy/nginx/ssl/liyu.key
```

#### 4. 配置域名

编辑 `deploy/nginx/conf.d/liyu.conf`:

```nginx
server_name your-domain.com www.your-domain.com;
```

#### 5. 部署

```bash
# 拉取最新代码
git pull origin main

# 启动服务
docker compose -f deploy/docker-compose.yml up -d

# 验证部署
curl -f https://your-domain.com/api/status
```

### 高可用部署

#### 1. 负载均衡器配置

使用外部负载均衡器（如 AWS ALB、Nginx Plus）分发流量到多个 鲤鱼 Core 实例。

#### 2. 数据库集群

配置 Redis Cluster 或 Redis Sentinel 实现高可用。

#### 3. 共享存储

使用 NFS 或分布式存储（如 Ceph）共享数据卷。

---

## 配置说明

### 环境变量

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| `鲤鱼_PORT` | 8765 | 鲤鱼 Core 监听端口 |
| `鲤鱼_HOST` | 0.0.0.0 | 鲤鱼 Core 监听地址 |
| `鲤鱼_ENV` | production | 运行环境 |
| `鲤鱼_LOG_LEVEL` | INFO | 日志级别 |
| `REDIS_PASSWORD` | liyu_redis_pass | Redis 密码 |
| `GRAFANA_USER` | admin | Grafana 管理员用户名 |
| `GRAFANA_PASSWORD` | liyu_grafana | Grafana 管理员密码 |
| `SENTRY_DSN` | - | Sentry 错误监控 DSN |
| `JWT_SECRET` | - | JWT 认证密钥 |
| `API_KEY` | - | API 访问密钥 |

### Nginx 配置

主要配置文件位置：

- `deploy/nginx/nginx.conf` - 主配置
- `deploy/nginx/conf.d/liyu.conf` - 站点配置

关键配置项：

```nginx
# 请求限流
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;

# 连接限流
limit_conn_zone $binary_remote_addr zone=conn_limit:10m;

# SSL 配置
ssl_protocols TLSv1.2 TLSv1.3;
ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:...;
```

### Prometheus 配置

配置文件位置：`deploy/prometheus/prometheus.yml`

主要抓取目标：

- `liyu-core:8765` - 鲤鱼 Core 指标
- `nginx-exporter:9113` - Nginx 指标
- `redis-exporter:9121` - Redis 指标

---

## 监控与日志

### Grafana 监控面板

访问地址：`http://your-server:3000`

默认登录信息：
- 用户名：`admin`
- 密码：`liyu_grafana`（请在 `.env` 中修改）

预置仪表盘：

1. **鲤鱼 Overview** - 核心服务概览
   - 服务状态
   - 请求速率
   - 响应时间
   - 错误率
   - 内存使用
   - 8-Sense 健康状态

### Prometheus 指标

访问地址：`http://your-server:9090`

常用查询：

```promql
# 请求速率
rate(http_requests_total{job="liyu-core"}[5m])

# 响应时间 P95
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{job="liyu-core"}[5m]))

# 错误率
rate(http_requests_total{status=~"5..", job="liyu-core"}[5m])
```

### Loki 日志查询

访问地址：通过 Grafana 的 Explore 功能

常用 LogQL 查询：

```logql
# 查看所有错误日志
{job="liyu-app"} |= "ERROR"

# 查看特定模块日志
{job="liyu-app", module="server"} | json

# 查看 Nginx 5xx 错误
{job="nginx-access"} | json | status >= 500
```

### 告警规则

预置告警规则位于 `deploy/prometheus/alert-rules.yml`：

| 告警名称 | 级别 | 触发条件 |
|----------|------|----------|
| PhoenixCoreDown | critical | 服务宕机 > 1 分钟 |
| PhoenixHighLatency | warning | 响应时间 > 2 秒 |
| PhoenixHighErrorRate | warning | 5xx 错误率 > 5% |
| NginxDown | critical | Nginx 宕机 |
| RedisDown | critical | Redis 宕机 |
| HighCpuUsage | warning | CPU > 80% |
| LowDiskSpace | warning | 磁盘 < 10% |

---

## 故障排除

### 常见问题

#### 1. 服务无法启动

```bash
# 查看服务日志
docker compose -f deploy/docker-compose.yml logs liyu-core

# 检查端口占用
sudo lsof -i :8765

# 检查配置文件语法
docker compose -f deploy/docker-compose.yml config
```

#### 2. Nginx 502 Bad Gateway

```bash
# 检查 鲤鱼 Core 是否运行
docker compose -f deploy/docker-compose.yml ps liyu-core

# 检查网络连接
docker compose -f deploy/docker-compose.yml exec nginx ping liyu-core

# 检查 Nginx 配置
docker compose -f deploy/docker-compose.yml exec nginx nginx -t
```

#### 3. Redis 连接失败

```bash
# 检查 Redis 状态
docker compose -f deploy/docker-compose.yml ps redis

# 测试 Redis 连接
docker compose -f deploy/docker-compose.yml exec redis redis-cli -a $REDIS_PASSWORD ping

# 检查 Redis 日志
docker compose -f deploy/docker-compose.yml logs redis
```

#### 4. Grafana 无法显示数据

```bash
# 检查 Prometheus 数据源
curl http://localhost:9090/api/v1/targets

# 检查 Loki 数据源
curl http://localhost:3100/ready

# 重启 Grafana
docker compose -f deploy/docker-compose.yml restart grafana
```

### 日志位置

| 服务 | 日志路径 |
|------|----------|
| 鲤鱼 Core | `/opt/liyu/logs/liyu.log` |
| Nginx | `/var/log/nginx/access.log` |
| Redis | 容器日志 |
| Prometheus | 容器日志 |
| Grafana | `/var/log/grafana/grafana.log` |

---

## 维护指南

### 日常维护

#### 1. 备份数据

```bash
# 备份 Redis 数据
docker compose -f deploy/docker-compose.yml exec redis redis-cli -a $REDIS_PASSWORD BGSAVE

# 备份 Prometheus 数据
docker compose -f deploy/docker-compose.yml exec prometheus tar -czf /tmp/prometheus-backup.tar.gz /prometheus

# 备份 Grafana 数据
docker compose -f deploy/docker-compose.yml exec grafana tar -czf /tmp/grafana-backup.tar.gz /var/lib/grafana
```

#### 2. 清理磁盘空间

```bash
# 清理 Docker 缓存
docker system prune -a

# 清理旧日志
docker compose -f deploy/docker-compose.yml exec loki find /loki -name "*.gz" -mtime +30 -delete
```

#### 3. 更新服务

```bash
# 拉取最新镜像
docker compose -f deploy/docker-compose.yml pull

# 滚动更新
docker compose -f deploy/docker-compose.yml up -d --remove-orphans

# 清理旧镜像
docker image prune -f
```

### 性能优化

#### 1. Nginx 优化

```nginx
# 增加工作进程数
worker_processes auto;

# 增加连接数
worker_connections 4096;

# 启用 HTTP/2
listen 443 ssl http2;
```

#### 2. Redis 优化

```bash
# 增加最大内存
redis-cli CONFIG SET maxmemory 512mb

# 优化淘汰策略
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

#### 3. 鲤鱼 Core 优化

```bash
# 增加工作线程
鲤鱼_WORKERS=4

# 启用缓存
鲤鱼_CACHE_ENABLED=true
鲤鱼_CACHE_TTL=300
```

### 扩容指南

#### 水平扩容

```bash
# 增加 鲤鱼 Core 实例
docker compose -f deploy/docker-compose.yml up -d --scale liyu-core=3

# 更新 Nginx 上游配置
# 在 nginx/conf.d/liyu.conf 中添加多个后端服务器
```

#### 垂直扩容

```bash
# 修改资源限制
# 在 docker-compose.yml 中调整 deploy.resources.limits
```

---

## 安全建议

### 1. 网络安全

- 使用 SSL/TLS 加密所有通信
- 配置防火墙限制访问
- 使用 VPN 访问管理界面

### 2. 认证安全

- 修改所有默认密码
- 使用强密码策略
- 启用多因素认证

### 3. 数据安全

- 定期备份数据
- 加密敏感数据
- 限制数据访问权限

### 4. 容器安全

- 使用非 root 用户运行
- 定期更新镜像
- 扫描镜像漏洞

---

## 支持与反馈

- **文档**: [鲤鱼 文档](https://docs.liyu.dev)
- **问题反馈**: [GitHub Issues](https://github.com/your-org/liyu-aios/issues)
- **安全漏洞**: security@liyu.dev

---

## 许可证

鲤鱼 AIOS 使用 MIT 许可证。详见 [LICENSE](../LICENSE) 文件。
