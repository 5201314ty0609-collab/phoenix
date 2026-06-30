# =============================================================================
# PHOENIX AIOS Makefile — 快捷命令集
# =============================================================================
# 用法:
#   make [command]
# =============================================================================

.PHONY: help init start stop restart status logs backup restore update health test lint

# 默认目标
help: ## 显示帮助信息
	@echo "PHOENIX AIOS 部署命令"
	@echo ""
	@echo "用法: make [command]"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# ── 部署命令 ──────────────────────────────────────────────────────────────

init: ## 初始化部署环境
	@./scripts/deploy.sh init

start: ## 启动所有服务
	@./scripts/deploy.sh start

stop: ## 停止所有服务
	@./scripts/deploy.sh stop

restart: ## 重启所有服务
	@./scripts/deploy.sh restart

status: ## 查看服务状态
	@./scripts/deploy.sh status

logs: ## 查看服务日志
	@./scripts/deploy.sh logs

logs-phoenix: ## 查看 PHOENIX Core 日志
	@./scripts/deploy.sh logs phoenix-core

logs-nginx: ## 查看 Nginx 日志
	@./scripts/deploy.sh logs nginx

logs-redis: ## 查看 Redis 日志
	@./scripts/deploy.sh logs redis

# ── 数据管理 ──────────────────────────────────────────────────────────────

backup: ## 备份数据
	@./scripts/deploy.sh backup

restore: ## 恢复数据 (需要指定备份文件: make restore BACKUP=file.tar.gz)
	@./scripts/deploy.sh restore $(BACKUP)

# ── 维护命令 ──────────────────────────────────────────────────────────────

update: ## 更新服务
	@./scripts/deploy.sh update

health: ## 健康检查
	@./scripts/deploy.sh health

clean: ## 清理 Docker 缓存
	@docker system prune -a -f
	@docker volume prune -f

# ── 开发命令 ──────────────────────────────────────────────────────────────

test: ## 运行测试
	@pytest tests/ -v --cov=. --cov-report=term-missing

lint: ## 代码检查
	@ruff check .
	@black --check .
	@isort --check-only .

format: ## 代码格式化
	@black .
	@isort .

type-check: ## 类型检查
	@mypy . --ignore-missing-imports

security: ## 安全扫描
	@safety check
	@bandit -r . -ll -ii --skip B101,B311

# ── Docker 命令 ──────────────────────────────────────────────────────────

build: ## 构建 Docker 镜像
	@docker compose -f docker-compose.yml build

pull: ## 拉取最新镜像
	@docker compose -f docker-compose.yml pull

push: ## 推送镜像到仓库
	@docker compose -f docker-compose.yml push

# ── 监控命令 ──────────────────────────────────────────────────────────────

prometheus: ## 打开 Prometheus
	@open http://localhost:9090

grafana: ## 打开 Grafana
	@open http://localhost:3000

dashboard: ## 打开 PHOENIX Dashboard
	@open http://localhost:8765

# ── SSL 证书 ──────────────────────────────────────────────────────────────

ssl-dev: ## 生成开发环境 SSL 证书
	@mkdir -p nginx/ssl
	@openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
		-keyout nginx/ssl/phoenix.key \
		-out nginx/ssl/phoenix.crt \
		-subj "/C=CN/ST=Beijing/L=Beijing/O=PHOENIX/CN=phoenix.local"
	@echo "SSL 证书生成完成"

ssl-check: ## 检查 SSL 证书
	@openssl x509 -in nginx/ssl/phoenix.crt -text -noout

# ── 快捷方式 ──────────────────────────────────────────────────────────────

up: start ## 同 start

down: stop ## 同 stop

ps: status ## 同 status

# ── 文档 ──────────────────────────────────────────────────────────────────

docs: ## 生成文档
	@sphinx-build -b html docs/ docs/_build/html
	@open docs/_build/html/index.html

# ── 环境检查 ──────────────────────────────────────────────────────────────

check: ## 检查环境依赖
	@echo "检查 Docker..."
	@docker --version
	@echo "检查 Docker Compose..."
	@docker compose version
	@echo "检查 Python..."
	@python3 --version
	@echo "检查 Git..."
	@git --version
	@echo "环境检查完成"
