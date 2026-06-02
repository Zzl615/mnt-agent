# 部署指南

## 1. 环境要求

### 1.1 系统要求

| 组件 | 最低要求 | 推荐配置 |
|------|----------|----------|
| CPU | 2核 | 4核+ |
| 内存 | 4GB | 8GB+ |
| 磁盘 | 10GB | 50GB+ |
| Python | 3.10+ | 3.11+ |
| 操作系统 | Linux/macOS/Windows | Linux (Ubuntu 22.04+) |

### 1.2 依赖软件

- Python 3.10+
- pip
- git
- Docker (可选)

## 2. 本地部署

### 2.1 克隆仓库

```bash
git clone https://github.com/your-org/macro-invest-agent.git
cd macro-invest-agent
```

### 2.2 创建虚拟环境

```bash
# 使用venv
python -m venv venv
source venv/bin/activate  # Linux/macOS
# 或
venv\Scripts\activate  # Windows

# 或使用conda
conda create -n macro-invest python=3.11
conda activate macro-invest
```

### 2.3 安装依赖

```bash
# 安装核心依赖
pip install -r requirements.txt

# 或安装开发版本
pip install -e ".[dev]"
```

**requirements.txt:**
```
bt>=0.2.9
pandas>=2.0.0
numpy>=1.24.0
yfinance>=0.2.31
akshare>=1.12.0
matplotlib>=3.7.0
seaborn>=0.12.0
pyyaml>=6.0
mcp>=0.9.0
httpx>=0.24.0
```

### 2.4 配置环境变量

创建`.env`文件：

```bash
# MCP服务器配置
MCP_MACRO_URL=http://localhost:8001
MCP_MARKET_URL=http://localhost:8002

# 数据源配置（可选）
TUSHARE_TOKEN=your_tushare_token
NEWS_API_KEY=your_news_api_key

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/agent.log
```

### 2.5 启动MCP服务器

**终端1 - 宏观数据服务器：**
```bash
python mcp-servers/macro-data-server/server.py
```

**终端2 - 市场数据服务器：**
```bash
python mcp-servers/market-data-server/server.py
```

### 2.6 运行Agent

```bash
# 基本运行
python scripts/run_agent.py

# 带查询参数
python scripts/run_agent.py --query "分析当前宏观环境并生成投资策略"

# 指定配置文件
python scripts/run_agent.py --config config/custom_settings.yaml
```

## 3. Docker部署

### 3.1 构建镜像

```bash
docker build -t macro-invest-agent:latest .
```

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制代码
COPY . .

# 创建必要目录
RUN mkdir -p data output logs cache

# 暴露端口
EXPOSE 8001 8002

# 启动命令
CMD ["python", "scripts/run_agent.py"]
```

### 3.2 运行容器

```bash
# 运行MCP服务器
docker run -d \
  --name macro-data-server \
  -p 8001:8001 \
  macro-invest-agent:latest \
  python mcp-servers/macro-data-server/server.py

docker run -d \
  --name market-data-server \
  -p 8002:8002 \
  macro-invest-agent:latest \
  python mcp-servers/market-data-server/server.py

# 运行Agent
docker run -it \
  --name macro-invest-agent \
  -v $(pwd)/output:/app/output \
  -v $(pwd)/data:/app/data \
  macro-invest-agent:latest
```

### 3.3 Docker Compose

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  macro-data-server:
    build: .
    command: python mcp-servers/macro-data-server/server.py
    ports:
      - "8001:8001"
    volumes:
      - ./data:/app/data
      - ./cache:/app/cache
    environment:
      - LOG_LEVEL=INFO

  market-data-server:
    build: .
    command: python mcp-servers/market-data-server/server.py
    ports:
      - "8002:8002"
    volumes:
      - ./data:/app/data
      - ./cache:/app/cache
    environment:
      - LOG_LEVEL=INFO

  agent:
    build: .
    command: python scripts/run_agent.py
    volumes:
      - ./output:/app/output
      - ./data:/app/data
      - ./config:/app/config
    environment:
      - MCP_MACRO_URL=http://macro-data-server:8001
      - MCP_MARKET_URL=http://market-data-server:8002
    depends_on:
      - macro-data-server
      - market-data-server
```

启动：
```bash
docker-compose up -d
```

## 4. 生产环境部署

### 4.1 服务器配置

**推荐配置：**
- CPU: 8核+
- 内存: 16GB+
- 磁盘: 100GB SSD
- 操作系统: Ubuntu 22.04 LTS

### 4.2 使用systemd管理

**/etc/systemd/system/macro-data.service:**
```ini
[Unit]
Description=Macro Data MCP Server
After=network.target

[Service]
Type=simple
User=macro-invest
WorkingDirectory=/opt/macro-invest-agent
ExecStart=/opt/macro-invest-agent/venv/bin/python mcp-servers/macro-data-server/server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**/etc/systemd/system/market-data.service:**
```ini
[Unit]
Description=Market Data MCP Server
After=network.target

[Service]
Type=simple
User=macro-invest
WorkingDirectory=/opt/macro-invest-agent
ExecStart=/opt/macro-invest-agent/venv/bin/python mcp-servers/market-data-server/server.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

启动服务：
```bash
sudo systemctl daemon-reload
sudo systemctl enable macro-data
sudo systemctl enable market-data
sudo systemctl start macro-data
sudo systemctl start market-data
```

### 4.3 Nginx反向代理

**/etc/nginx/sites-available/macro-invest:**
```nginx
server {
    listen 80;
    server_name api.example.com;

    location /macro-data/ {
        proxy_pass http://localhost:8001/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /market-data/ {
        proxy_pass http://localhost:8002/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

启用配置：
```bash
sudo ln -s /etc/nginx/sites-available/macro-invest /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4.4 HTTPS配置

使用Let's Encrypt获取SSL证书：
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d api.example.com
```

## 5. 监控与日志

### 5.1 日志配置

**config/logging.yaml:**
```yaml
version: 1
formatters:
  standard:
    format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
  json:
    format: "%(message)s"
    class: pythonjsonlogger.jsonlogger.JsonFormatter

handlers:
  console:
    class: logging.StreamHandler
    level: INFO
    formatter: standard
    stream: ext://sys.stdout
  
  file:
    class: logging.FileHandler
    level: DEBUG
    formatter: json
    filename: logs/agent.log

root:
  level: INFO
  handlers: [console, file]
```

### 5.2 健康检查

```bash
# 检查MCP服务器
curl http://localhost:8001/health
curl http://localhost:8002/health

# 检查Agent
curl http://localhost:8000/status
```

### 5.3 监控指标

使用Prometheus + Grafana监控：

**metrics.py:**
```python
from prometheus_client import Counter, Histogram, start_http_server

# 定义指标
REQUEST_COUNT = Counter('mcp_requests_total', 'Total MCP requests', ['tool', 'status'])
REQUEST_DURATION = Histogram('mcp_request_duration_seconds', 'Request duration')

# 启动指标服务器
start_http_server(9090)
```

## 6. 备份与恢复

### 6.1 数据备份

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/macro-invest"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录
mkdir -p $BACKUP_DIR

# 备份数据
tar -czf $BACKUP_DIR/data_$DATE.tar.gz data/
tar -czf $BACKUP_DIR/output_$DATE.tar.gz output/
tar -czf $BACKUP_DIR/config_$DATE.tar.gz config/

# 备份数据库（如有）
pg_dump macro_invest > $BACKUP_DIR/db_$DATE.sql

# 删除7天前的备份
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
```

### 6.2 定时备份

```bash
# 添加到crontab
0 2 * * * /opt/macro-invest-agent/scripts/backup.sh
```

## 7. 故障排查

### 7.1 常见问题

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| MCP连接失败 | 服务器未启动 | 检查服务状态，重启 |
| 数据获取超时 | 网络问题 | 检查网络，增加超时时间 |
| 内存不足 | 数据量过大 | 增加内存，分批处理 |
| 回测报错 | 数据缺失 | 检查数据完整性 |

### 7.2 日志查看

```bash
# 查看服务日志
sudo journalctl -u macro-data -f
sudo journalctl -u market-data -f

# 查看应用日志
tail -f logs/agent.log
```

### 7.3 性能调优

```bash
# 检查CPU使用
top

# 检查内存使用
free -h

# 检查磁盘使用
df -h

# 检查网络连接
netstat -tulpn
```

## 8. 安全建议

### 8.1 访问控制

- 使用防火墙限制端口访问
- 配置API密钥认证
- 定期更新依赖

### 8.2 数据安全

- 加密敏感配置
- 定期备份数据
- 限制数据访问权限

### 8.3 网络安全

- 使用HTTPS
- 配置速率限制
- 监控异常访问
