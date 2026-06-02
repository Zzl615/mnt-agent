# API参考文档

## 1. MCP工具调用

### 1.1 宏观数据工具

#### get_china_macro_indicator

获取中国宏观经济指标数据。

**请求示例：**
```json
{
  "tool": "get_china_macro_indicator",
  "arguments": {
    "indicator": "cpi",
    "start_date": "2020-01-01",
    "end_date": "2024-12-31"
  }
}
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 | 示例值 |
|------|------|------|------|--------|
| indicator | string | 是 | 指标类型 | "cpi", "ppi", "gdp", "m2", "lpr", "pmi" |
| start_date | string | 否 | 开始日期 | "2020-01-01" |
| end_date | string | 否 | 结束日期 | "2024-12-31" |

**响应示例：**
```json
[
  {
    "日期": "2024-01-01",
    "最新": 0.7,
    "同比": -0.3,
    "环比": 0.1
  },
  {
    "日期": "2023-12-01",
    "最新": 0.5,
    "同比": -0.5,
    "环比": -0.2
  }
]
```

**错误响应：**
```json
{
  "error": "Unknown indicator: xyz",
  "tool": "get_china_macro_indicator",
  "arguments": {"indicator": "xyz"}
}
```

---

#### get_us_macro_indicator

获取美国宏观经济指标数据。

**请求示例：**
```json
{
  "tool": "get_us_macro_indicator",
  "arguments": {
    "indicator": "treasury_yield",
    "period": "2y"
  }
}
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 | 示例值 |
|------|------|------|------|--------|
| indicator | string | 是 | 指标类型 | "treasury_yield", "fed_rate", "cpi", "nonfarm", "gdp", "unemployment" |
| period | string | 否 | 时间范围 | "1m", "3m", "6m", "1y", "2y", "5y", "10y" |

**响应示例：**
```json
[
  {
    "Date": "2024-01-01",
    "Open": 3.88,
    "High": 3.92,
    "Low": 3.85,
    "Close": 3.90,
    "Volume": 0
  }
]
```

---

#### get_global_commodity

获取大宗商品价格数据。

**请求示例：**
```json
{
  "tool": "get_global_commodity",
  "arguments": {
    "commodity": "gold",
    "days": 365
  }
}
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 | 示例值 |
|------|------|------|------|--------|
| commodity | string | 是 | 商品名称 | "crude", "gold", "silver", "copper", "natural_gas" |
| days | integer | 否 | 返回天数 | 365 |

**响应示例：**
```json
[
  {
    "Date": "2024-01-01",
    "Open": 2063.50,
    "High": 2078.20,
    "Low": 2058.30,
    "Close": 2071.80,
    "Volume": 185432
  }
]
```

### 1.2 市场数据工具

#### get_stock_history

获取股票历史行情数据。

**请求示例：**
```json
{
  "tool": "get_stock_history",
  "arguments": {
    "tickers": ["AAPL", "MSFT", "GOOGL"],
    "start_date": "2023-01-01",
    "end_date": "2024-12-31",
    "interval": "1d"
  }
}
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 | 示例值 |
|------|------|------|------|--------|
| tickers | array | 是 | 股票代码列表 | ["AAPL", "MSFT"] |
| start_date | string | 否 | 开始日期 | "2023-01-01" |
| end_date | string | 否 | 结束日期 | "2024-12-31" |
| interval | string | 否 | 数据间隔 | "1d", "1wk", "1mo" |

**响应示例：**
```json
{
  "AAPL": [
    {
      "Date": "2024-01-01",
      "Open": 185.00,
      "High": 186.50,
      "Low": 184.00,
      "Close": 185.50,
      "Volume": 50000000
    }
  ],
  "MSFT": [...]
}
```

---

#### get_etf_history

获取ETF历史行情数据。

**请求示例：**
```json
{
  "tool": "get_etf_history",
  "arguments": {
    "tickers": ["SPY", "QQQ", "TLT", "GLD"],
    "start_date": "2023-01-01",
    "end_date": "2024-12-31"
  }
}
```

**响应示例：**
```json
{
  "SPY": [
    {
      "Date": "2024-01-01",
      "Open": 475.00,
      "High": 477.50,
      "Low": 474.00,
      "Close": 476.80,
      "Volume": 65000000
    }
  ]
}
```

---

#### get_market_index

获取市场指数数据。

**请求示例：**
```json
{
  "tool": "get_market_index",
  "arguments": {
    "indices": ["^GSPC", "^IXIC", "^DJI"],
    "period": "1y"
  }
}
```

**参数说明：**

| 参数 | 类型 | 必填 | 说明 | 示例值 |
|------|------|------|------|--------|
| indices | array | 是 | 指数代码列表 | ["^GSPC", "^IXIC"] |
| period | string | 否 | 时间范围 | "1m", "3m", "6m", "1y", "2y", "5y" |

## 2. Agent工作流API

### 2.1 宏观研究

**调用示例：**
```python
from agent_core.workflows.macro_research import MacroResearchWorkflow

workflow = MacroResearchWorkflow(mcp_client)
result = await workflow.run_research(
    focus_areas=["china_gdp", "china_cpi", "us_fed_rate", "us_treasury", "commodities"]
)
```

**返回格式：**
```json
{
  "timestamp": "2024-01-01T00:00:00Z",
  "macro_environment": {
    "regime": "risk_on",
    "description": "宏观环境偏宽松，风险资产偏好上升",
    "bullish_signals": 5,
    "bearish_signals": 2,
    "confidence": 0.75
  },
  "insights": [
    {
      "indicator": "China CPI",
      "current_value": 0.7,
      "trend": "down",
      "signal": "bullish",
      "confidence": 0.8,
      "reasoning": "CPI下降，通缩风险，政策宽松预期"
    }
  ],
  "recommendations": [
    {
      "asset": "equity",
      "action": "overweight",
      "weight": 0.6,
      "rationale": "风险偏好上升，增配股票"
    }
  ]
}
```

### 2.2 策略生成

**调用示例：**
```python
from agent_core.workflows.strategy_builder import StrategyBuilderWorkflow

workflow = StrategyBuilderWorkflow()
strategy = workflow.build_strategy(
    macro_environment=macro_result["macro_environment"],
    recommendations=macro_result["recommendations"]
)
```

**返回格式：**
```json
{
  "name": "MacroMomentumStrategy",
  "type": "macro_momentum",
  "assets": ["SPY", "QQQ", "TLT", "GLD"],
  "weights": {
    "SPY": 0.35,
    "QQQ": 0.25,
    "TLT": 0.20,
    "GLD": 0.20
  },
  "rebalance": {
    "frequency": "monthly",
    "threshold": 0.05,
    "method": "calendar"
  },
  "constraints": {
    "max_single_weight": 0.40,
    "min_single_weight": 0.05,
    "max_turnover": 0.30
  }
}
```

### 2.3 回测执行

**调用示例：**
```python
from agent_core.workflows.backtest_runner import BacktestRunnerWorkflow

workflow = BacktestRunnerWorkflow()
result = await workflow.run_backtest(
    strategy=strategy,
    start_date="2018-01-01",
    end_date="2024-12-31",
    initial_capital=1000000
)
```

**返回格式：**
```json
{
  "period": {
    "start": "2018-01-01",
    "end": "2024-12-31",
    "days": 2557
  },
  "performance": {
    "total_return": 0.85,
    "annualized_return": 0.092,
    "max_drawdown": -0.18,
    "sharpe_ratio": 0.85,
    "sortino_ratio": 1.12,
    "calmar_ratio": 0.51,
    "volatility": 0.12
  },
  "benchmark_comparison": {
    "benchmark_return": 0.72,
    "alpha": 0.13,
    "beta": 0.85,
    "information_ratio": 0.45
  },
  "plots": {
    "equity_curve": "output/equity_curve.png",
    "drawdown": "output/drawdown.png",
    "monthly_returns": "output/monthly_returns.png"
  }
}
```

## 3. 错误码

| 错误码 | 说明 | 处理方式 |
|--------|------|----------|
| INVALID_PARAMETER | 参数无效 | 检查参数格式和取值范围 |
| DATA_NOT_FOUND | 数据未找到 | 检查代码/指标名称是否正确 |
| RATE_LIMIT_EXCEEDED | 请求频率超限 | 等待后重试 |
| DATA_SOURCE_ERROR | 数据源错误 | 检查网络连接，重试 |
| INTERNAL_ERROR | 内部错误 | 联系支持 |

## 4. 限流说明

| 工具类型 | 限制 | 时间窗口 |
|----------|------|----------|
| 宏观数据 | 60次 | 1分钟 |
| 市场数据 | 100次 | 1分钟 |
| 回测执行 | 10次 | 1分钟 |

## 5. 最佳实践

### 5.1 批量请求

```python
# 推荐：批量获取多个指标
indicators = ["cpi", "ppi", "gdp"]
tasks = [mcp_call("get_china_macro_indicator", {"indicator": ind}) for ind in indicators]
results = await asyncio.gather(*tasks)
```

### 5.2 缓存使用

```python
# 使用缓存减少重复请求
cached_data = cache.get("china_cpi_2024")
if cached_data:
    return cached_data
else:
    data = await mcp_call("get_china_macro_indicator", {"indicator": "cpi"})
    cache.set("china_cpi_2024", data)
    return data
```

### 5.3 错误处理

```python
try:
    result = await mcp_call("get_stock_history", {"tickers": ["AAPL"]})
except RateLimitError:
    await asyncio.sleep(60)
    result = await mcp_call("get_stock_history", {"tickers": ["AAPL"]})
except DataSourceError as e:
    logger.error(f"Data source error: {e}")
    # 使用备用数据源
    result = await fallback_call("get_stock_history", {"tickers": ["AAPL"]})
```
