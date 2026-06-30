#!/bin/bash
# =============================================================================
# 鲤鱼 AIOS 部署脚本 — 自动化部署工具
# =============================================================================
# 用法:
#   ./deploy.sh [command] [options]
#
# 命令:
#   init      - 初始化部署环境
#   start     - 启动所有服务
#   stop      - 停止所有服务
#   restart   - 重启所有服务
#   status    - 查看服务状态
#   logs      - 查看服务日志
#   backup    - 备份数据
#   restore   - 恢复数据
#   update    - 更新服务
#   health    - 健康检查
# =============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 配置文件路径
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEPLOY_DIR="$(dirname "$SCRIPT_DIR")"
PROJECT_DIR="$(dirname "$DEPLOY_DIR")"
COMPOSE_FILE="$DEPLOY_DIR/docker-compose.yml"
ENV_FILE="$PROJECT_DIR/.env"

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 检查依赖
check_dependencies() {
    log_step "检查依赖..."

    # 检查 Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker 未安装"
        exit 1
    fi

    # 检查 Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose 未安装"
        exit 1
    fi

    # 检查 curl
    if ! command -v curl &> /dev/null; then
        log_error "curl 未安装"
        exit 1
    fi

    log_info "依赖检查通过"
}

# 检查环境变量
check_env() {
    log_step "检查环境变量..."

    if [ ! -f "$ENV_FILE" ]; then
        log_warn "环境变量文件不存在，从模板创建..."
        cp "$DEPLOY_DIR/config/liyu.env" "$ENV_FILE"
        log_warn "请编辑 $ENV_FILE 配置环境变量"
        exit 1
    fi

    # 加载环境变量
    source "$ENV_FILE"

    # 检查必需变量
    REQUIRED_VARS=(
        "REDIS_PASSWORD"
        "GRAFANA_PASSWORD"
        "JWT_SECRET"
        "API_KEY"
    )

    for var in "${REQUIRED_VARS[@]}"; do
        if [ -z "${!var}" ] || [ "${!var}" = "your_${var,,}_here" ]; then
            log_error "请配置 $var"
            exit 1
        fi
    done

    log_info "环境变量检查通过"
}

# 生成 SSL 证书
generate_ssl() {
    log_step "生成 SSL 证书..."

    SSL_DIR="$DEPLOY_DIR/nginx/ssl"

    if [ ! -f "$SSL_DIR/liyu.crt" ] || [ ! -f "$SSL_DIR/liyu.key" ]; then
        mkdir -p "$SSL_DIR"

        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout "$SSL_DIR/liyu.key" \
            -out "$SSL_DIR/liyu.crt" \
            -subj "/C=CN/ST=Beijing/L=Beijing/O=鲤鱼/CN=liyu.local" \
            2>/dev/null

        log_info "SSL 证书生成完成"
    else
        log_info "SSL 证书已存在"
    fi
}

# 初始化部署环境
init() {
    log_step "初始化部署环境..."

    # 检查依赖
    check_dependencies

    # 检查环境变量
    check_env

    # 生成 SSL 证书
    generate_ssl

    # 创建必要目录
    mkdir -p "$PROJECT_DIR/logs"
    mkdir -p "$PROJECT_DIR/data"

    # 设置权限
    chmod +x "$SCRIPT_DIR"/*.sh

    log_info "初始化完成"
}

# 启动服务
start() {
    log_step "启动服务..."

    # 检查环境
    check_dependencies
    check_env

    # 启动服务
    docker compose -f "$COMPOSE_FILE" up -d

    # 等待服务启动
    log_info "等待服务启动..."
    sleep 10

    # 健康检查
    health

    log_info "服务启动完成"
    echo ""
    echo "访问地址:"
    echo "  - 鲤鱼: http://localhost:8765"
    echo "  - Grafana: http://localhost:3000"
    echo "  - Prometheus: http://localhost:9090"
}

# 停止服务
stop() {
    log_step "停止服务..."

    docker compose -f "$COMPOSE_FILE" down

    log_info "服务停止完成"
}

# 重启服务
restart() {
    log_step "重启服务..."

    stop
    start

    log_info "服务重启完成"
}

# 查看服务状态
status() {
    log_step "查看服务状态..."

    docker compose -f "$COMPOSE_FILE" ps
}

# 查看服务日志
logs() {
    local service=${1:-""}

    if [ -n "$service" ]; then
        docker compose -f "$COMPOSE_FILE" logs -f "$service"
    else
        docker compose -f "$COMPOSE_FILE" logs -f
    fi
}

# 备份数据
backup() {
    log_step "备份数据..."

    BACKUP_DIR="$PROJECT_DIR/backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"

    # 备份 Redis
    log_info "备份 Redis..."
    docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli -a "$REDIS_PASSWORD" BGSAVE
    sleep 5
    docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli -a "$REDIS_PASSWORD" SAVE
    docker cp liyu-redis:/data/dump.rdb "$BACKUP_DIR/redis.rdb"

    # 备份 Prometheus
    log_info "备份 Prometheus..."
    docker cp liyu-prometheus:/prometheus "$BACKUP_DIR/prometheus"

    # 备份 Grafana
    log_info "备份 Grafana..."
    docker cp liyu-grafana:/var/lib/grafana "$BACKUP_DIR/grafana"

    # 备份配置文件
    log_info "备份配置文件..."
    cp "$ENV_FILE" "$BACKUP_DIR/env.backup"
    cp "$COMPOSE_FILE" "$BACKUP_DIR/docker-compose.yml.backup"

    # 压缩备份
    tar -czf "$BACKUP_DIR.tar.gz" -C "$BACKUP_DIR" .
    rm -rf "$BACKUP_DIR"

    log_info "备份完成: $BACKUP_DIR.tar.gz"
}

# 恢复数据
restore() {
    local backup_file=${1:-""}

    if [ -z "$backup_file" ]; then
        log_error "请指定备份文件"
        echo "用法: ./deploy.sh restore <backup_file.tar.gz>"
        exit 1
    fi

    if [ ! -f "$backup_file" ]; then
        log_error "备份文件不存在: $backup_file"
        exit 1
    fi

    log_step "恢复数据..."

    # 停止服务
    stop

    # 解压备份
    RESTORE_DIR="/tmp/liyu-restore"
    mkdir -p "$RESTORE_DIR"
    tar -xzf "$backup_file" -C "$RESTORE_DIR"

    # 恢复 Redis
    if [ -f "$RESTORE_DIR/redis.rdb" ]; then
        log_info "恢复 Redis..."
        docker cp "$RESTORE_DIR/redis.rdb" liyu-redis:/data/dump.rdb
    fi

    # 恢复 Prometheus
    if [ -d "$RESTORE_DIR/prometheus" ]; then
        log_info "恢复 Prometheus..."
        docker cp "$RESTORE_DIR/prometheus/." liyu-prometheus:/prometheus
    fi

    # 恢复 Grafana
    if [ -d "$RESTORE_DIR/grafana" ]; then
        log_info "恢复 Grafana..."
        docker cp "$RESTORE_DIR/grafana/." liyu-grafana:/var/lib/grafana
    fi

    # 清理
    rm -rf "$RESTORE_DIR"

    # 启动服务
    start

    log_info "数据恢复完成"
}

# 更新服务
update() {
    log_step "更新服务..."

    # 拉取最新代码
    log_info "拉取最新代码..."
    cd "$PROJECT_DIR"
    git pull

    # 拉取最新镜像
    log_info "拉取最新镜像..."
    docker compose -f "$COMPOSE_FILE" pull

    # 滚动更新
    log_info "滚动更新..."
    docker compose -f "$COMPOSE_FILE" up -d --remove-orphans

    # 清理旧镜像
    log_info "清理旧镜像..."
    docker image prune -f

    log_info "更新完成"
}

# 健康检查
health() {
    log_step "健康检查..."

    # 检查 鲤鱼 Core
    if curl -sf http://localhost:8765/api/status > /dev/null 2>&1; then
        log_info "鲤鱼 Core: OK"
    else
        log_error "鲤鱼 Core: FAILED"
    fi

    # 检查 Nginx
    if curl -sf http://localhost/health > /dev/null 2>&1; then
        log_info "Nginx: OK"
    else
        log_error "Nginx: FAILED"
    fi

    # 检查 Redis
    if docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli -a "$REDIS_PASSWORD" ping > /dev/null 2>&1; then
        log_info "Redis: OK"
    else
        log_error "Redis: FAILED"
    fi

    # 检查 Prometheus
    if curl -sf http://localhost:9090/-/healthy > /dev/null 2>&1; then
        log_info "Prometheus: OK"
    else
        log_error "Prometheus: FAILED"
    fi

    # 检查 Grafana
    if curl -sf http://localhost:3000/api/health > /dev/null 2>&1; then
        log_info "Grafana: OK"
    else
        log_error "Grafana: FAILED"
    fi
}

# 显示帮助
help() {
    echo "鲤鱼 AIOS 部署脚本"
    echo ""
    echo "用法:"
    echo "  ./deploy.sh [command] [options]"
    echo ""
    echo "命令:"
    echo "  init      - 初始化部署环境"
    echo "  start     - 启动所有服务"
    echo "  stop      - 停止所有服务"
    echo "  restart   - 重启所有服务"
    echo "  status    - 查看服务状态"
    echo "  logs      - 查看服务日志"
    echo "  backup    - 备份数据"
    echo "  restore   - 恢复数据"
    echo "  update    - 更新服务"
    echo "  health    - 健康检查"
    echo "  help      - 显示帮助"
    echo ""
    echo "示例:"
    echo "  ./deploy.sh init"
    echo "  ./deploy.sh start"
    echo "  ./deploy.sh logs liyu-core"
    echo "  ./deploy.sh backup"
    echo "  ./deploy.sh restore backups/20260623_120000.tar.gz"
}

# 主函数
main() {
    local command=${1:-"help"}

    case "$command" in
        init)
            init
            ;;
        start)
            start
            ;;
        stop)
            stop
            ;;
        restart)
            restart
            ;;
        status)
            status
            ;;
        logs)
            logs "${@:2}"
            ;;
        backup)
            backup
            ;;
        restore)
            restore "${@:2}"
            ;;
        update)
            update
            ;;
        health)
            health
            ;;
        help|--help|-h)
            help
            ;;
        *)
            log_error "未知命令: $command"
            help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"
