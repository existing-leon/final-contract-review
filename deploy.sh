#!/usr/bin/env bash
# =====================================================================
# 合同审批审查系统 · 一键部署脚本
# 架构：Docker Compose（后端 + MySQL + Redis）+ 宿主 Nginx（前端静态）
# 用法：sudo bash deploy.sh
#
# 内置处理的高频坑：
#   ① Docker 镜像加速（腾讯云内网，合并而非覆盖 daemon.json）
#   ② DB_HOST 自动写 mysql（避免容器内连 127.0.0.1 报错）
#   ③ 等 MySQL 就绪后再跑迁移（轮询 mysqladmin ping）
#   ④ 删 Nginx 默认站点 + default_server（避免出来欢迎页）
#   ⑤ BuildKit + 国内源构建（已在 Dockerfile，本脚本开 BuildKit）
#   ⑥ 幂等：可重复运行，保留已生成的密码/密钥
# =====================================================================
set -Eeuo pipefail

# ---------------- 颜色 ----------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; NC='\033[0m'
info()  { echo -e "${BLUE}[INFO]${NC} $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}   $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
die()   { echo -e "${RED}[ERROR]${NC} $*"; exit 1; }

# ---------------- 默认配置（可用环境变量覆盖） ----------------
BACKEND_DIR="${BACKEND_DIR:-/opt/contract-review/backend}"
FRONTEND_DIR="${FRONTEND_DIR:-/opt/contract-review/frontend}"
WEB_ROOT="${WEB_ROOT:-/var/www/contract-review}"
NGINX_CONF="${NGINX_CONF:-/etc/nginx/conf.d/contract-review.conf}"
COMPOSE_FILE="$BACKEND_DIR/docker-compose.yml"

# 检测包管理器
detect_pm() {
  if command -v apt-get >/dev/null 2>&1; then echo apt
  elif command -v dnf >/dev/null 2>&1; then echo dnf
  elif command -v yum >/dev/null 2>&1; then echo yum
  else echo none; fi
}
PM="$(detect_pm)"

# ---------------- 交互收集配置 ----------------
collect_config() {
  info "请确认部署配置（直接回车用默认值）："
  read -rp "  后端目录 [$BACKEND_DIR]: " v; BACKEND_DIR="${v:-$BACKEND_DIR}"
  COMPOSE_FILE="$BACKEND_DIR/docker-compose.yml"
  read -rp "  前端目录 [$FRONTEND_DIR]: " v; FRONTEND_DIR="${v:-$FRONTEND_DIR}"

  # SERVER_NAME：用域名或 _（匹配 IP）
  read -rp "  访问域名（无域名直接回车，用 IP 访问） [_]: " v
  SERVER_NAME="${v:-_}"

  # DB_PASSWORD：已有 .env 则沿用，否则随机
  if [[ -f "$BACKEND_DIR/.env" ]] && grep -q '^DB_PASSWORD=' "$BACKEND_DIR/.env"; then
    DB_PASSWORD="$(grep '^DB_PASSWORD=' "$BACKEND_DIR/.env" | cut -d= -f2-)"
    info "  沿用已有 DB_PASSWORD"
  else
    DB_PASSWORD="$(head -c 16 /dev/urandom | base64 | tr -dc 'A-Za-z0-9' | head -c 16)"
  fi
  read -rp "  MySQL 密码（回车用随机/已有）: " v; DB_PASSWORD="${v:-$DB_PASSWORD}"

  # OCR_PROVIDER
  read -rp "  OCR 方式 local(本地PaddleOCR,吃内存) / baidu_api(云端) [local]: " v
  OCR_PROVIDER="${v:-local}"

  # MOCK_APPROVAL
  read -rp "  是否演示模式 MOCK_APPROVAL（True=假数据开箱可跑） [True]: " v
  MOCK_APPROVAL="${v:-True}"

  # SECRET_KEY：已有则沿用，否则随机
  if [[ -f "$BACKEND_DIR/.env" ]] && grep -q '^SECRET_KEY=' "$BACKEND_DIR/.env"; then
    SECRET_KEY="$(grep '^SECRET_KEY=' "$BACKEND_DIR/.env" | cut -d= -f2-)"
  else
    SECRET_KEY="$(openssl rand -hex 32 2>/dev/null || head -c 32 /dev/urandom | base64)"
  fi

  echo
  ok "配置：后端=$BACKEND_DIR  前端=$FRONTEND_DIR  域名=$SERVER_NAME  OCR=$OCR_PROVIDER  MOCK=$MOCK_APPROVAL"
  read -rp "确认开始部署？[Y/n] " c
  [[ "${c:-Y}" =~ ^[Yy]$ ]] || die "已取消"
}

# ---------------- Step 1: Docker ----------------
step_docker() {
  info "Step 1/7 检查 Docker"
  if ! command -v docker >/dev/null 2>&1; then
    warn "未检测到 Docker，开始安装…"
    curl -fsSL https://get.docker.com | sh
    systemctl enable --now docker
  fi
  ok "Docker 就绪：$(docker --version)"
  if ! docker compose version >/dev/null 2>&1; then die "docker compose 不可用"; fi

  # 镜像加速（合并 daemon.json）
  info "配置镜像加速（腾讯云内网）"
  mkdir -p /etc/docker
  python3 - <<PY 2>/dev/null || warn "配置加速失败（可忽略，仅影响拉取速度）"
import json, os
p = "/etc/docker/daemon.json"
d = {}
if os.path.exists(p):
    try: d = json.load(open(p))
    except Exception: d = {}
d.setdefault("registry-mirrors", [])
u = "https://mirror.ccs.tencentyun.com"
if u not in d["registry-mirrors"]:
    d["registry-mirrors"].insert(0, u)
json.dump(d, open(p, "w"), indent=2)
PY
  systemctl daemon-reload && systemctl restart docker
}

# ---------------- Step 2: 后端 .env ----------------
step_env() {
  info "Step 2/7 生成后端 .env"
  [[ -f "$COMPOSE_FILE" ]] || die "未找到 $COMPOSE_FILE，请确认后端目录"
  cat > "$BACKEND_DIR/.env" <<EOF
APP_ENV=prod
APP_HOST=0.0.0.0
APP_PORT=8000

DB_HOST=mysql
DB_PORT=3306
DB_USER=root
DB_PASSWORD=$DB_PASSWORD
DB_NAME=contract_review

REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=

MOCK_APPROVAL=$MOCK_APPROVAL
APPROVAL_BASE_URL=https://approval.example.com
APPROVAL_API_KEY=

SECRET_KEY=$SECRET_KEY
JWT_ALGORITHM=HS256
TOKEN_EXPIRE_MINUTES=1440

ATTACHMENT_DIR=./storage
SAMPLES_DIR=./samples

OCR_PROVIDER=$OCR_PROVIDER
OCR_USE_LAYOUT=True
OCR_TRUST_ENV=False
LLM_API_KEY=
EOF
  ok ".env 已生成（DB_HOST=mysql，SECRET_KEY 已设）"
}

# ---------------- Step 3: 构建并启动 ----------------
step_up() {
  info "Step 3/7 构建并启动容器（首次较慢）"
  cd "$BACKEND_DIR"
  DOCKER_BUILDKIT=1 docker compose build
  docker compose up -d
  ok "容器已启动"
}

# ---------------- Step 4: 等 MySQL 就绪 ----------------
step_wait_mysql() {
  info "Step 4/7 等待 MySQL 就绪"
  cd "$BACKEND_DIR"
  for i in $(seq 1 60); do
    if docker compose exec -T mysql mysqladmin ping -h127.0.0.1 -uroot -p"$DB_PASSWORD" --silent 2>/dev/null; then
      ok "MySQL 就绪"; return 0
    fi
    printf "."; sleep 2
  done
  echo
  die "MySQL 60s 内未就绪，请查：docker compose logs mysql"
}

# ---------------- Step 5: 初始化数据 ----------------
step_init() {
  info "Step 5/7 初始化数据库（迁移 + 规则 + 账号）"
  cd "$BACKEND_DIR"
  docker compose exec -T backend alembic upgrade head
  docker compose exec -T backend python scripts/create_tables.py   # 补 users 表
  docker compose exec -T backend python scripts/init_data.py        # 11 条规则
  docker compose exec -T backend python scripts/init_users.py       # admin/legal 账号
  docker compose exec -T backend python scripts/make_sample_pdf.py 2>/dev/null || warn "示例 PDF 生成跳过"
  ok "数据初始化完成（默认账号 admin/admin123、legal/legal123）"
}

# ---------------- Step 6: 前端构建 ----------------
step_frontend() {
  info "Step 6/7 构建前端"
  [[ -d "$FRONTEND_DIR" ]] || die "前端目录不存在：$FRONTEND_DIR"
  cd "$FRONTEND_DIR"

  # 检测 Node（Vite 需 18+）
  if ! command -v node >/dev/null 2>&1; then
    warn "未检测到 Node，开始安装 Node 18…"
    case "$PM" in
      apt) curl -fsSL https://deb.nodesource.com/setup_18.x | bash -; "$PM" -y install nodejs ;;
      yum|dnf) curl -fsSL https://rpm.nodesource.com/setup_18.x | bash -; "$PM" -y install nodejs ;;
      *) die "请手动安装 Node 18+ 后重跑" ;;
    esac
  fi
  ok "Node: $(node --version)"

  npm install --registry=https://registry.npmmirror.com
  npm run build
  [[ -d dist ]] || die "前端构建失败（无 dist 目录）"

  mkdir -p "$WEB_ROOT"
  rm -rf "${WEB_ROOT:?}/"*
  cp -r dist/* "$WEB_ROOT/"
  ok "前端已构建并部署到 $WEB_ROOT"
}

# ---------------- Step 7: Nginx ----------------
step_nginx() {
  info "Step 7/7 配置 Nginx"
  if ! command -v nginx >/dev/null 2>&1; then
    warn "未检测到 Nginx，开始安装…"
    case "$PM" in
      apt) apt-get update; apt-get -y install nginx ;;
      yum) yum -y install epel-release nginx ;;
      dnf) dnf -y install nginx ;;
      *) die "请手动安装 Nginx 后重跑" ;;
    esac
    systemctl enable --now nginx
  fi

  # 删默认站点（避免抢占 80 出欢迎页）
  rm -f /etc/nginx/sites-enabled/default

  cat > "$NGINX_CONF" <<EOF
server {
    listen 80 default_server;
    server_name __SERVER_NAME__;

    root $WEB_ROOT;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
        client_max_body_size 50m;
    }
}
EOF
  sed -i "s|__SERVER_NAME__|$SERVER_NAME|" "$NGINX_CONF"

  nginx -t || die "Nginx 配置语法错误"
  systemctl reload nginx
  ok "Nginx 已配置并重载"
}

# ---------------- 完成 ----------------
finish() {
  local ip
  ip="$(hostname -I 2>/dev/null | awk '{print $1}')"
  ip="${ip:-<服务器IP>}"
  local url="http://$ip/"
  [[ "$SERVER_NAME" != "_" ]] && url="http://$SERVER_NAME/"
  echo
  echo -e "${GREEN}========================================${NC}"
  echo -e "${GREEN}  ✅ 部署完成！${NC}"
  echo -e "${GREEN}========================================${NC}"
  echo -e "  访问地址：${BLUE}${url}${NC}"
  echo -e "  登录账号：admin / admin123  或  legal / legal123"
  echo
  echo -e "  ${YELLOW}⚠️ 上线前必做：${NC}"
  echo -e "    1. 腾讯云控制台 → 安全组 → 入方向放行 TCP 80"
  echo -e "    2. 修改默认密码 admin123/legal123"
  echo -e "    3. MOCK_APPROVAL=True 是假数据，接真实审批系统时改 False"
  echo
  echo -e "  常用命令（在 $BACKEND_DIR）："
  echo -e "    docker compose ps          # 查看容器状态"
  echo -e "    docker compose logs -f backend   # 看后端日志"
  echo -e "    docker compose restart backend   # 重启后端"
}

main() {
  echo -e "${GREEN}========================================${NC}"
  echo -e "${GREEN}  合同审批审查系统 · 一键部署${NC}"
  echo -e "${GREEN}========================================${NC}"
  [[ $EUID -eq 0 ]] || die "请用 root 或 sudo 运行：sudo bash deploy.sh"
  command -v python3 >/dev/null 2>&1 || die "需要 python3（用于配置镜像加速）"

  collect_config
  step_docker
  step_env
  step_up
  step_wait_mysql
  step_init
  step_frontend
  step_nginx
  finish
}

main "$@"
