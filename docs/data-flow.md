# 数据流设计

## 1. 数据流概览

系统数据流分为四个阶段：数据采集、数据清洗、数据存储、数据消费。

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  数据采集    │───▶│  数据清洗    │───▶│  数据存储    │───▶│  数据消费    │
│  (MCP Tools) │    │  (Pipeline) │    │  (Local/DB) │    │  (Agent)    │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## 2. 数据采集

### 2.1 数据源分类

| 数据类型 | 数据源 | 更新频率 | 覆盖范围 |
|----------|--------|----------|----------|
| 中国宏观指标 | AkShare | 月/季/年 | GDP、CPI、PPI、M2、LPR、PMI |
| 美国宏观指标 | AkShare/Yahoo Finance | 月 | 非农、CPI、联邦基金利率、国债收益率 |
| 股票行情 | Yahoo Finance/Tushare | 日 | A股、美股、港股 |
| 大宗商品 | Yahoo Finance | 日 | 原油、黄金、铜、农产品 |
| 市场指数 | Yahoo Finance | 日 | 上证指数、标普500、纳斯达克 |
| 财经新闻 | 新闻API | 实时 | 政策公告、行业动态 |

### 2.2 采集流程

```python
# 伪代码示例
async def collect_data(indicator: str, params: dict) -> pd.DataFrame:
    # 1. 检查缓存
    cached = check_cache(indicator, params)
    if cached and not is_expired(cached):
        return cached
    
    # 2. 调用MCP工具
    raw_data = await mcp_client.call_tool(
        tool_name=get_tool_name(indicator),
        arguments=params
    )
    
    # 3. 更新缓存
    update_cache(indicator, params, raw_data)
    
    return raw_data
```

### 2.3 缓存策略

| 数据类型 | 缓存时间 | 存储位置 |
|----------|----------|----------|
| 宏观指标 | 24小时 | 本地JSON/SQLite |
| 股票行情 | 1小时 | 本地Parquet |
| 实时新闻 | 10分钟 | 内存缓存 |

## 3. 数据清洗

### 3.1 清洗流程

```
原始数据
  │
  ▼
┌─────────────────┐
│  缺失值处理      │  前向填充/删除/插值
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  异常值检测      │  3σ原则/箱线图
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  格式标准化      │  日期格式、数值精度
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  特征工程        │  收益率、移动平均、技术指标
└────────┬────────┘
         │
         ▼
清洗后数据
```

### 3.2 清洗规则

#### 缺失值处理
```python
def handle_missing_values(df: pd.DataFrame, method: str = "ffill") -> pd.DataFrame:
    if method == "ffill":
        return df.ffill()
    elif method == "interpolate":
        return df.interpolate(method="linear")
    elif method == "drop":
        return df.dropna()
    else:
        raise ValueError(f"Unknown method: {method}")
```

#### 异常值检测
```python
def detect_outliers(df: pd.DataFrame, column: str, threshold: float = 3.0) -> pd.Series:
    mean = df[column].mean()
    std = df[column].std()
    return (df[column] - mean).abs() > threshold * std
```

#### 格式标准化
```python
def standardize_format(df: pd.DataFrame) -> pd.DataFrame:
    # 日期格式统一
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"])
        df = df.set_index("Date")
    
    # 数值精度统一
    numeric_cols = df.select_dtypes(include=["float64"]).columns
    df[numeric_cols] = df[numeric_cols].round(4)
    
    return df
```

### 3.3 特征工程

| 特征类型 | 计算方法 | 用途 |
|----------|----------|------|
| 收益率 | `pct_change()` | 策略信号 |
| 移动平均 | `rolling(window).mean()` | 趋势判断 |
| 波动率 | `rolling(window).std()` | 风险管理 |
| 技术指标 | MACD、RSI、布林带 | 交易信号 |
| 宏观因子 | 同比/环比变化率 | 宏观分析 |

## 4. 数据存储

### 4.1 存储方案

| 数据类型 | 存储格式 | 存储位置 | 说明 |
|----------|----------|----------|------|
| 宏观指标 | JSON | `data/macro/` | 便于查询和更新 |
| 股票行情 | Parquet | `data/market/` | 高效压缩和查询 |
| 回测结果 | JSON/CSV | `output/` | 便于分析和可视化 |
| 缓存数据 | SQLite | `cache.db` | 快速读写 |

### 4.2 目录结构

```
data/
├── macro/
│   ├── china/
│   │   ├── gdp.json
│   │   ├── cpi.json
│   │   └── ppi.json
│   └── us/
│       ├── cpi.json
│       └── treasury_yield.json
├── market/
│   ├── stocks/
│   │   ├── AAPL.parquet
│   │   └── MSFT.parquet
│   └── commodities/
│       ├── crude.parquet
│       └── gold.parquet
└── cache.db
```

### 4.3 数据更新机制

```python
class DataUpdater:
    def __init__(self):
        self.cache = SQLiteCache("cache.db")
    
    async def update(self, indicator: str, force: bool = False):
        # 检查是否需要更新
        if not force and not self.cache.is_expired(indicator):
            return
        
        # 获取最新数据
        raw_data = await self.fetch_from_source(indicator)
        
        # 清洗数据
        cleaned_data = self.clean(raw_data)
        
        # 存储数据
        self.save(indicator, cleaned_data)
        
        # 更新缓存时间戳
        self.cache.update_timestamp(indicator)
```

## 5. 数据消费

### 5.1 消费场景

| 场景 | 数据需求 | 消费方 |
|------|----------|--------|
| 宏观研究 | 宏观指标、大宗商品 | MacroResearchWorkflow |
| 策略生成 | 股票行情、市场指数 | StrategyBuilderWorkflow |
| 回测验证 | 历史行情、基准指数 | BacktestRunnerWorkflow |
| 报告生成 | 所有数据 | MacroInvestAgent |

### 5.2 数据接口

```python
class DataProvider:
    def get_macro_data(self, indicator: str, start: str, end: str) -> pd.DataFrame:
        """获取宏观数据"""
        pass
    
    def get_market_data(self, tickers: list, start: str, end: str) -> pd.DataFrame:
        """获取市场数据"""
        pass
    
    def get_commodity_data(self, commodities: list, days: int) -> pd.DataFrame:
        """获取大宗商品数据"""
        pass
```

## 6. 异常处理

### 6.1 数据异常

| 异常类型 | 处理方式 | 说明 |
|----------|----------|------|
| 数据源不可用 | 重试3次，切换备用源 | 网络问题、API限制 |
| 数据格式错误 | 记录日志，使用默认值 | 数据源变更 |
| 数据缺失 | 前向填充或跳过 | 非交易日、数据延迟 |

### 6.2 错误恢复

```python
async def fetch_with_retry(fetch_func, max_retries: int = 3, delay: float = 1.0):
    for attempt in range(max_retries):
        try:
            return await fetch_func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(delay * (2 ** attempt))
```

## 7. 性能优化

### 7.1 批量获取

```python
async def batch_fetch(indicators: list) -> dict:
    """批量获取多个指标"""
    tasks = [fetch_indicator(ind) for ind in indicators]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return {ind: res for ind, res in zip(indicators, results)}
```

### 7.2 并行处理

```python
# 使用多进程处理数据清洗
from concurrent.futures import ProcessPoolExecutor

def clean_data_parallel(dataframes: list) -> list:
    with ProcessPoolExecutor() as executor:
        return list(executor.map(clean_single_dataframe, dataframes))
```

## 8. 监控与日志

### 8.1 监控指标

| 指标 | 说明 | 告警阈值 |
|------|------|----------|
| 数据获取延迟 | 从请求到响应的时间 | > 5秒 |
| 数据质量 | 缺失值比例 | > 10% |
| 缓存命中率 | 缓存命中次数/总请求次数 | < 50% |
| 存储使用量 | 磁盘使用量 | > 80% |

### 8.2 日志格式

```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "level": "INFO",
  "component": "data_pipeline",
  "action": "fetch_macro_data",
  "indicator": "china_cpi",
  "status": "success",
  "duration_ms": 1200,
  "records": 60
}
```
