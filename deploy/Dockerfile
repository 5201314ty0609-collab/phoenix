# =============================================================================
# PHOENIX AIOS Dockerfile — 生产级容器化配置
# =============================================================================
# 基础镜像: Python 3.11 slim (轻量级，安全性高)
# 构建策略: 多阶段构建，最小化镜像体积
# 安全特性: 非 root 用户运行，只读文件系统
# =============================================================================

# ── 阶段 1: 构建阶段 ─────────────────────────────────────────────────────
FROM python:3.11-slim as builder

# 设置构建时环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 安装构建依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 创建虚拟环境
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 复制依赖文件（如果存在）
COPY requirements.txt /tmp/requirements.txt 2>/dev/null || true

# 安装 Python 依赖
RUN if [ -f /tmp/requirements.txt ]; then \
    pip install --no-cache-dir -r /tmp/requirements.txt; \
    fi

# ── 阶段 2: 运行阶段 ─────────────────────────────────────────────────────
FROM python:3.11-slim as runtime

# 设置运行时环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/opt/venv/bin:$PATH" \
    PHOENIX_HOME="/opt/phoenix" \
    PHOENIX_PORT=8765 \
    PHOENIX_HOST="0.0.0.0" \
    PHOENIX_ENV="production"

# 安装运行时依赖
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    tini \
    && rm -rf /var/lib/apt/lists/*

# 从构建阶段复制虚拟环境
COPY --from=builder /opt/venv /opt/venv

# 创建非 root 用户
RUN groupadd -r phoenix && \
    useradd -r -g phoenix -d /opt/phoenix -s /sbin/nologin phoenix

# 创建应用目录结构
RUN mkdir -p /opt/phoenix/{aios,configs,data,logs,senses,frameworks,heartbeats} && \
    chown -R phoenix:phoenix /opt/phoenix

# 设置工作目录
WORKDIR /opt/phoenix

# 复制应用代码
COPY --chown=phoenix:phoenix . .

# 创建数据卷挂载点
VOLUME ["/opt/phoenix/data", "/opt/phoenix/logs", "/opt/phoenix/configs"]

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PHOENIX_PORT}/api/status || exit 1

# 切换到非 root 用户
USER phoenix

# 暴露端口
EXPOSE ${PHOENIX_PORT}

# 使用 tini 作为 init 进程
ENTRYPOINT ["tini", "--"]

# 启动命令
CMD ["python", "server.py", "--port", "${PHOENIX_PORT}", "--host", "${PHOENIX_HOST}"]
