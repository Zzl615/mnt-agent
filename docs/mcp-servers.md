# MCP服务器设计

## 1. 概述

MCP（Model Context Protocol）服务器为本系统提供标准化的数据接口，使Agent能够通过自然语言调用工具获取金融数据。系统包含两个核心MCP服务器：

- **Macro Data Server**: 提供宏观经济数据
- **Market Data Server**: 提供金融市场数据

## 2. Macro Data Server

### 2.1 服务器配置

```python
# mcp-servers/macro-data-server/server.py
from mcp.server import Server
from mcp.types import Tool, TextContent
import akshare as ak
import pandas as pd

server = Server("macro-data-server")
```

### 2.2 工具定义

#### 2.2.1 get_china_macro_indicator

获取中国宏观经济指标数据。

**工具定义：**
```python
Tool(
    name="get_china_macro_indicator",
    description="获取中国宏观经济指标（GDP、CPI、PPI、M2、LPR、PMI等）",
    inputSchema={
        "type": "object",
        "properties": {
            "indicator": {
                "type": "string",
                "enum": ["gdp", "cpi", "ppi", "m2", "lpr", "pmi", "unemployment", "retail_sales"]
            },
            "start_date": {
                "type": "string",
                "format": "date",
                "description": "开始日期，格式YYYY-MM-DD"
            },
            "end_date": {
                "type": "string",
                "format": "date",
                "description": "结束日期，格式YYYY-MM-DD"
            }
        },
        "required": ["indicator"]
    }
)
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| indicator | string | 是 | 指标类型 | "cpi" |
| start_date | string | 否 | 开始日期 | "2020-01-01" |
| end_date | string | 否 | 结束日期 | "2024-12-31" |

**返回值格式：**
```json
[
  {
    "日期": "2024-01-01",
    "最新": 0.7,
    "同比": -0.3,
    "环比": 0.1
  }
]
```

**实现代码：**
```python
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_china_macro_indicator":
        indicator = arguments["indicator"]
        start_date = arguments.get("start_date")
        end_date = arguments.get("end_date")
        
        df = _fetch_china_macro(indicator, start_date, end_date)
        return [TextContent(type="text", text=df.to_json(orient="records"))]

def _fetch_china_macro(indicator: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
    """获取中国宏观数据"""
    fetchers = {
        "cpi": ak.macro_china_cpi_yearly,
        "ppi": ak.macro_china_ppi_yearly,
        "gdp": ak.macro_china_gdp_yearly,
        "m2": ak.macro_china_money_supply,
        "lpr": ak.macro_china_lpr,
        "pmi": ak.macro_china_pmi_yearly,
        "unemployment": ak.macro_china_unemployment_rate,
        "retail_sales": ak.macro_china_retail_sales_yearly
    }
    
    if indicator not in fetchers:
        raise ValueError(f"Unknown indicator: {indicator}")
    
    df = fetchers[indicator]()
    
    if start_date:
        df = df[df["日期"] >= start_date]
    if end_date:
        df = df[df["日期"] <= end_date]
    
    return df.tail(60)
```

#### 2.2.2 get_us_macro_indicator

获取美国宏观经济指标数据。

**工具定义：**
```python
Tool(
    name="get_us_macro_indicator",
    description="获取美国宏观经济指标（非农、CPI、联邦基金利率、国债收益率等）",
    inputSchema={
        "type": "object",
        "properties": {
            "indicator": {
                "type": "string",
                "enum": ["nonfarm", "cpi", "fed_rate", "treasury_yield", "gdp", "unemployment"]
            },
            "period": {
                "type": "string",
                "enum": ["1m", "3m", "6m", "1y", "2y", "5y", "10y"],
                "default": "1y",
                "description": "时间范围"
            }
        },
        "required": ["indicator"]
    }
)
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| indicator | string | 是 | 指标类型 | "treasury_yield" |
| period | string | 否 | 时间范围 | "2y" |

**返回值格式：**
```json
[
  {
    "Date": "2024-01-01",
    "Value": 4.02,
    "Change": 0.05
  }
]
```

**实现代码：**
```python
def _fetch_us_macro(indicator: str, period: str = "1y") -> pd.DataFrame:
    """获取美国宏观数据"""
    import yfinance as yf
    
    fetchers = {
        "treasury_yield": lambda: _fetch_treasury_yield(period),
        "fed_rate": ak.macro_usa_interest_rate,
        "cpi": ak.macro_usa_cpi_monthly,
        "nonfarm": ak.macro_usa_non_farm_monthly,
        "gdp": ak.macro_usa_gdp,
        "unemployment": ak.macro_usa_unemployment_rate
    }
    
    if indicator not in fetchers:
        raise ValueError(f"Unknown indicator: {indicator}")
    
    return fetchers[indicator]()

def _fetch_treasury_yield(period: str) -> pd.DataFrame:
    """获取国债收益率"""
    ticker_map = {
        "1m": "^IRX",
        "3m": "^IRX",
        "6m": "^IRX",
        "1y": "^TYX",
        "2y": "^TYX",
        "5y": "^FVX",
        "10y": "^TNX",
        "30y": "^TYX"
    }
    
    ticker = ticker_map.get(period, "^TNX")
    df = yf.download(ticker, period=period)
    return df.reset_index()
```

#### 2.2.3 get_global_commodity

获取大宗商品价格数据。

**工具定义：**
```python
Tool(
    name="get_global_commodity",
    description="获取大宗商品价格（原油、黄金、铜、铁矿石、农产品等）",
    inputSchema={
        "type": "object",
        "properties": {
            "commodity": {
                "type": "string",
                "description": "商品名称或代码"
            },
            "days": {
                "type": "integer",
                "default": 365,
                "description": "返回天数"
            }
        },
        "required": ["commodity"]
    }
)
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| commodity | string | 是 | 商品名称 | "gold" |
| days | integer | 否 | 返回天数 | 365 |

**支持的商品：**

| 商品 | 代码 | Yahoo Ticker |
|------|------|--------------|
| 原油 | crude | CL=F |
| 黄金 | gold | GC=F |
| 白银 | silver | SI=F |
| 铜 | copper | HG=F |
| 天然气 | natural_gas | NG=F |
| 小麦 | wheat | ZW=F |
| 玉米 | corn | ZC=F |
| 大豆 | soybean | ZS=F |

**实现代码：**
```python
def _fetch_commodity(commodity: str, days: int = 365) -> pd.DataFrame:
    """获取大宗商品价格"""
    import yfinance as yf
    
    commodity_map = {
        "crude": "CL=F",
        "gold": "GC=F",
        "silver": "SI=F",
        "copper": "HG=F",
        "natural_gas": "NG=F",
        "wheat": "ZW=F",
        "corn": "ZC=F",
        "soybean": "ZS=F"
    }
    
    ticker = commodity_map.get(commodity.lower(), commodity)
    period = f"{max(1, days//30)}mo" if days < 365 else "5y"
    
    df = yf.download(ticker, period=period)
    return df.reset_index().tail(days)
```

### 2.3 错误处理

```python
class MacroDataError(Exception):
    """宏观数据错误"""
    pass

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    try:
        # 工具调用逻辑
        result = await execute_tool(name, arguments)
        return [TextContent(type="text", text=result)]
    except Exception as e:
        error_response = json.dumps({
            "error": str(e),
            "tool": name,
            "arguments": arguments
        })
        return [TextContent(type="text", text=error_response)]
```

## 3. Market Data Server

### 3.1 服务器配置

```python
# mcp-servers/market-data-server/server.py
from mcp.server import Server
from mcp.types import Tool, TextContent
import yfinance as yf
import pandas as pd

server = Server("market-data-server")
```

### 3.2 工具定义

#### 3.2.1 get_stock_history

获取股票历史行情数据。

**工具定义：**
```python
Tool(
    name="get_stock_history",
    description="获取股票历史行情数据（开盘价、收盘价、最高价、最低价、成交量）",
    inputSchema={
        "type": "object",
        "properties": {
            "tickers": {
                "type": "array",
                "items": {"type": "string"},
                "description": "股票代码列表"
            },
            "start_date": {
                "type": "string",
                "format": "date",
                "description": "开始日期"
            },
            "end_date": {
                "type": "string",
                "format": "date",
                "description": "结束日期"
            },
            "interval": {
                "type": "string",
                "enum": ["1d", "1wk", "1mo"],
                "default": "1d",
                "description": "数据间隔"
            }
        },
        "required": ["tickers"]
    }
)
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 | 示例 |
|------|------|------|------|------|
| tickers | array | 是 | 股票代码列表 | ["AAPL", "MSFT"] |
| start_date | string | 否 | 开始日期 | "2020-01-01" |
| end_date | string | 否 | 结束日期 | "2024-12-31" |
| interval | string | 否 | 数据间隔 | "1d" |

**返回值格式：**
```json
{
  "AAPL": [
    {"Date": "2024-01-01", "Open": 185.0, "High": 186.5, "Low": 184.0, "Close": 185.5, "Volume": 50000000}
  ],
  "MSFT": [...]
}
```

**实现代码：**
```python
@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    if name == "get_stock_history":
        tickers = arguments["tickers"]
        start_date = arguments.get("start_date", "2020-01-01")
        end_date = arguments.get("end_date", datetime.now().strftime("%Y-%m-%d"))
        interval = arguments.get("interval", "1d")
        
        data = {}
        for ticker in tickers:
            df = yf.download(ticker, start=start_date, end=end_date, interval=interval)
            data[ticker] = df.reset_index().to_dict(orient="records")
        
        return [TextContent(type="text", text=json.dumps(data))]
```

#### 3.2.2 get_etf_history

获取ETF历史行情数据。

**工具定义：**
```python
Tool(
    name="get_etf_history",
    description="获取ETF历史行情数据",
    inputSchema={
        "type": "object",
        "properties": {
            "tickers": {
                "type": "array",
                "items": {"type": "string"},
                "description": "ETF代码列表"
            },
            "start_date": {"type": "string", "format": "date"},
            "end_date": {"type": "string", "format": "date"}
        },
        "required": ["tickers"]
    }
)
```

**常用ETF代码：**

| ETF | 说明 |
|-----|------|
| SPY | 标普500 ETF |
| QQQ | 纳斯达克100 ETF |
| IWM | 罗素2000 ETF |
| TLT | 20年期国债 ETF |
| IEF | 7-10年期国债 ETF |
| GLD | 黄金 ETF |
| USO | 原油 ETF |
| XLF | 金融板块 ETF |
| XLK | 科技板块 ETF |

#### 3.2.3 get_market_index

获取市场指数数据。

**工具定义：**
```python
Tool(
    name="get_market_index",
    description="获取市场指数数据",
    inputSchema={
        "type": "object",
        "properties": {
            "indices": {
                "type": "array",
                "items": {"type": "string"},
                "description": "指数代码列表"
            },
            "period": {
                "type": "string",
                "enum": ["1m", "3m", "6m", "1y", "2y", "5y"],
                "default": "1y"
            }
        },
        "required": ["indices"]
    }
)
```

**常用指数代码：**

| 指数 | 代码 | 说明 |
|------|------|------|
| 上证指数 | 000001.SS | 上海证券交易所综合股价指数 |
| 深证成指 | 399001.SZ | 深圳证券交易所成份股价指数 |
| 标普500 | ^GSPC | S&P 500 Index |
| 纳斯达克 | ^IXIC | NASDAQ Composite |
| 道琼斯 | ^DJI | Dow Jones Industrial Average |
| 恒生指数 | ^HSI | Hang Seng Index |

### 3.3 数据缓存

```python
class DataCache:
    """数据缓存"""
    def __init__(self, cache_dir: str = "cache/", ttl: int = 3600):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[pd.DataFrame]:
        """获取缓存数据"""
        cache_file = self.cache_dir / f"{key}.parquet"
        if cache_file.exists():
            mtime = cache_file.stat().st_mtime
            if time.time() - mtime < self.ttl:
                return pd.read_parquet(cache_file)
        return None
    
    def set(self, key: str, data: pd.DataFrame):
        """设置缓存数据"""
        cache_file = self.cache_dir / f"{key}.parquet"
        data.to_parquet(cache_file)
```

## 4. MCP客户端

### 4.1 客户端实现

```python
# agent-core/mcp_client.py
from mcp import ClientSession
import httpx

class MCPClient:
    def __init__(self, server_urls: dict):
        self.server_urls = server_urls
        self.sessions = {}
    
    async def connect(self):
        """连接到MCP服务器"""
        for name, url in self.server_urls.items():
            client = httpx.AsyncClient(base_url=url)
            session = ClientSession(client)
            await session.initialize()
            self.sessions[name] = session
    
    async def call_tool(self, server: str, tool_name: str, arguments: dict) -> pd.DataFrame:
        """调用MCP工具"""
        if server not in self.sessions:
            raise ValueError(f"Unknown server: {server}")
        
        session = self.sessions[server]
        result = await session.call_tool(tool_name, arguments)
        
        # 解析结果
        data = json.loads(result.content[0].text)
        return pd.DataFrame(data)
    
    async def close(self):
        """关闭连接"""
        for session in self.sessions.values():
            await session.close()
```

### 4.2 配置示例

```json
// config/mcp_config.json
{
  "mcpServers": {
    "macro-data": {
      "command": "python",
      "args": ["mcp-servers/macro-data-server/server.py"],
      "cwd": ".",
      "env": {}
    },
    "market-data": {
      "command": "python",
      "args": ["mcp-servers/market-data-server/server.py"],
      "cwd": ".",
      "env": {}
    }
  }
}
```

## 5. 安全与限流

### 5.1 API限流

```python
class RateLimiter:
    """API限流"""
    def __init__(self, max_requests: int = 60, window: int = 60):
        self.max_requests = max_requests
        self.window = window
        self.requests = []
    
    async def acquire(self):
        """获取请求许可"""
        now = time.time()
        self.requests = [t for t in self.requests if now - t < self.window]
        
        if len(self.requests) >= self.max_requests:
            wait_time = self.window - (now - self.requests[0])
            await asyncio.sleep(wait_time)
        
        self.requests.append(now)
```

### 5.2 认证（可选）

```python
class AuthMiddleware:
    """认证中间件"""
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def verify(self, request: dict) -> bool:
        """验证请求"""
        return request.get("api_key") == self.api_key
```

## 6. 监控与日志

### 6.1 请求日志

```python
import logging

logger = logging.getLogger("mcp_server")

async def log_request(tool_name: str, arguments: dict, duration: float, status: str):
    """记录请求日志"""
    logger.info({
        "tool": tool_name,
        "arguments": arguments,
        "duration_ms": duration * 1000,
        "status": status
    })
```

### 6.2 健康检查

```python
@server.list_resources()
async def list_resources() -> list:
    """健康检查端点"""
    return [{
        "uri": "health://check",
        "name": "Health Check",
        "description": "Server health status"
    }]
```
